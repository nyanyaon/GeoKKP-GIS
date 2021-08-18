# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoKKP
                                 A QGIS plugin
 This plugin ports GeoKKP for National Land Agency of Indonesia
                              -------------------
        begin                : 2021-05-24
        git sha              : $Format:%H$
        copyright            : (C) 2021 by GeoKKP Developer Team
        email                : danylaksono@ugm.ac.id
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import json

from qgis.PyQt.QtCore import (
    QSettings,
    QTranslator,
    QCoreApplication,
    Qt,
    QSize
)

from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.PyQt.QtWidgets import (
    QWidget,
    QAction,
    QMenu,
    QDockWidget,
    QToolButton,
    QMessageBox,
    QSizePolicy,
    QHBoxLayout,
    QLabel
)

from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapToolIdentify
from qgis import utils as qgis_utils

# Import the code for the DockWidget
from .geokkp_dockwidget import GeoKKPDockWidget

# Modules
from .modules.add_layer import AddLayerDialog
from .modules.gotoxy import GotoXYDialog
from .modules.plotcoord import PlotCoordinateDialog
from .modules.login import LoginDialog, get_saved_credentials
from .modules.openaerialmap import OAMDialog
from .modules.adjust import AdjustDialog
from .modules.postlogin import PostLoginDock
from .modules.import_from_file import ImportGeomFromFile
from .modules.coordinate_transform import CoordinateTransformDialog
from .modules.layout_peta import LayoutPetaDialog
from .modules.layout_gu import LayoutGUDialog
from .modules.utils import (
    activate_editing,
    iconPath,
    icon
)
from .modules.memo import app_state


class GeoKKP:
    """GeoKKP QGIS Plugin Basic Implementation"""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.project = QgsProject
        self.root = QgsProject.instance().layerTreeRoot()
        self.mapToolIdentify = QgsMapToolIdentify(self.canvas)

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize memo
        login_state = app_state.set('logged_in', False)
        login_state.changed.connect(self.login_changed)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeoKKP_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []

        # Add GeoKKP Toolbar
        self.toolbar = self.iface.addToolBar(u'GeoKKP')
        self.toolbar.setObjectName(u'GeoKKP')

        # Add GeoKKP Main Menu
        self.menu = self.iface.mainWindow().findChild(QMenu, 'GeoKKPGIS')
        if not self.menu:
            self.menu = QMenu(self.tr(u'&GeoKKP-GIS'), self.iface.mainWindow().menuBar())
            self.menu.setObjectName('GeoKKPGIS')
            actions = self.iface.mainWindow().menuBar().actions()
            lastAction = actions[-1]
            self.iface.mainWindow().menuBar().insertMenu(lastAction, self.menu)

        # Change QGIS Title and Default Icon to GeoKKP
        title = self.iface.mainWindow().windowTitle()
        new_title = title.replace('QGIS', 'GeoKKP-GIS')
        self.iface.mainWindow().setWindowTitle(new_title)
        self.iface.mainWindow().setWindowIcon(icon('icon.png'))

        self.pluginIsActive = False

        # self.canvasClicked = pyqtSignal('QgsPointXY')

        # Set widgets
        self.dockwidget = GeoKKPDockWidget()
        self.addlayeraction = AddLayerDialog()
        self.gotoxyaction = GotoXYDialog()
        self.plotxyaction = PlotCoordinateDialog()
        self.import_from_file_widget = ImportGeomFromFile(self)
        self.loginaction = LoginDialog()
        self.postloginaction = PostLoginDock()
        self.oamaction = OAMDialog()
        self.adjustaction = AdjustDialog()
        self.layoutpetaaction = LayoutPetaDialog()
        self.layoutguaction = LayoutGUDialog()
        self.coordinate_transform_dialog = CoordinateTransformDialog()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeoKKP', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None,
            need_auth=True):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """
        login_state = app_state.get('logged_in')
        enabled_flag = enabled_flag and (not need_auth or login_state.value)

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        '''
        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)
        '''
        if add_to_menu:
            self.menu.addAction(action)

        if need_auth:
            action.setData({'need_auth': True})

        self.actions.append(action)

        return action

    def initGui(self):
        """================== GeoKKP-GIS Main Interface =================="""
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # start the deck
        self.run

        # ========== Menu: Login Pengguna ==========
        self.add_action(
            iconPath("login.png"),
            text=self.tr(u'Login Pengguna'),
            callback=self.login_geokkp,
            parent=self.iface.mainWindow().menuBar(),
            need_auth=False)
        widget = QWidget()
        layout = QHBoxLayout()
        self.labelLoggedIn = QLabel()
        self.labelLoggedIn.setText("Masuk Pengguna")
        layout.addWidget(self.labelLoggedIn)
        widget.setLayout(layout)
        self.toolbar.addWidget(widget)
        # -------------------------------------------

        self.toolbar.addSeparator()
        self.menu.addSeparator()

        # ======== Menu: Buat Layer ========
        self.add_action(
            iconPath("buatlayer.png"),
            text=self.tr(u'Layer Baru'),
            callback=self.add_layers,
            need_auth=False,
            parent=self.iface.mainWindow().menuBar())
        # -------------------------------------------

        # ======== Dropdown Menu: Tambah Data ========
        # Deklarasi menu tambah data
        self.popupAddData = QMenu("&Tambah Data", self.iface.mainWindow())

        #  --- Sub-menu Unduh Data Persil ---
        self.actionAddData = self.add_action(
            icon("getparcel.png"),
            text=self.tr(u"Tambah Data"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            parent=self.popupAddData,
            add_to_menu=False
        )
        self.popupAddData.addAction(self.actionAddData)

        #  --- Sub-menu Import CSV ---
        self.actionImportCSV = self.add_action(
            icon("importcsv.png"),
            text=self.tr(u"Import CSV/TXT"),
            callback=self.import_file,
            add_to_toolbar=False,
            parent=self.popupAddData,
            add_to_menu=False
        )
        self.popupAddData.addAction(self.actionImportCSV)

        self.popupAddData.addSeparator()

        #  --- Sub-menu Tambah Basemap ---
        self.actionTambahBasemap = self.add_action(
            icon("basemap.png"),
            text=self.tr(u"Tambah Basemap"),
            callback=self.import_file,
            add_to_toolbar=False,
            parent=self.popupAddData,
            add_to_menu=False
        )
        self.popupAddData.addAction(self.actionTambahBasemap)

        #  --- Sub-menu Tambah OpenAerialMap ---
        self.actionTambahOAM = self.add_action(
            icon("openaerialmap.png"),
            text=self.tr(u"Tambah OpenAerialMap"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            parent=self.popupAddData,
            add_to_menu=False
        )
        self.popupAddData.addAction(self.actionTambahOAM)

        # Pengaturan Dropdown menu Tambah Data
        self.AddDataButton = QToolButton()
        self.AddDataButton.setMenu(self.popupAddData)
        self.AddDataButton.setIcon(icon("getparcel.png"))
        self.AddDataButton.setToolTip("Tambah Data")
        self.AddDataButton.setDefaultAction(self.actionAddData)
        self.AddDataButton.setPopupMode(QToolButton.MenuButtonPopup)
        # Register menu to toolbar
        self.toolbar.addWidget(self.AddDataButton)
        self.menu.addMenu(self.popupAddData)
        # -------------------------------------------

        # ======== Dropdown Menu: Penggambaran ========
        # Deklarasi menu penggambaran
        self.popupDraw = QMenu("&Penggambaran", self.iface.mainWindow())

        #  --- Sub-menu Gambar Manual ---
        self.actionManualDraw = self.add_action(
            icon("manualedit.png"),
            text=self.tr(u"Gambar Manual"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupDraw
        )
        self.popupDraw.addAction(self.actionManualDraw)

        #  --- Sub-menu Plot Koordinat ---
        self.actionPlotCoordinate = self.add_action(
            icon("plotcoordinate.png"),
            text=self.tr(u"Plot Koordinat"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupDraw
        )
        self.popupDraw.addAction(self.actionPlotCoordinate)

        #  --- Sub-menu Trilaterasi ---
        self.actionTrilateration = self.add_action(
            icon("trilateration.png"),
            text=self.tr(u"Gambar dengan Trilaterasi"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupDraw
        )
        self.popupDraw.addAction(self.actionTrilateration)

        #  --- Sub-menu Triangulasi ---
        self.actionTriangulation = self.add_action(
            icon("triangulation.png"),
            text=self.tr(u"Gambar dengan Triangulasi"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupDraw
        )
        self.popupDraw.addAction(self.actionTriangulation)

        # Pengaturan Dropdown menu Penggambaran
        self.DrawButton = QToolButton()
        self.DrawButton.setMenu(self.popupDraw)
        self.DrawButton.setIcon(icon("drawpoly.png"))
        self.DrawButton.setToolTip("Penggambaran")
        self.DrawButton.setDefaultAction(self.actionManualDraw)
        self.DrawButton.setPopupMode(QToolButton.MenuButtonPopup)
        # Register menu to toolbar
        self.toolbar.addWidget(self.DrawButton)
        self.menu.addMenu(self.popupDraw)
        # -------------------------------------------

        # ======== Dropdown Menu: Validasi ========
        # Deklarasi menu validasi
        self.popupValidasi = QMenu("&Validasi", self.iface.mainWindow())

        #  --- Sub-menu Cek Topologi ---
        self.actionCekTopologi = self.add_action(
            icon("validasi.png"),
            text=self.tr(u"Validasi"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupValidasi
        )
        self.popupValidasi.addAction(self.actionCekTopologi)

        #  --- Sub-menu Auto Adjust ---
        self.actionAutoAdjust = self.add_action(
            icon("autoadjust.png"),
            text=self.tr(u"Auto Adjust"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupValidasi
        )
        self.popupValidasi.addAction(self.actionAutoAdjust)

        # Pengaturan Dropdown menu Validasi
        self.ValidasiButton = QToolButton()
        self.ValidasiButton.setMenu(self.popupValidasi)
        self.ValidasiButton.setIcon(icon("validasi.png"))
        self.ValidasiButton.setToolTip("Validasi")
        self.ValidasiButton.setDefaultAction(self.actionCekTopologi)
        self.ValidasiButton.setPopupMode(QToolButton.MenuButtonPopup)
        # Register menu to toolbar
        self.toolbar.addWidget(self.ValidasiButton)
        self.menu.addMenu(self.popupValidasi)
        # -------------------------------------------

        # ======== Dropdown Menu: Pencetakan ========
        # Deklarasi menu Pencetakan
        self.popupPencetakan = QMenu("&Pencetakan", self.iface.mainWindow())

        #  --- Sub-menu Cetak Peta ---
        self.actionCetakPeta = self.add_action(
            icon("layout.png"),
            text=self.tr(u"Cetak Gambar Ukur"),
            callback=self.layout_gu,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupPencetakan
        )
        self.popupPencetakan.addAction(self.actionCetakPeta)

        #  --- Sub-menu Cetak SU ---
        self.actionCetakSU = self.add_action(
            icon("layout.png"),
            text=self.tr(u"Cetak Surat Ukur"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupPencetakan
        )
        self.popupPencetakan.addAction(self.actionCetakSU)

        #  --- Sub-menu Cetak PBT ---
        self.actionCetakPBT = self.add_action(
            icon("layout.png"),
            text=self.tr(u"Cetak Peta Bidang Tanah"),
            callback=self.layout_peta,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupPencetakan
        )
        self.popupPencetakan.addAction(self.actionCetakPBT)

        # Pengaturan Dropdown menu Pencetakan
        self.PencetakanButton = QToolButton()
        self.PencetakanButton.setMenu(self.popupPencetakan)
        self.PencetakanButton.setIcon(icon("layout.png"))
        self.PencetakanButton.setToolTip("Pencetakan")
        self.PencetakanButton.setDefaultAction(self.actionCetakPeta)
        self.PencetakanButton.setPopupMode(QToolButton.MenuButtonPopup)
        # Register menu to toolbar
        self.toolbar.addWidget(self.PencetakanButton)
        self.menu.addMenu(self.popupPencetakan)
        # -------------------------------------------

        # ======== Dropdown Menu: Peralatan ========
        # Deklarasi menu Pencetakan
        self.popupPeralatan = QMenu("&Peralatan", self.iface.mainWindow())

        #  --- Sub-menu Transformasi Koordinat ---
        self.actionTransformasiKoordinat = self.add_action(
            icon("conversion.png"),
            text=self.tr(u"Transformasi Koordinat"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            need_auth=False,
            parent=self.popupPeralatan
        )
        self.popupPeralatan.addAction(self.actionTransformasiKoordinat)

        #  --- Sub-menu Zoom to XY ---
        self.actionGotoXY = self.add_action(
            icon("zoomto.png"),
            text=self.tr(u"Zoom ke XY"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            need_auth=False,
            parent=self.popupPeralatan
        )
        self.popupPeralatan.addAction(self.actionGotoXY)

        #  --- Sub-menu Geocoding ---
        self.actionGeocoding = self.add_action(
            icon("georef.png"),
            text=self.tr(u"Geocoding"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupPeralatan
        )
        self.popupPeralatan.addAction(self.actionGeocoding)

        # Pengaturan Dropdown menu Peralatan
        self.PeralatanButton = QToolButton()
        self.PeralatanButton.setMenu(self.popupPeralatan)
        self.PeralatanButton.setIcon(icon("perangkat.png"))
        self.PeralatanButton.setToolTip("Perangkat")
        self.PeralatanButton.setDefaultAction(self.actionTransformasiKoordinat)
        self.PeralatanButton.setPopupMode(QToolButton.MenuButtonPopup)
        # Register menu to toolbar
        self.toolbar.addWidget(self.PeralatanButton)
        self.menu.addMenu(self.popupPeralatan)
        # -------------------------------------------

        # ========== Label Toolbar GeoKKP ==========
        self.judul_aplikasi()


        # ======== Dropdown Menu: Workspace GeoKKP ========
        # Deklarasi menu Workspace
        self.popupWorkspace = QMenu("&Workspace", self.iface.mainWindow())

        #  --- Sub-menu Workspace Rutin ---
        self.actionWorkspaceRutin = self.add_action(
            icon(""),
            text=self.tr(u"Workspace Rutin"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupWorkspace
        )
        self.popupWorkspace.addAction(self.actionWorkspaceRutin)

        #  --- Sub-menu Workspace Partisipatif ---
        self.actionWorkspacePartisipatif = self.add_action(
            icon(""),
            text=self.tr(u"Partisipatif"),
            callback=self.gotoxy,
            add_to_toolbar=False,
            add_to_menu=False,
            parent=self.popupWorkspace
        )
        self.popupWorkspace.addAction(self.actionWorkspacePartisipatif)


        # Pengaturan Dropdown menu Workspace
        self.WorkspaceButton = QToolButton()
        self.WorkspaceButton.setMenu(self.popupWorkspace)
        self.WorkspaceButton.setToolTip("Perangkat")
        self.WorkspaceButton.setDefaultAction(self.actionWorkspaceRutin)
        self.WorkspaceButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.WorkspaceButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        # Register menu to toolbar
        self.toolbar.addWidget(self.WorkspaceButton)
        self.menu.addMenu(self.popupWorkspace)
        # -------------------------------------------

        # ========== Menu: CADMode ==========
        self.add_action(
            iconPath("autoadjust.png"),
            text=self.tr(u'CAD Mode'),
            callback=self.toggle_cad_mode,
            parent=self.iface.mainWindow(),
            need_auth=False)
        # -------------------------------------------

        # ========== Menu: Pengaturan ==========
        self.add_action(
            iconPath("settings.png"),
            text=self.tr(u'Pengaturan'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow(),
            need_auth=False)
        # -------------------------------------------

        # ========== Menu: Bantuan ==========
        self.add_action(
            iconPath("help.png"),
            text=self.tr(u'Bantuan'),
            callback=self.openhelp,
            parent=self.iface.mainWindow(),
            need_auth=False)
        # -------------------------------------------

        # ============ Toolbar Events ============
        # self.loginaction.loginChanged.connect(self.login_changed)

    def judul_aplikasi(self):
        """
        Widget di tengah toolbar
        """
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QHBoxLayout()
        layout.addStretch()
        icon = QIcon(iconPath("icon.png"))
        labelIcon = QLabel()
        labelIcon.setPixmap(icon.pixmap(QSize(24, 24)))
        layout.addWidget(labelIcon)
        self.labelLoggedIn = QLabel()
        self.labelLoggedIn.setText("<b> Aplikasi GeoKKP-GIS ATR/BPN </b>")
        self.labelLoggedIn.setFont(QFont('Arial', 12))
        layout.addWidget(self.labelLoggedIn)
        layout.addStretch()
        widget.setLayout(layout)
        self.toolbar.addWidget(widget)

    def onClosePlugin(self):
        """
        Cleanup necessary items here when plugin dockwidget is closed
        """
        # disconnects
        # self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # self.dockwidget = None
        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GeoKKP-GIS'),
                action)
            self.iface.removeToolBarIcon(action)

        # remove the toolbar
        # del self.dockwidget
        # remove the toolbar
        if self.toolbar:
            del self.toolbar
        if self.dockwidget:
            self.dockwidget.deleteLater()

        # remove panels registry
        self.iface.mainWindow().removeDockWidget(self.dockwidget)
        self.dockwidget.setVisible(False)
        self.dockwidget.destroy()

        # remove menu
        if self.menu:
            # self.menu.clear()
            self.menu = None

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True
            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = GeoKKPDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            #print("run the plugin")

    def login_changed(self, state):
        # self._is_logged_in = readSetting("geokkp/isLoggedIn")
        # print("successfully logged in")
        # print(self._is_logged_in)
        for action in self.actions:
            action_data = action.data()
            if isinstance(action_data, dict) \
                    and 'need_auth' in action_data.keys() \
                    and action_data['need_auth']:
                action.setEnabled(state)
        if state:
            self.postlogin()

    def enable_button(self, loggedIn):
        # self.btnLogin.setVisible(not loggedIn)
        labelText = ("<b>Welcome to Planet</b>" if not loggedIn else "<b>Planet</b>")
        self.labelLoggedIn.setText(labelText)

    # ==============================================================
    # Definisi Fungsi GeoKKP-GIS
    # ==============================================================

    def gotoxy(self):
        if self.gotoxyaction is None:
            # Create the dockwidget (after translation) and keep reference
            self.gotoxyaction = GotoXYDialog()
        self.gotoxyaction.selectProj.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

        # connect to provide cleanup on closing of dockwidget
        # self.gotoxyaction.closingPlugin.connect(self.onClosePlugin)

        # show the dialog
        # self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.gotoxyaction.show()

    def coordinate_transform(self):
        if self.coordinate_transform_dialog is None:
            # Create the dockwidget (after translation) and keep reference
            self.coordinate_transform_dialog = CoordinateTransformDialog()

        # show the dialog
        self.coordinate_transform_dialog.show()

    def plotxy(self):
        if self.plotxyaction is None:
            # Create the dockwidget (after translation) and keep reference
            self.plotxyaction = PlotCoordinateDialog()
        self.plotxyaction.listCoordsProj.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

        # connect to provide cleanup on closing of dockwidget
        # self.gotoxyaction.closingPlugin.connect(self.onClosePlugin)

        # show the dialog
        # self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.plotxyaction.show()

    def postlogin(self):
        """
        what to do if user is logged in
        """
        if self.postloginaction is None:
            # Create the dockwidget (after translation) and keep reference
            self.postloginaction = PostLoginDock()

        # connect to provide cleanup on closing of dockwidget
        self.postloginaction.closingPlugin.connect(self.onClosePlugin)

        # show the dialog
        # self.iface.addDockWidget(Qt.RightDockWidgetArea, self.postloginaction)
        self.postloginaction.show()

    def layout_peta(self):
        if self.layoutpetaaction is None:
            # Create the dockwidget (after translation) and keep reference
            self.layoutpetaaction = LayoutPetaDialog()
        self.layoutpetaaction.show()

    def layout_gu(self):
        if self.layoutguaction is None:
            # Create the dockwidget (after translation) and keep reference
            self.layoutguaction = LayoutGUDialog()
        self.layoutguaction.show()


    def add_layers(self):
        if self.addlayeraction is None:
            self.addlayeraction = AddLayerDialog()
        self.addlayeraction.show()


    def toggle_cad_mode(self):
        if 'qad' in qgis_utils.active_plugins:
            for panel in self.iface.mainWindow().findChildren(QDockWidget):
                if panel.windowTitle() == 'QAD Text Window - 3.0.4':
                    panel.setVisible(not panel.isVisible())
                    return
        QMessageBox.warning(None, 'Plugin tidak ditemukan', 'Plugin QAD perlu diaktifkan lebih dahulu')

    def import_file(self):
        if self.import_from_file_widget is None:
            self.import_from_file_widget = ImportGeomFromFile()
        self.import_from_file_widget.show()

    def login_geokkp(self):
        if self.loginaction is None:
            self.loginaction = LoginDialog()
        self.loginaction.show()
        self.loginaction

    def loadoam(self):
        if self.oamaction is None:
            self.oamaction = OAMDialog()
        self.oamaction.show()

    def show_atribute(self):
        if self.layer.selectedFeatures():
            fitur = self.layer.selectedFeatures()
            self.iface.openFeatureForm(self.layer, fitur[0])
        #print("show")

        # self.mapToolIdentify.activate()

        # edit_by_identify(self.canvas, layer)
        # layer = self.iface.activeLayer()

    def edit_parcel_attribute(self):
        self.layer = self.iface.activeLayer()
        # print(is_layer_exist(self.project, 'Persil'))

        if self.actionAttribute.isChecked():
            #print("it is checked")
            self.layer.startEditing()
            self.iface.actionSelect().trigger()
            self.layer.selectionChanged.connect(self.show_atribute)
        else:
            #print("unchecked")
            self.layer.selectionChanged.disconnect(self.show_atribute)
            self.iface.mainWindow().findChild(QAction, 'mActionToggleEditing').trigger()
            #print("stop editing")

        # self.layer.startEditing()
        # f = self.layer.selectedFeatures()[0]

        # fid = feature.id()

        # print ("feature selected : " + str(fid))

    def start_editing(self):
        if self.actionDrawPoly.isChecked():
            #print("it is checked")
            layer = self.project.instance().mapLayersByName('Persil')[0]
            self.project.instance().setAvoidIntersectionsLayers([layer])
            activate_editing(layer)
        else:
            #print("unchecked")
            self.stop_editing()

    def stop_editing(self):
        self.iface.mainWindow().findChild(QAction, 'mActionToggleEditing').trigger()
        #print("stop editing")

    def sudut_jarak(self):
        #print("sudut jarak")
        for x in self.iface.advancedDigitizeToolBar().actions():
            #print(x.text())
            if x.text() == 'Enable advanced digitizing tools':
                x.trigger()
                #print(x)

    def auto_adjust(self):
        if self.adjustaction is None:
            self.adjustaction = AdjustDialog()
        self.adjustaction.show()

    def openhelp(self):
        # QDesktopServices.openUrl(QUrl('https://qgis-id.github.io/'))
        get_saved_credentials()

# TODO: Move to dockwidget
# Methods for GeoKKP Dock Widget

    def selectLocation(self):
        """ what to do when user clicks location selection """

        urlWithParams = "http://mt0.google.com/vt/lyrs%3Ds%26hl%3Den%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D"
        self.loadXYZ(urlWithParams, 'Google Basemap')
        # self.delIfLayerExist('Google Basemap')

        selectedLocation = json.dumps(self.dockwidget.loadLocation())
        # self.delIfLayerExist('Wilayah Kerja')

        wilkerLayer = self.iface.addVectorLayer(selectedLocation, '', 'ogr')
        wilkerLayer.setName('Wilayah Kerja')
        self.iface.actionZoomToLayer().trigger()
        wilkerLayer.renderer().symbol().setColor(QColor("transparent"))
        wilkerLayer.renderer().symbol().symbolLayer(0).setStrokeColor(QColor(255, 0, 0))
        wilkerLayer.renderer().symbol().symbolLayer(0).setStrokeWidth(1)
        wilkerLayer.triggerRepaint()
        # self.project.instance().addMapLayer(wilkerLayer)

    def loadXYZ(self, url, name):
        rasterLyr = QgsRasterLayer("type=xyz&zmin=0&zmax=21&url=" + url, name, "wms")
        self.project.instance().addMapLayer(rasterLyr)

    def delIfLayerExist(self, layername):
        for layer in QgsProject.instance().mapLayers().values():
            #print(layer.name(), " - ", layername)
            #print(layer.name() == layername)
            if (layer.name != layername):
                #print("layer exist. deleting..", layername)
                to_be_deleted = QgsProject.instance().mapLayersByName(layer.name())[0]
                self.root.removeLayer(to_be_deleted)
                # self.project.removeMapLayer(to_be_deleted.id())
            else:
                pass
                #print('existing not deleting,', layer.name())

    def addWMSParcel(self):
        wms_url = "url=https://103.123.13.78/geoserver/umum/wms&format=image/png&layers=PersilHak&styles=&crs=EPSG:4326"
        rasterLyr = QgsRasterLayer(wms_url, "Persil berdasarkan Hak", "wms")
        self.project.instance().addMapLayer(rasterLyr)
        self.iface.messageBar().pushMessage(
            "Sukses", "Berhasil menambahkan layer Persil", level=Qgis.Success, duration=4)
        # self.delIfLayerExist('Bidang Tanah')

    def set_symbology(self, layer, qml):
        uri = os.path.join(os.path.dirname(__file__), 'styles/'+qml)
        layer.loadNamedStyle(uri)

    def set_dimension_style(self):
        layer = self.project.instance().mapLayersByName('Persil')[0]
        if self.actionDimension.isChecked():
            self.set_symbology(layer, 'dimension.qml')
        else:
            self.set_symbology(layer, 'simplepersil.qml')

        layer.triggerRepaint()

        # uri = 'https://raw.githubusercontent.com/danylaksono/GeoKKP-GIS/main/styles/dimension.qml'
        # layer = self.iface.activeLayer()
        # print(layer.name())
        # layer.loadNamedStyle(uri)
        # layer.triggerRepaint()
        # for layer in self.project.instance().mapLayers().values():
        #    if (layer.name == "Bidang Tanah"):
