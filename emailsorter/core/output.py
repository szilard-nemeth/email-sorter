from emailsorter.display.table import TableColumnStyles, TableRenderSettings, EmailTable


class InboxDiscoveryResults:
    @staticmethod
    def print(rows):
        # row = [sender, message.recipient, message.date_str, message.subject, thread.api_id, message.msg_id]

        # TODO add this to TableRenderSettings: title="Grouping results", expand=True, min_width=300
        col_styles = TableColumnStyles()
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

        render = TableRenderSettings(col_styles, wide_print=True, show_lines=False)
        cols=["Sender", "Count from this sender", "Recipient", "Date", "Subject", "Thread ID", "Message ID"]
        table = EmailTable(cols, render)
        table.render(rows)
        table.print()


    @staticmethod
    def print_table(table: EmailTable, rows):
        table.render(rows)
        table.print()
