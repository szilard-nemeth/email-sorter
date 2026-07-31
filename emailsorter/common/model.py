from abc import abstractmethod, ABC


import logging
from collections import defaultdict
from enum import Enum
from typing import Iterable, Callable, Dict, List

from googleapiwrapper.gmail_domain import GmailMessage

UNLABELED_KEY = "Unlabeled (just Inbox)"
LABELED_KEY = "Labeled"

# Column-name constants for GroupingEmailMessageProcessor rows.
# Both the row producers and GroupingEmailMessageProcessorRepresentation.get_cols()
# reference these — the single source of truth that eliminates positional coupling.
COL_SENDER = "Sender"
COL_COUNT = "Count from this sender"
COL_RECIPIENT = "Recipient"
COL_DATE = "Date"
COL_SUBJECT = "Subject"
COL_THREAD_ID = "Thread ID"
COL_MSG_ID = "Message ID"
COL_LABELS = "Labels"

# Column-name constants for MultipleFilterResultProcessor rows.
COL_FILTER = "Filter"
COL_FILTER_COUNT = "Count"
COL_GMAIL_LINK = "Gmail link"

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
    def convert_to_table_rows(self) -> List[Dict[str, str]]:
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
            LOG.warning(
                "Multiple senders found across processed messages. Sender/recipient/subject triples so far: %s",
                list(zip(self.senders, self.recipients, self.subjects)),
            )

        self.grouping_by_sender[message.sender_email].append((message.thread_id, message))

    def convert_to_table_rows(self) -> List[Dict[str, str]]:
        """Produce sender-grouped rows for the main results table.

        Rows are dicts keyed by column name (see COL_* constants). Which keys
        each row contains is dictated by the active ProcessorResultType and
        must match the matching GroupingEmailMessageProcessorRepresentation.get_cols().
        """
        if not self.result_type in self._row_producers:
            raise NotImplementedError(f"Unknown result type: {self.result_type}, there is no row producer defined for this type!")
        row_producer = self._row_producers[self.result_type]

        table_rows: List[Dict[str, str]] = []
        for sender, thread_message_lst in self.grouping_by_sender.items():
            no_of_messages_from_sender = len(thread_message_lst)
            # TODO add gmail query URL for each recipient: https://mail.google.com/mail/u/0/#search/label%3Ainbox
            for thread_id, message in thread_message_lst:
                row = row_producer(thread_id, message, sender, no_of_messages_from_sender)
                if row:
                    table_rows.append(row)
        return table_rows

    def build_label_summary(self) -> Dict[str, int]:
        """Aggregate thread counts per label bucket.

        Buckets:
          - UNLABELED_KEY: threads in Inbox with no user labels
          - LABELED_KEY:   threads in Inbox that carry at least one user label
          - "Label: {name}": one bucket per individual user label

        A single thread contributes to LABELED_KEY at most once but appears
        under every one of its labels. Non-inbox threads are skipped.
        """
        summary: Dict[str, int] = {UNLABELED_KEY: 0, LABELED_KEY: 0}
        visited_threads = set()

        for thread_message_lst in self.grouping_by_sender.values():
            for thread_id, message in thread_message_lst:
                if thread_id in visited_threads:
                    continue
                visited_threads.add(thread_id)

                if not message.is_in_inbox:
                    # Skip non-inbox emails; every message is expected to carry
                    # the inbox label but this can happen with archived threads.
                    continue

                if not message.labels:
                    summary[UNLABELED_KEY] += 1
                else:
                    summary[LABELED_KEY] += 1
                    for label in message.labels:
                        l_key = f"Label: {label}"
                        summary[l_key] = summary.get(l_key, 0) + 1

        # Sanity check: per-label counts should sum to LABELED_KEY (a thread with
        # N labels contributes N to the per-label sum but 1 to LABELED_KEY, so
        # the equality only holds when every labeled thread has exactly one label).
        per_label_total = sum(v for k, v in summary.items() if k.startswith("Label: "))
        if per_label_total < summary[LABELED_KEY]:
            LOG.warning(
                "Label summary inconsistency: sum(per-label)=%d < Labeled=%d",
                per_label_total, summary[LABELED_KEY],
            )
        return summary

    def _produce_simplified_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        if sender in self._visited_senders:
            # This sender was already visited, do not return new row for this sender again
            return None
        self._visited_senders.add(sender)
        return {
            COL_SENDER: sender,
            COL_COUNT: str(no_of_messages_from_sender),
        }

    def _produce_simplified_with_labels_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        if sender in self._visited_senders:
            return None
        self._visited_senders.add(sender)
        labels = ",".join(message.labels) if message.labels else ""
        return {
            COL_SENDER: sender,
            COL_COUNT: str(no_of_messages_from_sender),
            COL_RECIPIENT: message.recipient_email,
            COL_DATE: message.date_str,
            COL_SUBJECT: message.subject,
            COL_THREAD_ID: thread_id,
            COL_MSG_ID: message.msg_id,
            COL_LABELS: labels,
        }

    def _produce_detailed_row(self, thread_id: str, message: GmailMessage, sender: str, no_of_messages_from_sender: int):
        return {
            COL_SENDER: sender,
            COL_COUNT: str(no_of_messages_from_sender),
            COL_RECIPIENT: message.recipient_email,
            COL_DATE: message.date_str,
            COL_SUBJECT: message.subject,
            COL_THREAD_ID: thread_id,
            COL_MSG_ID: message.msg_id,
        }

class MultipleFilterResultProcessor(EmailMessageProcessor):
    def __init__(self):
        self.count_per_filter = {}
        self._filters_by_description = {}

    def process(self, message: 'GmailMessage'):
        # No-op for this processor
        pass

    def convert_to_table_rows(self) -> List[Dict[str, str]]:
        return self._get_rows()

    def _get_rows(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for filter_desc, count in self.count_per_filter.items():
            filter = self._filters_by_description[filter_desc]
            rows.append({
                COL_FILTER: filter_desc,
                COL_FILTER_COUNT: str(count),
                COL_GMAIL_LINK: filter.gmail_link,
            })
        return rows

    def add_result(self, filter: 'GmailFilter', processor_results):
        self._filters_by_description[filter.description] = filter
        self.count_per_filter[filter.description] = processor_results["count"]



