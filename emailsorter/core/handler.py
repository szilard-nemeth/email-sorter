import logging

from googleapiwrapper.gmail_domain import ThreadQueryFormat

from emailsorter.actions.inbox_discovery import InboxDiscovery, InboxDiscoveryConfig
from emailsorter.core.context import EmailSorterContext

logger = logging.getLogger(__name__)


class MainCommandHandler:
    """Entry point for the CLI commands.

    Owns the construction of InboxDiscoveryConfig + InboxDiscovery so the CLI
    layer stays limited to option parsing and delegates all work here.
    """

    def __init__(self, ctx: EmailSorterContext):
        self.ctx = ctx

    def discover_inbox(self, gmail_query: str, fetch_mode: ThreadQueryFormat, offline_mode: bool):
        conf = InboxDiscoveryConfig(
            self.ctx,
            gmail_query=gmail_query,
            fetch_mode=fetch_mode,
            offline_mode=offline_mode,
        )
        InboxDiscovery(conf, self.ctx).run()

    def filter_stats(self, filters_file, gmail_query: str, fetch_mode: ThreadQueryFormat, offline_mode: bool):
        conf = InboxDiscoveryConfig(
            self.ctx,
            gmail_query=gmail_query,
            fetch_mode=fetch_mode,
            offline_mode=offline_mode,
        )
        InboxDiscovery(conf, self.ctx).create_filter_stats(filters_file)
