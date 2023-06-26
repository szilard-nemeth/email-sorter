from abc import abstractmethod, ABC


import logging
LOG = logging.getLogger(__name__)


class EmailContentProcessor(ABC):
    @abstractmethod
    def process(self, email_content: 'EmailContent'):
        pass


class PrintingEmailContentProcessor(EmailContentProcessor):
    def __init__(self):
        pass

    def process(self, email: 'EmailContent'):
        LOG.info("Processing email: %s", email)
