import os

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from qgis.core import (
    QgsProject,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
)

from qgis.gui import QgsVertexMarker

# using utils
from .utils import (
    draw_rect_bound,
    icon,
    get_nlp,
    bk_10000,
    bk_2500,
    bk_1000,
    bk_500,
    bk_250,
    dialogBox,
)
from .maptools import MapTool

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/gambar_nlp.ui")
)

# constants
skala = ["1:10000", "1:2500", "1:1000", "1:500", "1:250"]

# constants for NLP
x_origin = 32000
y_origin = 282000
grid_10rb = 6000
grid_2500 = 1500
grid_1000 = 500
grid_500 = 250
grid_250 = 125


class DrawNLPDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for NLP Dialog"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        super(DrawNLPDialog, self).__init__(parent)
        self.setupUi(self)
        self.project = QgsProject()
        self.setWindowIcon(icon("icon.png"))

        copy_icon = QIcon(":/images/themes/default/mActionEditCopy.svg")
        
        self.project.instance().crsChanged.connect(self.set_epsg)

        # Clipboard
        self.clipboard = QApplication.clipboard()

        self.ambil_titik.checked = False
        self.point = None

        # setup map tool
        self.previousMapTool = self.canvas.mapTool()
        self.epsg = self.project.instance().crs().authid()
        self.crs_tm3.setText(self.project.instance().crs().description())

        # copy to clipboard
        self.copyTeksNLP.setIcon(copy_icon)
        self.copyTeksNLP.clicked.connect(self.copy_clicked)

        # self.skala_peta.currentIndexChanged.connect(self.get_nlp_text())
        self.ambil_titik.clicked.connect(self.on_pressed)

        self.skala_peta.addItems(skala)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        self.iface.actionPan().trigger()
        MapTool(self.canvas, self.vm).clear_drawing()
        event.accept()
    
    def copy_clicked(self, button_index):
        text = self.nlp.text()
        self.clipboard.setText(text)
        self.iface.statusBarIface().showMessage(
            "Nomor lembar peta berhasil disalin", 3000
        )

    def createMapTool(self):
        self.canvas.setMapTool(self.myMapTool)

    def deactivateMapTool(self):
        self.point_tool.isEmittingPoint = False
        self.point_tool.deleteLater()
        self.canvas.scene().removeItem(self.vm)
        self.canvas.setMapTool(self.previousMapTool)

    def set_epsg(self):
        self.epsg = self.project.instance().crs().authid()
        self.crs_tm3.setText(self.project.instance().crs().description())
        # print("changing epsg now into", self.epsg)

    def on_pressed(self):
        self.check_is_tm3()
        self.ambil_titik.checked = True
        try:
            self.canvas.scene().removeItem(self.vm)
            self.canvas.scene().removeItem(self.rb)
            MapTool(self.canvas, self.vm).clear_drawing()
        except:  # noqa
            pass
        self.vm = self.create_vertex_marker()
        self.point_tool = MapTool(self.canvas, self.vm)

        self.point_tool.map_clicked.connect(self.update_titik)

        self.point_tool.isEmittingPoint = True
        self.canvas.setMapTool(self.point_tool)

    def check_is_tm3(self):
        if int(self.epsg.split(":")[1]) in range(23830, 23846):
            return True
            print("EPSG Tercatat", self.epsg.split(":")[1])
        else:
            dialogBox("Anda belum mengatur sistem proyeksi TM-3 Project")
            print("EPSG Tercatat", self.epsg.split(":")[1])
            self.ambil_titik.checked = False
            return False

    def update_titik(self, x, y):
        self.ambil_titik.setChecked(False)
        self.point = QgsPointXY(x, y)

        # check point bounds against TM-3 Boundary
        source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        crs = QgsCoordinateReferenceSystem(self.epsg)
        transform = QgsCoordinateTransform(source_crs, crs, QgsProject.instance())
        crs_box = transform.transformBoundingBox(crs.bounds())
        if not crs_box.contains(self.point):
            dialogBox("Anda memilih titik di luar zona TM-3 Project")
        else:
            self.koordinat.setText(str(round(x, 3)) + "," + str(round(y, 3)))
            self.canvas.unsetMapTool(self.point_tool)
            self.deactivateMapTool()
            self.get_nlp_text()

    def create_vertex_marker(self, type="CROSS"):
        vm = QgsVertexMarker(self.canvas)

        if type == "BOX":
            icon_type = QgsVertexMarker.ICON_BOX
        elif type == "CIRCLE":
            icon_type = QgsVertexMarker.ICON_CIRCLE
        elif type == "CROSS":
            icon_type = QgsVertexMarker.ICON_CROSS
        else:
            icon_type = QgsVertexMarker.ICON_X

        vm.setIconType(icon_type)
        vm.setPenWidth(3)
        vm.setIconSize(7)
        return vm

    def get_nlp_text(self):
        skala_now = self.skala_peta.currentText()
        if self.point is not None:
            x, y = self.point
            self.nlp.setText(get_nlp(skala_now[2:], x, y))
        if self.checkBoxNLP.isChecked():
            self.draw_nlp()

    def draw_nlp(self):
        xMin = xMax = yMin = yMax = None
        skala_now = self.skala_peta.currentText()
        if self.point is not None:
            x, y = self.point

        def rect10rb():
            k_10rb, b_10rb = bk_10000(x, y)
            xMin = x_origin + (k_10rb - 1) * grid_10rb
            yMin = y_origin + (b_10rb - 1) * grid_10rb
            xMax = x_origin + (k_10rb) * grid_10rb
            yMax = y_origin + (b_10rb) * grid_10rb
            return [xMin, yMin, xMax, yMax]

        def rect2500():
            k_2500, b_2500 = bk_2500(x, y)
            ori_10rb_x, ori_10rb_y, p, q = rect10rb()
            xMin = ori_10rb_x + (k_2500 - 1) * grid_2500
            yMin = ori_10rb_y + (b_2500 - 1) * grid_2500
            xMax = ori_10rb_x + (k_2500) * grid_2500
            yMax = ori_10rb_y + (b_2500) * grid_2500
            return [xMin, yMin, xMax, yMax]

        def rect1000():
            k_1000, b_1000 = bk_1000(x, y)
            ori_2500_x, ori_2500_y, p, q = rect2500()
            xMin = ori_2500_x + (k_1000 - 1) * grid_1000
            yMin = ori_2500_y + (b_1000 - 1) * grid_1000
            xMax = ori_2500_x + (k_1000) * grid_1000
            yMax = ori_2500_y + (b_1000) * grid_1000
            return [xMin, yMin, xMax, yMax]

        def rect500():
            k_500, b_500 = bk_500(x, y)
            ori_1000_x, ori_1000_y, p, q = rect1000()
            xMin = ori_1000_x + (k_500 - 1) * grid_500
            yMin = ori_1000_y + (b_500 - 1) * grid_500
            xMax = ori_1000_x + (k_500) * grid_500
            yMax = ori_1000_y + (b_500) * grid_500
            return [xMin, yMin, xMax, yMax]

        def rect250():
            k_250, b_250 = bk_250(x, y)
            ori_500_x, ori_500_y, p, q = rect500()
            xMin = ori_500_x + (k_250 - 1) * grid_250
            yMin = ori_500_y + (b_250 - 1) * grid_250
            xMax = ori_500_x + (k_250) * grid_250
            yMax = ori_500_y + (b_250) * grid_250
            return [xMin, yMin, xMax, yMax]

        if skala_now == skala[0]:
            xMin, yMin, xMax, yMax = rect10rb()
        elif skala_now == skala[1]:
            xMin, yMin, xMax, yMax = rect2500()
        elif skala_now == skala[2]:
            xMin, yMin, xMax, yMax = rect1000()
        elif skala_now == skala[3]:
            xMin, yMin, xMax, yMax = rect500()
        elif skala_now == skala[4]:
            xMin, yMin, xMax, yMax = rect250()

        if xMin is not None:
            draw_rect_bound(xMin, yMin, xMax, yMax, self.epsg)
