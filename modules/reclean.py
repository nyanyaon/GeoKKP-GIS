import os

import processing
from processing.core.Processing import Processing


from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QTreeWidgetItem
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QVariant
from qgis.utils import iface
from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsProcessingFeedback
)

from .processing_printout import MyFeedBack

from .utils import (
    dialogBox,
    set_symbology,
    logMessage,
    add_layer,
    icon
)


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/topology.ui")
)

Processing.initialize()


class CleanTopologyDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog for Reclean Topology"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        self.iface = iface
        self.project = QgsProject()
        self.canvas = iface.mapCanvas()
        super(CleanTopologyDialog, self).__init__(parent)
        self.setWindowIcon(icon("icon.png"))
        self._currentcrs = None
        self.setupUi(self)

        self.feed = MyFeedBack()
        self.cleanButton.clicked.connect(self.clean_topology)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def clean_topology(self):
        layer = self.iface.activeLayer()
        if layer is None:
            dialogBox("Pilih salah satu layer vektor pada daftar")
            pass
        if not layer.type() == 0:
            dialogBox("Layer aktif bukan vektor")
            pass

        basename = layer.name()
        # basecrs = layer.crs().authid()

        # TODO: make all this parameterized
        parameters = {
            'input': layer,
            'type': [0, 1, 2, 3, 4, 5, 6],
            'tool': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'threshold': [
                        5,   # 0-break
                        5,   # 1-snap
                        5,   # 2-rmdangle
                        0,   # 3-chdangle
                        0,   # 4-rmbridge
                        0,   # 5-chbridge
                        0,   # 6-rmdupl
                        0,   # 7-rmdac
                        0,   # 8-bpol
                        5,   # 9-prune
                        10,  # 10-rmarea
                        0,   # 11-rmline
                        0    # 12- rmsa
                        ],
            '-b': False,
            '-c': True,
            'GRASS_SNAP_TOLERANCE_PARAMETER': 1,
            'GRASS_REGION_PARAMETER': "%f, %f, %f, %f" % (
                layer.extent().xMinimum(),
                layer.extent().xMaximum(),
                layer.extent().yMinimum(),
                layer.extent().yMaximum()),
            'GRASS_MIN_AREA_PARAMETER': 0.0001,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,
            'output': 'TEMPORARY_OUTPUT',
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'error': 'TEMPORARY_OUTPUT'
            }

        result = processing.run(
                "grass7:v.clean",
                parameters, feedback=self.feed)
        try:
            cleaned_layer = QgsVectorLayer(result['output'], basename, "ogr")
            set_symbology(cleaned_layer, "persil_cleaned.qml")
            self.project.instance().addMapLayer(cleaned_layer)
        except Exception as e:
            print(e)


