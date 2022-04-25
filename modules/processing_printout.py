import sys
# from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.PyQt import QtWidgets
import qgis.PyQt.QtCore as QtCore
from qgis.PyQt.QtCore import pyqtSignal

from qgis.utils import iface

from qgis.core import (
    QgsProcessingFeedback
)


class MyFeedBack(QgsProcessingFeedback):
    """ Dedicated QgsFeedback for handling processing feedback"""

    closingPlugin = pyqtSignal()

    def __init__(self, parent=iface.mainWindow()):
        super(MyFeedBack, self).__init__()
        self.iface = iface
        self.setup_ui()
        self.cleanButton.clicked.connect(self.close_dialog)
    
    def setup_ui(self):
        self.dlg = QtWidgets.QDialog()
        self.dlg.resize(600, 450)
        self.dlg.setWindowTitle("Bersihkan Topology")
        self.dlg.setWindowModality(QtCore.Qt.NonModal)
        self.gridLayout = QtWidgets.QGridLayout(self.dlg)
        self.gridLayout.setObjectName("gridLayout")
        self.report = QtWidgets.QTextEdit(self.dlg)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.report.sizePolicy().hasHeightForWidth())
        self.report.setSizePolicy(sizePolicy)
        self.report.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.report.setReadOnly(True)
        self.report.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.report.setObjectName("report")
        self.gridLayout.addWidget(self.report, 0, 0, 1, 1)
        self.cleanButton = QtWidgets.QPushButton(self.dlg)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cleanButton.sizePolicy().hasHeightForWidth())
        self.cleanButton.setSizePolicy(sizePolicy)
        self.cleanButton.setMinimumSize(QtCore.QSize(0, 35))
        self.cleanButton.setObjectName("cleanButton")
        self.cleanButton.setText("OK")
        self.gridLayout.addWidget(self.cleanButton, 1, 0, 1, 1)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def close_dialog(self):
        self.dlg.close()

    def setProgressText(self, text):
        # print("Progres", text)
        self.report.append(text)

    def pushInfo(self, info):
        # print("info", info)
        self.report.append(info)

    def pushCommandInfo(self, info):
        # print("pushcommandinfo", info)
        self.dlg.show()
        self.report.append(info)

    def pushDebugInfo(self, info):
        # print("push debug", info)
        self.report.append(info)

    def pushConsoleInfo(self, info):
        # print("push console", info)
        self.report.append(info)

    def reportError(self, error, fatalError=False):
        # print("report error", error)
        self.report.append(error)

