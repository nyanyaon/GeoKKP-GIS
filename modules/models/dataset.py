import json
from qgis.PyQt.QtWidgets import QTableWidgetItem


class DataRow(dict):
    def __init__(self, column_list, column_defn):
        super(DataRow, self).__init__()
        self._column_list = column_list
        self._column_defn = column_defn

        self._populate_default_value()

    def _populate_default_value(self):
        for col in self._column_list:
            val = self._column_defn[col]
            self[col] = val

    def __setitem__(self, key, value):
        if isinstance(key, int):
            key = self._column_list[key]

        super().__setitem__(key, value)

    def __getitem__(self, key):
        if isinstance(key, int):
            key = self._column_list[key]
        return super().__getitem__(key)


class DataContainer:
    def __init__(self):
        self._rows = []
        self._column_list = []
        self._column_defn = {}

    @property
    def rows(self):
        return self._rows

    @property
    def columns(self):
        return self._column_list

    def add_column(self, name, default_value=None):
        if name in self._column_defn:
            raise KeyError("Column already exists")
        self._column_list.append(name)
        self._column_defn[name] = default_value

    def new_row(self):
        row = DataRow(self._column_list, self._column_defn)
        self._rows.append(row)
        return row

    @property
    def rows(self):
        return self._rows


class Dataset(dict):
    def __init__(self, data={}):
        super(Dataset, self).__init__()
        self._data = {}

        if data:
            self.load_data(data)

    def add_table(self, name):
        if name in self:
            raise KeyError("Table is already exists")

        data = DataContainer()
        self._data[name] = data
        self[name] = data._rows
        return data

    def load_data(self, data, merge_dfn=True):
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, bytes):
            data = json.loads(data.decode('utf-8'))

        self.from_dict(data, merge_dfn)

    def from_dict(self, data, merge_dfn=True):
        for table_name, rows in data.items():
            if not merge_dfn and table_name not in self:
                raise KeyError(f"Table {table_name} is not exists")

            if not isinstance(rows, list):
                raise ValueError("Not a table")

            table = self[table_name] if table_name in self else self.add_table(table_name)

            if not rows:
                continue

            for col in rows[0]:
                table.add_column(col)
            for row in rows:
                new_row = table.new_row()
                for col_name, value in row.items():
                    new_row[col_name] = value

    def render_to_qtable_widget(self, table_name, table_widget, hidden_index=[]):
        table_widget.setRowCount(0)

        if table_name not in self._data:
            raise KeyError(f"Table {table_name} is not exists")

        data = self._data[table_name]
        if not data.rows:
            return

        columns = data.columns
        table_widget.setColumnCount(len(columns))
        table_widget.setHorizontalHeaderLabels(columns)

        for row in data.rows:
            pos = table_widget.rowCount()
            table_widget.insertRow(pos)

            for index, col in enumerate(columns):
                table_widget.setItem(
                    pos, index, QTableWidgetItem(str(row[col]))
                )

        for index in hidden_index:
            table_widget.setColumnHidden(index, True)
