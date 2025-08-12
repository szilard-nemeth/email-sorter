import logging
from collections import defaultdict
from typing import List, Any, Dict

from rich.table import Table

from emailsorter.display.console import CliLogger

LOG = logging.getLogger(__name__)
CLI_LOG = CliLogger(LOG)


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
                 sort_by_column: str=None):
        if not col_styles:
            raise ValueError("col_styles cannot be None!")
        self._col_styles: TableColumnStyles = col_styles
        self._wide_print = wide_print
        self._show_lines = show_lines
        self.sort_by_column = sort_by_column

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
        return {"show_lines": self._show_lines}


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

    def render(self, rows: List[List[Any]]):
        self._rows = rows
        self._rows = self._do_sorting(rows)

        for row in self._rows:
            vals = [self._render_settings.format_value(self._cols[idx], val) for idx, val in enumerate(row)]
            self._table.add_row(*vals)

    def _do_sorting(self, rows):
        def is_numeric_column(col_idx):
            for row in rows:
                try:
                    int(row[col_idx])
                except (ValueError, TypeError):
                    return False
            return True

        sort_by_column = self.get_sort_by_column()
        sort_by_column_idx = self.get_sort_by_column_idx(sort_by_column)

        LOG.debug("Sorting by column: %s", sort_by_column)
        LOG.debug("Column index: %s", sort_by_column_idx)
        LOG.debug("First 5 values to sort by: %s", [row[sort_by_column_idx] for row in rows[:5]])

        # if sort_by_column:
        #     rows = sorted(rows, key=lambda row: int(row[sort_by_column_idx]), reverse=True)
        if sort_by_column:
            if is_numeric_column(sort_by_column_idx):
                rows = sorted(rows, key=lambda row: int(row[sort_by_column_idx]), reverse=True)
            else:
                rows = sorted(rows, key=lambda row: str(row[sort_by_column_idx]).lower(), reverse=False)
        return rows

    def print(self):
        CLI_LOG.print(self._table, wide_print=self._render_settings._wide_print)

    def get_sort_by_column(self):
        col = self._render_settings.sort_by_column
        if col:
            if col not in self._cols:
                raise ValueError(f"Invalid sort by column: {col}. Available column names are: {self._cols}")
            return col
        return None

    def get_sort_by_column_idx(self, col: str):
        for idx, c in enumerate(self._cols):
            if c == col:
                return idx
        return -1


