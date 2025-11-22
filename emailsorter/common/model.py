from abc import abstractmethod, ABC


import logging
from collections import defaultdict
from enum import Enum
from typing import Iterable, Callable, Dict, Tuple, Any, Set

from googleapiwrapper.gmail_domain import GmailMessage

UNLABELED_KEY = "Unlabeled (just Inbox)"
LABELED_KEY = "Labeled"
THREADS_KEY = "threads"
COUNT_KEY = "count"

LOG = logging.getLogger(__name__)

class ProcessorResultType(Enum):
    SIMPLIFIED = "simplified"
    SIMPLIFIED_WITH_LABELS = "simplified_with_labels"
    DETAILED = "detailed"


class EmailContentProcessor(ABC):
    @abstractmethod
    def process(self, email_content: 'EmailContent'):
        pass

class EmailMessageProcessor(ABC):
    @abstractmethod
    def process(self, email_message: 'GmailMessage'):
        pass

    @abstractmethod
    def convert_to_table_rows(self) -> Iterable[Iterable[str]]:
        pass


class PrintingEmailContentProcessor(EmailContentProcessor):
    def __init__(self):
        pass

    def process(self, email: 'EmailContent'):
        LOG.info("Processing email: %s", email)


class NoOpEmailContentProcessor(EmailContentProcessor):
    def __init__(self):
        pass

    def process(self, email: 'EmailContent'):
        pass


class GroupingEmailMessageProcessor(EmailMessageProcessor):
    def __init__(self, result_type: ProcessorResultType):
        self.senders = []
        self.recipients = []
        self.subjects = []
        self.senders_set = set()
        self.grouping_by_sender = defaultdict(list)
        self.result_type = result_type

        self._visited_senders = set()
        self._row_producers = {ProcessorResultType.SIMPLIFIED: self._produce_simplified_row,
                               ProcessorResultType.SIMPLIFIED_WITH_LABELS: self._produce_simplified_with_labels_row,
                               ProcessorResultType.DETAILED: self._produce_detailed_row,
                               }

    def process(self, message: 'GmailMessage'):
        # This does print the whole email
        # LOG.info("Processing email: %s", message)

        self.senders_set.add(message.sender_email)
        self.senders.append(message.sender_email)
        self.recipients.append(message.recipient)
        self.subjects.append(message.subject)

        if len(self.senders_set) > 1:
            # This can happen in a following case:
            # Sender X sends a mail to email Z
            # Z forwards the mail to recipient Y
            # So Z becomes the sender and Sender X was the original sender
            # TODO Debug this with warning log
            # LOG.warning("Multiple senders found for email thread. Sender, recipient, subject: %s",
            #             list(zip(self.senders, self.recipients, self.subjects)))
            pass

        self.grouping_by_sender[message.sender_email].append((message.thread_id, message))

    def convert_to_table_rows(self):
        if not self.result_type in self._row_producers:
            raise NotImplementedError(f"Unknown result type: {self.result_type}, there is no row producer defined for this type!")
        row_producer = self._row_producers[self.result_type]
        grouping_for_result_table, table_rows = self._get_results(row_producer)
        return grouping_for_result_table, table_rows

    def _produce_simplified_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        if sender not in self._visited_senders:
            self._visited_senders.add(sender)
            # TODO Returned list of data assumes specific order coming from: GroupingEmailMessageProcessorRepresentation.get_cols
            #   ["Sender", "Count from this sender"]
            #   Use dict instead?
            return [sender,
                str(no_of_messages_from_sender)
                ]
        # This sender was already visited, do not return new row for this sender again
        return None

    def _produce_simplified_with_labels_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        if sender not in self._visited_senders:
            self._visited_senders.add(sender)
            # TODO Returned list of data assumes specific order coming from: GroupingEmailMessageProcessorRepresentation.get_cols
            #   ["Sender", "Count from this sender"]
            #   Use dict instead?
            labels = ""
            if message.labels:
                labels = ",".join(message.labels)
            return [sender,
                    str(no_of_messages_from_sender),
                    message.recipient_email,
                    message.date_str,
                    message.subject,
                    thread_id,
                    message.msg_id,
                    labels]
        return None

    def _produce_detailed_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        # TODO Returned list of data assumes specific order coming from: GroupingEmailMessageProcessorRepresentation.get_cols
        #   ["Sender", "Count from this sender", "Recipient", "Date", "Subject", "Thread ID", "Message ID"]
        #   Use dict instead?
        return [sender,
                str(no_of_messages_from_sender),
                message.recipient_email,
                message.date_str,
                message.subject,
                thread_id,
                message.msg_id]

    def _get_results(self, row_producer: Callable[[str, GmailMessage, str, int], None]):
        # TODO This must be fixed, do not return two results
        grouping_for_result_table: Dict[str, Dict[str, Any]] = defaultdict(dict)
        table_rows = []

        # 1. grouping_for_result_table -> First, group by sender
        for sender, thread_message_lst in self.grouping_by_sender.items():
            no_of_messages_from_sender = len(thread_message_lst)
            # TODO add gmail query URL for each recipient: https://mail.google.com/mail/u/0/#search/label%3Ainbox
            sender_key = f"Sender: {sender}"
            for thread_message in thread_message_lst:
                thread = thread_message[0]
                message = thread_message[1]
                if THREADS_KEY not in grouping_for_result_table[sender_key]:
                    grouping_for_result_table[sender_key][THREADS_KEY] = set()
                grouping_for_result_table[sender_key][THREADS_KEY].add((thread, message.subject))
                row = row_producer(thread, message, sender, no_of_messages_from_sender)
                if row:
                    table_rows.append(row)

        # 2. grouping_for_result_table -> Second, group by inbox and labeled
        visited_threads = set()
        groups: Dict[str, Dict[str, Any]] = {UNLABELED_KEY: {THREADS_KEY: set()},
                                             LABELED_KEY: {THREADS_KEY: set()}}
        for sender, thread_message_lst in self.grouping_by_sender.items():
            for thread_message in thread_message_lst:
                thread = thread_message[0]
                message = thread_message[1]
                if thread not in visited_threads:
                    visited_threads.add(thread)
                    if not message.is_in_inbox:
                        # raise ValueError(f"Every message should have the inbox label. Encountered Thread: {thread}, Message: {message}")
                        # Skip non-inbox emails for now
                        continue
                    if message.is_in_inbox and not message.labels:
                        groups[UNLABELED_KEY][THREADS_KEY].add((thread, message.subject))
                    elif message.labels:
                        groups[LABELED_KEY][THREADS_KEY].add((thread, message.subject))

                    for label in message.labels:
                        l_key = f"Label: {label}"
                        if l_key not in groups:
                            groups[l_key] = {THREADS_KEY: set()}
                        groups[l_key][THREADS_KEY].add((thread, message.subject))

        # TODO Add sanity check: sum up count of Label[count] keys and compare value with Labeled[count]
        grouping_for_result_table.update(groups)
        for k, dic in grouping_for_result_table.items():
            dic[COUNT_KEY] = len(dic[THREADS_KEY])

        # TODO temporarily remove key: THREADS (we are not interested in threads now, just the aggregate count
        for group, dic in grouping_for_result_table.items():
            del dic[THREADS_KEY]
        return grouping_for_result_table, table_rows

class MultipleFilterResultProcessor(EmailMessageProcessor):
    def __init__(self):
        self.count_per_filter = {}
        self._filters_by_description = {}

    def process(self, message: 'GmailMessage'):
        # No-op for this processor
        pass

    def convert_to_table_rows(self):
        return self._get_rows()

    def _get_rows(self):
        rows = []
        for filter_desc, count in self.count_per_filter.items():
            filter = self._filters_by_description[filter_desc]
            rows.append([filter_desc, count, filter.gmail_link])
        return rows

    def add_result(self, filter: 'GmailFilter', processor_results):
        self._filters_by_description[filter.description] = filter
        self.count_per_filter[filter.description] = processor_results["count"]



