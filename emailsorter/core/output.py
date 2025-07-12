from abc import ABC, abstractmethod

from emailsorter.common.model import ProcessorResultType
from emailsorter.display.table import TableColumnStyles, TableRenderSettings, EmailTable


class InboxDiscoveryResults:
    @staticmethod
    def print(rows, cols, render_settings: TableRenderSettings):
        # TODO add this to TableRenderSettings: title="Grouping results", expand=True, min_width=300
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
            return ["Sender", "Count from this sender"]
        elif self.result_type == ProcessorResultType.DETAILED:
            return ["Sender", "Count from this sender", "Recipient", "Date", "Subject", "Thread ID", "Message ID"]
        return None

    def get_col_styles(self):
        col_styles = TableColumnStyles()
        if self.result_type == ProcessorResultType.DETAILED:
            (col_styles
             .bind_style("Sender", "cyan")
             .bind_format_to_column("Sender", no_wrap=True, justify="left")
             .bind_style("Count from this sender", "cyan")
             .bind_format_to_column("Count from this sender", no_wrap=True, justify="right")
             .bind_style("Recipient", "magenta")
             .bind_format_to_column("Recipient", no_wrap=True)
             .bind_format_to_column("Date", no_wrap=True)
             .bind_format_to_column("Subject", no_wrap=False, overflow="ellipsis")
             .bind_format_to_column("Thread ID", no_wrap=True)
             .bind_format_to_column("Message ID", no_wrap=True))
        elif self.result_type == ProcessorResultType.SIMPLIFIED:
            (col_styles
             .bind_style("Sender", "cyan")
             .bind_format_to_column("Sender", no_wrap=True, justify="left")
             .bind_style("Count from this sender", "cyan")
             .bind_format_to_column("Count from this sender", no_wrap=True, justify="right"))
        return col_styles
