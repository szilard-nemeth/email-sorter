import datetime
import logging
import time
from dataclasses import dataclass
from pprint import pformat
from typing import List, Iterable, Tuple

import rich
from googleapiwrapper.gmail_api import ThreadQueryResults
from googleapiwrapper.gmail_domain import GmailMessage, ThreadQueryFormat
from pythoncommons.file_utils import FileUtils

from emailsorter.common.model import EmailContentProcessor, PrintingEmailContentProcessor, \
    GroupingEmailMessageProcessor, EmailMessageProcessor, NoOpEmailContentProcessor, ProcessorResultType
from emailsorter.core.common import CommandType, EmailSorterConfig
from emailsorter.core.constants import DEFAULT_LINE_SEP

from emailsorter.core.output import InboxDiscoveryResults, GroupingEmailMessageProcessorRepresentation, \
    GroupingEmailMessageProcessorRepresentation, ProcessorRepresentationAbs
from emailsorter.display.console import CliLogger
from emailsorter.display.table import TableRenderSettings

LOG = logging.getLogger(__name__)

SUBJECT = "subject:"
CMD = CommandType.EMAIL_SORTER

CLI_LOG = CliLogger(LOG)


@dataclass
class EmailContent:
    msg_id: str
    thread_id: str
    date: datetime.datetime
    subject: str
    lines: Iterable[str]


class InboxDiscoveryConfig:
    def __init__(self, email_sorter_ctx, gmail_query, offline_mode: bool, request_limit=1000000):
        #self.session_dir = ProjectUtils.get_session_dir_under_child_dir(FileUtils.basename(output_dir))
        FileUtils.create_symlink_path_dir(
            CMD.session_link_name,
            email_sorter_ctx.session_dir,
            EmailSorterConfig.PROJECT_OUT_ROOT,
        )
        self.gmail_query = gmail_query
        self.request_limit = request_limit
        self.offline_mode = offline_mode
        self.content_line_sep = DEFAULT_LINE_SEP


class InboxDiscovery:
    def __init__(self, config, email_sorter_ctx):
        self.config: InboxDiscoveryConfig = config
        self.ctx = email_sorter_ctx

    def run(self):
        LOG.info(f"Starting Gmail Inbox discovery. Config: \n{str(self.config)}")
        # TODO use ThreadQueryFormat.MINIMAL or ThreadQueryFormat.METADATA to get only subject, sender, title, labels, etc.
        # TODO Add new method to gmail_wrapper that only works from cache
        start_time = time.time()
        query_result: ThreadQueryResults = self.ctx.gmail_wrapper.query_threads(
            query=self.config.gmail_query,
            limit=self.config.request_limit,
            expect_one_message_per_thread=True,
            format=ThreadQueryFormat.FULL,
            show_empty_body_errors=False,
            offline=self.config.offline_mode
        )
        LOG.trace(f"Received thread query result: {query_result}")
        end_time = time.time()
        seconds = end_time - start_time
        LOG.info("Fetched email threads in %d seconds", seconds)

        result_type = ProcessorResultType.SIMPLIFIED
        grouping_processor = GroupingEmailMessageProcessor(result_type)
        self.process_gmail_results(query_result,
                                   split_body_by=self.config.content_line_sep,
                                   email_content_processors=[NoOpEmailContentProcessor()],
                                   email_message_processors=[grouping_processor])
        grouping_for_result_table, table_rows = grouping_processor.convert_to_table_rows()

        # TODO order table rows by 'no_of_messages_from_sender'
        rich.print(grouping_for_result_table)
        InboxDiscovery.print_result_table(table_rows, GroupingEmailMessageProcessorRepresentation(result_type))

    @staticmethod
    def process_gmail_results(
        query_result: ThreadQueryResults,
        split_body_by: str,
        email_content_processors: Iterable[EmailContentProcessor],
        email_message_processors: Iterable[EmailMessageProcessor]
    ):
        if not email_content_processors:
            email_content_processors = []

        skipped_emails: List[EmailContent] = []
        for message in query_result.threads.messages:
            email_content = InboxDiscovery._create_email_content(message, split_body_by)
            # TODO print date
            LOG.debug("Processing message: %s", email_content.subject)

            # Email content processor is invoked with original lines from email (except stripping)
            for p in email_content_processors:
                p.process(email_content)

            for p in email_message_processors:
                p.process(message)

        if skipped_emails:
            LOG.warning(
                "The following emails were skipped: %s",
                pformat(skipped_emails),
            )

    @staticmethod
    def _create_email_content(message: GmailMessage, split_body_by: str):
        # Extract all lines first (from all message parts)
        all_lines = []
        for msg_part in message.get_all_plain_text_parts():
            if not isinstance(msg_part.body_data, str):
                print("INSTANCE IS WRONG: " + str(msg_part.body_data))
                continue
            lines = msg_part.body_data.split(split_body_by)
            lines = list(map(lambda line: line.strip(), lines))
            all_lines.extend(lines)

        return EmailContent(
            message.msg_id,
            message.thread_id,
            message.date,
            message.subject,
            all_lines,
        )

    @staticmethod
    def _check_if_line_is_valid(line, skip_lines_starting_with):
        for skip_str in skip_lines_starting_with:
            if line.startswith(skip_str):
                return False
        return True

    @classmethod
    def print_result_table(cls, rows, processor_repr: ProcessorRepresentationAbs):
        # TODO implement console mode --> Just print this and do not log anything to console other than the table
        # TODO add progressbar while loading emails

        CLI_LOG.record_console()
        cols = processor_repr.get_cols()
        col_styles = processor_repr.get_col_styles()
        render_settings = TableRenderSettings(col_styles, wide_print=True, show_lines=False)
        InboxDiscoveryResults.print(rows, cols, render_settings)
        out_file = "/tmp/rich_table_output.html"
        files = CLI_LOG.export_to_html(out_file)
        CLI_LOG.info("Saved console output to HTML files: %s", files)

        LOG.info("Execute: ")
        LOG.info("open " + out_file)
