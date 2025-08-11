import logging
import time

import click
from pythoncommons.constants import ExecutionMode
from rich import print as rich_print, box
from rich.table import Table

from emailsorter.core.error import EmailSorterException
from emailsorter.actions.inbox_discovery import InboxDiscovery, InboxDiscoveryConfig
from emailsorter.core.context import EmailSorterContext
from emailsorter.core.handler import MainCommandHandler
from initializer import Initializer

GMAIL_QUERY_INBOX = "label:inbox"
GMAIL_QUERY_LABEL_EXTERNAL = "label:external"

LOG = logging.getLogger(__name__)


@click.group()
@click.option('-e', '--account-email', help='Account\'s email address', required=True)
@click.option('-d', '--debug', is_flag=True, help='turn on DEBUG level logging')
@click.option('-t', '--trace', is_flag=True, help='turn on TRACE level logging')
@click.pass_context
def cli(ctx, account_email, debug: bool, trace: bool):
    if ctx.invoked_subcommand == "usage":
        return

    level = logging.DEBUG if debug else logging.INFO
    Initializer.configure_logging(debug, trace)

    ctx.ensure_object(dict)
    ctx.obj['loglevel'] = level

    LOG.info("Invoked command {}".format(ctx.invoked_subcommand))
    context = EmailSorterContext(account_email=account_email)
    ctx.obj['handler'] = MainCommandHandler(context)


@cli.command()
@click.option('-n', '--no-wrap', is_flag=True, help='Turns off the wrapping')
def usage(no_wrap: bool = False):
    """
    Prints the aggregated usage of Email sorter
    """
    table = Table(title="Email Sorter CLI", show_lines=True, box=box.SQUARE)
    table.add_column("Command")
    table.add_column("Description")
    table.add_column("Options", no_wrap=no_wrap)

    def recursive_help(cmd, parent=None, is_root: bool = False):
        ctx = click.core.Context(cmd, info_name=cmd.name, parent=parent)
        commands = getattr(cmd, 'commands', {})
        help = list(filter(bool, cmd.get_help(ctx).split("\n")))
        if is_root:
            command = help[0]
            cmd_id = help.index("Commands:")
            desc = "\n".join(help[2:cmd_id])
            options = "\n".join(help[cmd_id + 1:])
        else:
            command = help[0]
            desc = help[1]
            options = "\n".join(help[3:])
            table.add_row(command, desc, options)

        for sub in commands.values():
            recursive_help(sub, ctx)

    recursive_help(cli, is_root=True)
    rich_print(table)


@cli.command()
@click.option('-o', '--offline', is_flag=True, help='Offline mode, only work from cache')
@click.option('-mq', '--main-query', help='Main query to filter gmail results off. Default is: All items from Gmail inbox')
@click.pass_context
def discover_inbox(ctx, offline, main_query: str):
    """
    Discovers Inbox
    """
    handler: MainCommandHandler = ctx.obj['handler']
    email_sorter_ctx = handler.ctx

    if not main_query:
        main_query = GMAIL_QUERY_INBOX

    conf = InboxDiscoveryConfig(email_sorter_ctx,
                                gmail_query=main_query,
                                offline_mode=offline)
    discovery = InboxDiscovery(conf, email_sorter_ctx)
    discovery.run()


if __name__ == "__main__":
    LOG.info("Started application")
    Initializer.setup_dirs(execution_mode=ExecutionMode.PRODUCTION)
    before = time.time()
    try:
        cli()
        after = time.time()
        LOG.info("Executed successfully after %d seconds", int(after - before))
    except EmailSorterException as e:
        LOG.error(str(e))
        after = time.time()
        LOG.info("Error during execution after %d seconds", int(after - before))
        exit(1)
