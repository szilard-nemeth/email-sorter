from abc import abstractmethod, ABC


import logging
from collections import defaultdict
from typing import Iterable

LOG = logging.getLogger(__name__)


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
    def __init__(self):
        self.senders = []
        self.recipients = []
        self.subjects = []
        self.senders_set = set()
        self.grouping_by_sender = defaultdict(list)

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
            LOG.warning("Multiple senders found for email thread. Sender, recipient, subject: %s",
                        list(zip(self.senders, self.recipients, self.subjects)))

        self.grouping_by_sender[message.sender_email].append((message.thread_id, message))

    def convert_to_table_rows(self):
        # TODO grouping_by_sender_2 and table_rows shouldn't be fields!
        self.grouping_by_sender_2 = {}
        self.table_rows = []
        for sender, thread_message_lst in self.grouping_by_sender.items():
            no_of_messages_from_sender = len(thread_message_lst)
            # TODO add gmail query URL for each recipient: https://mail.google.com/mail/u/0/#search/label%3Ainbox

            for thread_message in thread_message_lst:
                thread = thread_message[0]
                message = thread_message[1]
                self.grouping_by_sender_2[sender] = (thread, message.msg_id, message.subject)
                row = [sender,
                       str(no_of_messages_from_sender),
                       message.recipient_email,
                       message.date_str,
                       message.subject,
                       thread,
                       message.msg_id]
                self.table_rows.append(row)
        return self.table_rows


