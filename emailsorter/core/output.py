from abc import ABC, abstractmethod

from emailsorter.common.model import (
    ProcessorResultType,
    COL_SENDER, COL_COUNT, COL_RECIPIENT, COL_DATE, COL_SUBJECT,
    COL_THREAD_ID, COL_MSG_ID, COL_LABELS,
    COL_FILTER, COL_FILTER_COUNT, COL_GMAIL_LINK,
)
from emailsorter.display.table import TableColumnStyles, TableRenderSettings, EmailTable


class InboxDiscoveryResults:
    @staticmethod
    def print(rows, cols, render_settings: TableRenderSettings):
        table = EmailTable(cols, render_settings)
        table.render(rows)
        table.print()


class ProcessorRepresentationAbs(ABC):
    @abstractmethod
    def get_cols(self):
        pass

    @abstractmethod
    def get_col_styles(self):
        pass


class GroupingEmailMessageProcessorRepresentation(ProcessorRepresentationAbs):
    def __init__(self, result_type: ProcessorResultType):
        self.result_type = result_type

    def get_cols(self):
        if self.result_type == ProcessorResultType.SIMPLIFIED:
            return [COL_SENDER, COL_COUNT]
        elif self.result_type == ProcessorResultType.DETAILED:
            return [COL_SENDER, COL_COUNT, COL_RECIPIENT, COL_DATE, COL_SUBJECT, COL_THREAD_ID, COL_MSG_ID]
        elif self.result_type == ProcessorResultType.SIMPLIFIED_WITH_LABELS:
            return [COL_SENDER, COL_COUNT, COL_RECIPIENT, COL_DATE, COL_SUBJECT, COL_THREAD_ID, COL_MSG_ID, COL_LABELS]
        else:
            raise NotImplementedError(f"Rendering not implemented for {self.result_type}")

    def get_col_styles(self):
        col_styles = TableColumnStyles()
        if self.result_type == ProcessorResultType.DETAILED:
            (col_styles
             .bind_style(COL_SENDER, "cyan")
             .bind_format_to_column(COL_SENDER, no_wrap=True, justify="left")
             .bind_style(COL_COUNT, "cyan")
             .bind_format_to_column(COL_COUNT, no_wrap=True, justify="right")
             .bind_style(COL_RECIPIENT, "magenta")
             .bind_format_to_column(COL_RECIPIENT, no_wrap=True)
             .bind_format_to_column(COL_DATE, no_wrap=True)
             .bind_format_to_column(COL_SUBJECT, no_wrap=False, overflow="ellipsis")
             .bind_format_to_column(COL_THREAD_ID, no_wrap=True)
             .bind_format_to_column(COL_MSG_ID, no_wrap=True))
        elif self.result_type == ProcessorResultType.SIMPLIFIED:
            (col_styles
             .bind_style(COL_SENDER, "cyan")
             .bind_format_to_column(COL_SENDER, no_wrap=True, justify="left")
             .bind_style(COL_COUNT, "cyan")
             .bind_format_to_column(COL_COUNT, no_wrap=True, justify="right"))
        elif self.result_type == ProcessorResultType.SIMPLIFIED_WITH_LABELS:
            (col_styles
             .bind_style(COL_SENDER, "cyan")
             .bind_format_to_column(COL_SENDER, no_wrap=True, justify="left")
             .bind_style(COL_COUNT, "cyan")
             .bind_format_to_column(COL_COUNT, no_wrap=True, justify="right")
             .bind_style(COL_LABELS, "blue")
             .bind_format_to_column(COL_LABELS, no_wrap=True, justify="left"))
        else:
            raise NotImplementedError(f"Rendering not implemented for {self.result_type}")
        return col_styles


class MultipleFilterResultProcessorRepresentation(ProcessorRepresentationAbs):
    def __init__(self):
        pass

    def get_cols(self):
        return [COL_FILTER, COL_FILTER_COUNT, COL_GMAIL_LINK]

    def get_col_styles(self):
        col_styles = TableColumnStyles()
        (col_styles
         .bind_style(COL_FILTER, "cyan")
         .bind_format_to_column(COL_FILTER, no_wrap=True, justify="left")
         .bind_style(COL_FILTER_COUNT, "cyan")
         .bind_format_to_column(COL_FILTER_COUNT, no_wrap=True, justify="right")
         .bind_style(COL_GMAIL_LINK, "yellow")
         .bind_format_to_column(COL_GMAIL_LINK, no_wrap=True, justify="right"))
        return col_styles