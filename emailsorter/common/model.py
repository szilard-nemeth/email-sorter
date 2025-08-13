from abc import abstractmethod, ABC


import logging
from collections import defaultdict
from enum import Enum
from typing import Iterable, Callable

from googleapiwrapper.gmail_domain import GmailMessage

LOG = logging.getLogger(__name__)

class ProcessorResultType(Enum):
    SIMPLIFIED = "simplified"
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
        row_producer = self._produce_simplified_row if self.result_type == ProcessorResultType.SIMPLIFIED else self._produce_detailed_row
        grouping_for_result_table, table_rows = self._get_results(row_producer)
        return grouping_for_result_table, table_rows

    def _produce_simplified_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        if sender not in self._visited_senders:
            self._visited_senders.add(sender)
            return [sender,
                str(no_of_messages_from_sender)
                ]
        # This sender was already visited, do not return new row for this sender again
        return None

    def _produce_detailed_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        return [sender,
                str(no_of_messages_from_sender),
                message.recipient_email,
                message.date_str,
                message.subject,
                thread_id,
                message.msg_id]

    def _get_results(self, row_producer: Callable[[str, GmailMessage, str, int], None]):
        grouping_for_result_table = {}
        table_rows = []
        for sender, thread_message_lst in self.grouping_by_sender.items():
            no_of_messages_from_sender = len(thread_message_lst)
            # TODO add gmail query URL for each recipient: https://mail.google.com/mail/u/0/#search/label%3Ainbox

            for thread_message in thread_message_lst:
                thread = thread_message[0]
                message = thread_message[1]
                grouping_for_result_table[sender] = (thread, message.msg_id, message.subject)
                row = row_producer(thread, message, sender, no_of_messages_from_sender)
                if row:
                    table_rows.append(row)
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



