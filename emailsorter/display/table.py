import logging
from collections import defaultdict
from typing import List, Any, Dict

from rich.table import Table

from emailsorter.display.console import CliLogger

LOG = logging.getLogger(__name__)
CLI_LOG = CliLogger(LOG)

# TODO Move from dexter and check diff: table.py + ReApiReportAbs + one report Impl
class TableColumnStyles:
    def __init__(self):
        self._color_by_value: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._style_by_col: Dict[str, str] = defaultdict(dict)
        self._style_dict_per_column: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def bind_color(self, col_name: str, value: str, color: str):
        self._color_by_value[col_name][value] = color
        return self

    def bind_style(self, col_name: str, style: str):
        self._style_by_col[col_name] = style
        return self

    def bind_format_to_column(self, col: str, no_wrap: bool = False, justify: str = None, overflow: str = None):
        self._style_dict_per_column[col]["no_wrap"] = no_wrap
        if justify:
            self._style_dict_per_column[col]["justify"] = justify
        if overflow:
            self._style_dict_per_column[col]["overflow"] = overflow
        return self

    def style_by_col(self, col: str):
        try:
            style = self._style_by_col[col]
        except KeyError:
            style = ""
        return style

    def color_by_value(self, col: str, val: str):
        try:
            color = self._color_by_value[col][val]
        except KeyError:
            color = ""
        return color

    def get_column_style_dict(self, col):
        return self._style_dict_per_column[col]


class TableRenderSettings:
    def __init__(self, col_styles: TableColumnStyles, wide_print=False, show_lines=False,
                 sort_by_column: str = None, title: str = None, expand: bool = False,
                 min_width: int = None):
        if not col_styles:
            raise ValueError("col_styles cannot be None!")
        self._col_styles: TableColumnStyles = col_styles
        self._wide_print = wide_print
        self._show_lines = show_lines
        self.sort_by_column = sort_by_column
        self._title = title
        self._expand = expand
        self._min_width = min_width

    def format_value(self, col: str, val: str):
        style = self._col_styles.style_by_col(col)
        color = self._col_styles.color_by_value(col, val)
        if style:
            rich_style = f"[{style} {color}]"
        elif color:
            rich_style = f"[{color}]"
        else:
            rich_style = ""
        return f"{rich_style}{val}"

    def get_column_style_dict(self, col_name: str):
        return self._col_styles.get_column_style_dict(col_name)

    def get_table_config_dict(self):
        config = {"show_lines": self._show_lines, "expand": self._expand}
        if self._title is not None:
            config["title"] = self._title
        if self._min_width is not None:
            config["min_width"] = self._min_width
        return config


class EmailTable:
    def __init__(self, cols: List[str], render_settings: TableRenderSettings):
        self._render_settings: TableRenderSettings = render_settings
        self._cols = cols
        self._rows = None
        self._table = Table(**self._render_settings.get_table_config_dict())

        for col in cols:
            # https://rich.readthedocs.io/en/stable/tables.html#column-options
            col_style_dict = self._render_settings.get_column_style_dict(col)
            self._table.add_column(col, **col_style_dict)

    def render(self, rows: List[Dict[str, Any]]):
        """Render rows into the underlying Rich table.

        Each row is a dict keyed by column name; the value under a column that
        this table does not declare is dropped. A column declared by the table
        but missing from a row renders as an empty cell.
        """
        self._rows = self._do_sorting(rows)

        for row in self._rows:
            vals = [
                self._render_settings.format_value(col, row.get(col, ""))
                for col in self._cols
            ]
            self._table.add_row(*vals)

    def _do_sorting(self, rows: List[Dict[str, Any]]):
        sort_by_column = self.get_sort_by_column()
        if not sort_by_column:
            return rows

        def is_numeric_column(col: str) -> bool:
            for row in rows:
                try:
                    int(row.get(col, ""))
                except (ValueError, TypeError):
                    return False
            return True

        LOG.debug("Sorting by column: %s", sort_by_column)
        LOG.debug("First 5 values to sort by: %s", [row.get(sort_by_column) for row in rows[:5]])

        if is_numeric_column(sort_by_column):
            return sorted(rows, key=lambda row: int(row.get(sort_by_column, 0)), reverse=True)
        return sorted(rows, key=lambda row: str(row.get(sort_by_column, "")).lower())

    def print(self):
        CLI_LOG.print(self._table, wide_print=self._render_settings._wide_print)

    def get_sort_by_column(self):
        col = self._render_settings.sort_by_column
        if col:
            if col not in self._cols:
                raise ValueError(f"Invalid sort by column: {col}. Available column names are: {self._cols}")
            return col
        return None


