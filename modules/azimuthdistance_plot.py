import csv
import os
import math

from qgis.PyQt import uic, QtGui #, QtCore
from qgis.PyQt.QtWidgets import QFileDialog, QDialog, QTableWidgetItem, QSizePolicy
from PyQt5.QtCore import Qt, QDir
from qgis.utils import iface

from qgis.core import Qgis

from qgis.gui import QgsVertexMarker, QgsMessageBar

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
        'x' : 000000,
        'y' : 000000,
        'z' : 000000,
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

        self.initiate_first_row()

        self.dialog_bar = QgsMessageBar()
        self.dialog_bar.setSizePolicy(
            QSizePolicy.MinimumExpanding, 
            QSizePolicy.Fixed
            )
        self.layout().insertWidget(0, self.dialog_bar)
        self.tableWidget.cellChanged.connect(self.current_item_changed)
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
        self.vm_start = self.create_vertex_marker()
        self.point_tool = MapTool(self.canvas, self.vm_start)
        self.iface.mapCanvas().setMapTool(self.point_tool)
        self.point_tool.map_clicked.connect(self.update_titik_awal)

    def update_titik_awal(self, x, y):
        self.x_titik_awal.setText(str(round(x,3)))
        self.y_titik_awal.setText(str(round(y,3)))
        # self.tableWidget.setItem(0, 4, QTableWidgetItem(str(round(x,3))))
        # self.tableWidget.setItem(0, 5, QTableWidgetItem(str(round(y,3))))
        self.iface.mapCanvas().unsetMapTool(self.point_tool)
        self.iface.mapCanvas().scene().removeItem(self.vm_start)

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
        self.tableWidget.setColumnCount(4)
        list_titik = []
        df_titik = {}
        num = 0

        # existing column
        columns = []
        for i in range(self.tableWidget.columnCount()):
            columns.append(self.tableWidget.horizontalHeaderItem(i).text())

        for row in range(self.tableWidget.rowCount()):
            titik = {}
            titik['no_titik'] = num
            titik['nama_titik'] = self.tableWidget.item(row,0).text()
            titik['jarak'] = float(self.tableWidget.item(row,1).text())
            try:
                az = float(self.tableWidget.item(row,2).text())
            except ValueError:
                az = self.validate_az(self.tableWidget.item(row,2).text())
            titik['azimuth'] = az
            titik['Delta Z'] = float(self.tableWidget.item(row,3).text())

            df_titik[num] = titik       #  to be removed
            num += 1                    #  to be removed

            list_titik.append(titik)
            
        # set utk titik awal
        x = float(self.x_titik_awal.text())
        y = float(self.y_titik_awal.text())
        z = float(self.z_titik_awal.text())
        df_titik[0]['x'] = x #  to be removed
        df_titik[0]['y'] = y #  to be removed
        df_titik[0]['z'] = z #  to be removed
        
        list_titik[0]['x'] = x
        list_titik[0]['x'] = y
        list_titik[0]['x'] = z

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

        for key,value in df_titik.items():
            dist = df_titik[key]['jarak']
            az = df_titik[key]['azimuth'] 
            dx = round(dist*math.sin(math.radians(az)),3)
            dy = round(dist*math.cos(math.radians(az)),3)
            dz = round(df_titik[key]['Delta Z'],3)
            # store in dictionary
            df_titik[key]['Delta X'] = dx
            df_titik[key]['Delta Y'] = dy
            
            self.tableWidget.setItem(key, dx_idx, QTableWidgetItem(str(dx)))
            self.tableWidget.setItem(key, dy_idx, QTableWidgetItem(str(dy)))

            if key > 0:
                x = df_titik[key-1]['x'] + df_titik[key-1]['Delta X']
                y = df_titik[key-1]['y'] + df_titik[key-1]['Delta Y']
                z = df_titik[key-1]['z'] + df_titik[key-1]['Delta Z']
                df_titik[key]['x'] = x
                df_titik[key]['y'] = y
                df_titik[key]['z'] = z
            
            self.tableWidget.setItem(key, x_idx, QTableWidgetItem(str(x)))
            self.tableWidget.setItem(key, y_idx, QTableWidgetItem(str(y)))
            self.tableWidget.setItem(key, z_idx, QTableWidgetItem(str(z)))
        
        self.df_titik = df_titik

    def on_btn_plotTitik_pressed(self):
        print(self.df_titik)
        pass

    def on_btn_importTitik_pressed(self):
        input_csv, _ = QFileDialog.getOpenFileName(self, 'Browse CSV file', QDir.rootPath() , '*.csv')
        
        import_list = []

        with open(input_csv, mode='r') as infile:
            reader = csv.reader(infile)
            for row in reader:
                import_list.append(row)

        df_titik = {}
        df_titik_key = import_list[0]

        for id, row in enumerate(import_list[1:]):
            titik = {}
            for key_id,key in enumerate(df_titik_key):
                titik[key] = row[key_id]
            df_titik[id] = titik
        

    def table_from_list(self, list_of_titik):
        self.initiate_first_row()

        row_count = len(list_of_titik)
        col_count = len(list_of_titik[0])
        
        self.tableWidget.setItem(row, col, QTableWidgetItem(''))



    def on_btn_exportTitik_pressed(self):
        csv_columns = list(self.df_titik[0].keys())
        csv_file, _ = QFileDialog.getSaveFileName(self, 'Save File', QDir.rootPath() , '*.csv')

        try:
            with open(csv_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for key,value in self.df_titik.items():
                    writer.writerow(value)
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