import logging


logger = logging.getLogger(__name__)


class MainCommandHandler:
    def __init__(self, ctx):
        self.ctx = ctx

    def discover_inbox(self):
        raise NotImplementedError()
