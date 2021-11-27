import csv
import os
import math

from qgis.PyQt import uic, QtGui #, QtCore
from qgis.PyQt.QtWidgets import QFileDialog, QDialog, QTableWidgetItem, QSizePolicy
from PyQt5.QtCore import Qt, QDir
from qgis.utils import iface

from qgis.core import Qgis, QgsPoint, QgsPointXY, QgsGeometry

from qgis.gui import QgsVertexMarker, QgsMessageBar, QgsRubberBand

from .maptools import MapTool

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/az_distance.ui'))

"""
dics = {
    'titik0' : {
        'nama' : 'P0',
        'X' : 000000,
        'Y' : 000000,
        'Z' : 000000,
        'x_terkoreksi' : 00000,
        'y_terkoreksi' : 00000,
        'z_terkoreksi' : 00000
        },
    'titik1' : {
        'nama' : 'P1',
        'jarak' : 123.12,
        'sudut' : 12 34 56.789,
        'tinggi' : 12.34,
        'X' : 000000,
        'Y' : 000000,
        'Z' : 000000,
        'x_terkoreksi' : 00000,
        'y_terkoreksi' : 00000,
        'z_terkoreksi' : 00000
    }
}

list_of_dicts = [
    {
        'nama' : 'P0',
        'X' : 000000,
        'Y' : 000000,
        'Z' : 000000,
        'x_terkoreksi' : 00000,
        'y_terkoreksi' : 00000,
        'z_terkoreksi' : 00000
    },
    {
        'nama' : 'P1',
        'jarak' : 123.12,
        'sudut' : 12 34 56.789,
        'tinggi' : 12.34,
        'x' : 000000,
        'y' : 000000,
        'z' : 000000,
        'x_terkoreksi' : 00000,
        'y_terkoreksi' : 00000,
        'z_terkoreksi' : 00000
    }
]
"""

class AzDistanceDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(AzDistanceDialog, self).__init__(parent)
        self.setupUi(self)

        self.label_last_point.setVisible(False)
        self.last_point.setVisible(False)

        self.initiate_first_row()

        self.dialog_bar = QgsMessageBar()
        self.dialog_bar.setSizePolicy(
            QSizePolicy.MinimumExpanding, 
            QSizePolicy.Fixed
            )
        self.layout().insertWidget(0, self.dialog_bar)
        self.tableWidget.cellChanged.connect(self.current_item_changed)

        self.list_vm = []
        self.vm_start = None
        self.coord_calculated = False
        # self.tableWidget.currentCellChanged.connect(self.current_cell_changed)

    def current_item_changed(self):
        current_column = self.tableWidget.currentColumn()
        # check az
        if current_column == 1 or current_column == 3:
            if self.tableWidget.currentItem().text() != '':
                try:
                    _ = float(self.tableWidget.currentItem().text())
                    self.dialog_bar.clearWidgets()
                except ValueError:
                    message = """Format angka tidak sesuai."""
                    self.dialog_bar.pushMessage(
                        "Warning", message, level=Qgis.Warning)
        elif current_column == 2:
            if self.tableWidget.currentItem().text() != '':
                az_str = str(self.tableWidget.currentItem().text())
                validated_az = self.validate_az(az_str)
    
    def on_btn_pilihKoord_pressed(self):
        self.vm_start = self.create_vertex_marker('CROSS')
        self.point_tool = MapTool(self.canvas, self.vm_start)
        self.iface.mapCanvas().setMapTool(self.point_tool)
        self.point_tool.map_clicked.connect(self.update_titik_awal)

    def update_titik_awal(self, x, y):
        self.x_titik_awal.setText(str(round(x,3)))
        self.y_titik_awal.setText(str(round(y,3)))
        # self.tableWidget.setItem(0, 4, QTableWidgetItem(str(round(x,3))))
        # self.tableWidget.setItem(0, 5, QTableWidgetItem(str(round(y,3))))
        self.iface.mapCanvas().unsetMapTool(self.point_tool)
        # self.iface.mapCanvas().scene().removeItem(self.vm_start)
        self.list_vm.append(self.vm_start)

    def on_btn_tambahTitik_pressed(self):
        current_row = self.tableWidget.rowCount()
        self.tableWidget.setRowCount(current_row + 1)
        for row in range(current_row, current_row+1):
            for col in range(7):
                self.tableWidget.setItem(row, col, QTableWidgetItem(''))
    
    # def disable_cell(self, cell_item):
        # cell_item.setFlags(Qt.ItemIsSelectable)
        # cell_item.setBackground(QtGui.QColor(128,128,128,180))

    def initiate_first_row(self):
        self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(4)
        for i in range(4):
            self.tableWidget.setItem(0, i, QTableWidgetItem(''))
            
        # disable 2nd to 4th cells
        # for i in range(1,5):
            # self.disable_cell(self.tableWidget.item(0,i))

    def on_btn_hapusTable_pressed(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.setRowCount(4)
        self.initiate_first_row()

    def on_btn_hapusTitik_pressed(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        for item in reversed(sorted(selected_rows)):
            self.tableWidget.removeRow(item.row())

    def on_btn_bowditch_pressed(self):
        pass

    def on_btn_hitungKoord_pressed(self):
        self.coord_calculated = True

        if self.radio_pTertutup.isChecked():
            self.polygon_terbuka = True
        else:
            self.polygon_terbuka = False

        self.tableWidget.setColumnCount(4)
        num = 0

        # existing column
        columns = []
        for i in range(self.tableWidget.columnCount()):
            columns.append(self.tableWidget.horizontalHeaderItem(i).text())

        list_titik = self.read_table()

        # set utk titik awal
        x = float(self.x_titik_awal.text())
        y = float(self.y_titik_awal.text())
        z = float(self.z_titik_awal.text())

        list_titik[0]['X'] = x
        list_titik[0]['Y'] = y
        list_titik[0]['Z'] = z

        # insert column
        add_columns = ['X', 'Y', 'Z', 'Delta X', 'Delta Y']
        new_columns = columns + add_columns
        self.tableWidget.setColumnCount(self.tableWidget.columnCount() + 5)
        self.tableWidget.setHorizontalHeaderLabels(new_columns)

        dx_idx = new_columns.index('Delta X')
        dy_idx = new_columns.index('Delta Y')
        # dz_idx = new_columns.index('Dz')
        x_idx = new_columns.index('X')
        y_idx = new_columns.index('Y')
        z_idx = new_columns.index('Z')

        for id,titik in enumerate(list_titik):
            dist = float(titik['Jarak'])
            az = self.validate_az(titik['Azimuth']) 
            dx = round(dist*math.sin(math.radians(az)),3)
            dy = round(dist*math.cos(math.radians(az)),3)
            dz = round(float(titik['Beda Tinggi']),3)
            # store in dictionary
            titik['Delta X'] = dx
            titik['Delta Y'] = dy
            
            self.tableWidget.setItem(id, dx_idx, QTableWidgetItem(str(dx)))
            self.tableWidget.setItem(id, dy_idx, QTableWidgetItem(str(dy)))

            if id > 0:
                prev_titik = list_titik[id-1]
                x = prev_titik['X'] + prev_titik['Delta X']
                y = prev_titik['Y'] + prev_titik['Delta Y']
                z = prev_titik['Z'] + dz
                titik['X'] = x
                titik['Y'] = y
                titik['Z'] = z
            
            self.tableWidget.setItem(id, x_idx, QTableWidgetItem(str(x)))
            self.tableWidget.setItem(id, y_idx, QTableWidgetItem(str(y)))
            self.tableWidget.setItem(id, z_idx, QTableWidgetItem(str(z)))

        # Last Point
        self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
        titik_akhir = {}
        if self.polygon_terbuka:
            prev_titik = list_titik[-1]
            dx = float(prev_titik['Delta X'])
            dy = float(prev_titik['Delta Y'])
            dz = float(prev_titik['Beda Tinggi'])
            titik_akhir['no_titik'] = prev_titik['no_titik'] + 1
            titik_akhir['Nama Titik'] = prev_titik['Nama Titik'] + "'"
            titik_akhir['X'] = prev_titik['X'] + dx
            titik_akhir['Y'] = prev_titik['Y'] + dy
            titik_akhir['Z'] = prev_titik['Z'] + dz
            list_titik.append(titik_akhir)
        last_row = self.tableWidget.rowCount()-1
        self.tableWidget.setItem(last_row, 0, QTableWidgetItem(titik_akhir['Nama Titik']))
        self.tableWidget.setItem(last_row, x_idx, QTableWidgetItem(str(titik_akhir['X'])))
        self.tableWidget.setItem(last_row, y_idx, QTableWidgetItem(str(titik_akhir['Y'])))
        self.tableWidget.setItem(last_row, z_idx, QTableWidgetItem(str(titik_akhir['Z'])))
        for col in [1,2,3,7,8]:
            self.tableWidget.setItem(last_row, col, QTableWidgetItem('-'))
        self.list_titik = list_titik

    def read_table(self):
        row_count = self.tableWidget.rowCount()
        col_count = self.tableWidget.columnCount()
        # existing column
        col_name = []
        for i in range(col_count):
            col_name.append(self.tableWidget.horizontalHeaderItem(i).text())

        list_titik_read = []
        for row in range(row_count):
            titik = {}
            titik['no_titik'] = row
            for col in range(col_count):
                print(f'Current row :{row} and col {col}')
                current_key = col_name[col]
                current_value = self.tableWidget.item(row,col).text()
                titik[current_key] = current_value
            list_titik_read.append(titik)
        return list_titik_read

    def on_btn_plotTitik_pressed(self):
        list_titik = self.read_table()
        for vm_titik in self.list_vm:
            self.iface.mapCanvas().scene().removeItem(vm_titik)

        for id_titik,titik in enumerate(list_titik):
            vm = self.create_vertex_marker('CIRCLE')
            xtitik = float(titik['X'])
            ytitik = float(titik['Y'])
            titik_point = QgsPointXY(xtitik, ytitik)
            if id_titik > 0:
                line_rb = self.create_rubberband(self.canvas, 'SOLID_LINE')
                prev_titik = list_titik[id_titik - 1]
                prev_titik_x = float(prev_titik['X'])
                prev_titik_y = float(prev_titik['Y'])
                prev_titik_pt = QgsPointXY(prev_titik_x, prev_titik_y)
                line_geom = QgsGeometry.fromPolylineXY([titik_point, prev_titik_pt])
                line_rb.setToGeometry(line_geom)
                self.list_vm.append(line_rb)

            vm.setCenter(titik_point)
            self.list_vm.append(vm)

        print(list_titik)
    
    def on_btn_resetHitung_pressed(self):
        self.tableWidget.setColumnCount(4)
        for vm_titik in self.list_vm:
            self.iface.mapCanvas().scene().removeItem(vm_titik)
        if self.coord_calculated:
            row_count = self.tableWidget.rowCount()
            self.tableWidget.setRowCount(row_count - 1)

    def on_btn_importTitik_pressed(self):
        input_csv, _ = QFileDialog.getOpenFileName(self, 'Browse CSV file', QDir.rootPath() , '*.csv')
        
        import_list = []

        with open(input_csv, mode='r') as infile:
            reader = csv.reader(infile)
            for row in reader:
                import_list.append(row)

        # df_titik = {} # to be removed
        list_titik_import = []
        titik_key = import_list[0]

        for id, row in enumerate(import_list):
            titik = {}
            for key_id,key in enumerate(titik_key):
                titik[key] = row[key_id]
            # df_titik[id] = titik
            list_titik_import.append(titik)
        # print(list_titik_import)
        self.table_from_list(list_titik_import)        

    def table_from_list(self, list_of_titik):
        self.initiate_first_row()
        column = [key for key,value in list_of_titik[0].items()][1:]
        row_count = len(list_of_titik[1:])
        col_count = len(column)

        self.tableWidget.setColumnCount(col_count)
        self.tableWidget.setHorizontalHeaderLabels(column)
        self.tableWidget.setRowCount(row_count)

        if 'X' in column:
            x = round(float(list_of_titik[1]['X']),3)
            y = round(float(list_of_titik[1]['Y']),3)
            z = round(float(list_of_titik[1]['Z']),3)

            self.x_titik_awal.setText(str(x))
            self.y_titik_awal.setText(str(y))
            self.z_titik_awal.setText(str(z))
        else:
            self.x_titik_awal.setText('')
            self.y_titik_awal.setText('')
            self.z_titik_awal.setText('')

        for row, titik in enumerate(list_of_titik[1:]):
            for key,value in titik.items():
                try:
                    col = column.index(key)
                    print(f'setting row {row} and col {col} with {value}')
                    self.tableWidget.setItem(row, col, QTableWidgetItem(value))
                except ValueError:
                    print(f'{key} is not in the list of column')

    def on_btn_exportTitik_pressed(self):
        list_titik = self.read_table()

        csv_columns = [key for key,value in list_titik[0].items()]
        csv_file, _ = QFileDialog.getSaveFileName(self, 'Save File', QDir.rootPath() , '*.csv')

        try:
            with open(csv_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                # for key,value in self.df_titik.items():
                    # writer.writerow(value)
                for titik in list_titik:
                    writer.writerow(titik)
        except IOError:
            print("I/O Error occured")

    def validate_az(self, az_str):
        message = """
                        Format tidak dikenali. Gunakan spasi sebagai pemisah. 
                        ('DD.dd' atau 'D M S.ss')
                        """
        if not az_str:
            return False
        az_split = az_str.strip().split(' ')

        if len(az_split) == 3:
            self.dialog_bar.clearWidgets()
            try:
                d = float(az_split[0])
                m = float(az_split[1])
                s = float(az_split[2])
            except ValueError:
                self.dialog_bar.pushMessage(
                    "Warning", message, level=Qgis.Warning)
                return False
            return d + (m/60) + (s/3600)
        
        elif len(az_split) == 1:
            self.dialog_bar.clearWidgets()
            try:
                return float(az_str)
            except ValueError:
                self.dialog_bar.pushMessage(
                    "Warning", message, level=Qgis.Warning)
                return False
        else:
            self.dialog_bar.pushMessage("Warning", message, level=Qgis.Warning)
            return False

    def create_vertex_marker(self, type='BOX'):
        vm = QgsVertexMarker(self.canvas)

        if type == 'BOX':
            icon_type = QgsVertexMarker.ICON_BOX
        elif type == 'CIRCLE':
            icon_type = QgsVertexMarker.ICON_CIRCLE
        elif type == 'CROSS':
            icon_type = QgsVertexMarker.ICON_CROSS
        else:
            icon_type = QgsVertexMarker.ICON_X

        vm.setIconType(icon_type)
        vm.setPenWidth(3)
        vm.setIconSize(7)
        return vm
    
    def create_rubberband(self, canvas, line_style = 'SOLID_LINE'):
        rb = QgsRubberBand(canvas, False)
        rb.setStrokeColor(QtGui.QColor(255, 0, 0, 255)) # red
        rb.setFillColor(QtGui.QColor(0, 0, 0, 0))
        rb.setWidth(1)
        if line_style == 'DASH_LINE':
            rb.setLineStyle(Qt.DashLine)
        elif line_style == 'SOLID_LINE':
            rb.setLineStyle(Qt.SolidLine)
        elif line_style == 'DOT_LINE':
            rb.setLineStyle(Qt.DotLine)
        return rb
