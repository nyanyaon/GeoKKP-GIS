# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoKKP
                                 A QGIS plugin
 This plugin ports GeoKKP for National Land Agency of Indonesia
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-12-24
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Dany Laksono
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

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QUrl
from qgis.PyQt.QtGui import QIcon, QColor, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton
from qgis.core import Qgis, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapToolIdentify





# Import the code for the DockWidget
import os
import json
from .geokkp_dockwidget import GeoKKPDockWidget

# Modules
from .modules.gotoxy import GotoXYDialog
from .modules.plotcoord import PlotCoordinateDialog
from .modules.login import LoginDialog
from .modules.openaerialmap import OAMDialog
from .modules.adjust import AdjustDialog

from .modules.utils import activate_editing, is_layer_exist, iconPath, icon


class GeoKKP:
    """QGIS Plugin Implementation."""

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

        # self.menu = self.tr(u'&GeoKKP-GIS')

        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeoKKP')
        self.toolbar.setObjectName(u'GeoKKP')

        # change title, for fun
        title = self.iface.mainWindow().windowTitle()
        new_title = title.replace('QGIS', 'GeoKKP-GIS')
        self.iface.mainWindow().setWindowTitle(new_title)

        self.pluginIsActive = False

        # self.canvasClicked = pyqtSignal('QgsPointXY')

        # self.dockwidget = None
        self.dockwidget = GeoKKPDockWidget()
        self.gotoxyaction = GotoXYDialog()
        self.plotxyaction = PlotCoordinateDialog()
        self.loginaction = LoginDialog()
        self.oamaction = OAMDialog()
        self.adjustaction = AdjustDialog()

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
            parent=None):
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

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.menu = self.iface.mainWindow().findChild(QMenu, 'GeoKKPGIS')
        if not self.menu:
            self.menu = QMenu(self.tr(u'&GeoKKP-GIS'), self.iface.mainWindow().menuBar())
            self.menu.setObjectName('GeoKKPGIS')
            actions = self.iface.mainWindow().menuBar().actions()
            lastAction = actions[-1]
            self.iface.mainWindow().menuBar().insertMenu(lastAction, self.menu)

        # Add Interface: Docked Main Panel GeoKKP
        self.iface.mainWindow().setWindowIcon(icon('icon.png'))

        self.add_action(
            iconPath("icon.png"),
            text=self.tr(u'Panel GeoKKP'),
            callback=self.run,
            parent=self.iface.mainWindow().menuBar())

        # Add Interface: Login Dialog
        self.add_action(
            iconPath("login.png"),
            text=self.tr(u'Login Pengguna'),
            callback=self.loginGeoKKP,
            parent=self.iface.mainWindow().menuBar())

        # Add Interface: Download Parcel GeoKKP Database Dialog
        self.add_action(
            iconPath("getparcel.png"),
            text=self.tr(u'Unduh Persil'),
            callback=self.addWMSParcel,
            parent=self.iface.mainWindow().menuBar())

        self.toolbar.addSeparator()
        self.menu.addSeparator()

        # QMenu here
        self.actionDrawPoly = QAction(
            icon("manualedit.png"),
            u"Editing Manual Persil",
            self.iface.mainWindow())
        self.actionPlotCoordinate = QAction(
            icon("plotcoordinate.png"),
            u"Plot Koordinat",
            self.iface.mainWindow())
        self.actionImportCSV = QAction(
            icon("importcsv.png"),
            u"Import CSV",
            self.iface.mainWindow())
        self.actionAzimuth = QAction(
            icon("azimuth.png"),
            u"Sudut dan Jarak",
            self.iface.mainWindow())
        self.actionTrilateration = QAction(
            icon("trilateration.png"),
            u"Gambar dengan Trilaterasi",
            self.iface.mainWindow())
        self.actionTriangulation = QAction(
            icon("triangulation.png"),
            u"Gambar dengan Triangulasi",
            self.iface.mainWindow())

        self.popupDrawMenu = QMenu("&Gambar Persil", self.iface.mainWindow())
        self.popupDrawMenu.setIcon(icon("manualedit.png"))

        self.popupDrawMenu.addAction(self.actionDrawPoly)
        self.popupDrawMenu.addAction(self.actionPlotCoordinate)
        self.popupDrawMenu.addAction(self.actionImportCSV)

        self.popupDrawMenu.addSeparator()

        self.popupDrawMenu.addAction(self.actionAzimuth)
        self.popupDrawMenu.addAction(self.actionTrilateration)
        self.popupDrawMenu.addAction(self.actionTriangulation)

        self.actionDrawPoly.setCheckable(True)
        self.actionDrawPoly.triggered.connect(self.start_editing)
        self.actionPlotCoordinate.triggered.connect(self.plotxy)
        self.actionImportCSV.triggered.connect(self.plotxy)
        self.actionAzimuth.triggered.connect(self.sudut_jarak)
        self.actionTrilateration.triggered.connect(self.gotoxy)
        self.actionTriangulation.triggered.connect(self.gotoxy)

        self.toolButton = QToolButton()

        self.toolButton.setMenu(self.popupDrawMenu)
        self.toolButton.setDefaultAction(self.actionDrawPoly)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        # self.toolButton.triggered.connect(self.gotoxy)

        self.toolbar.addWidget(self.toolButton)
        self.menu.addMenu(self.popupDrawMenu)

        # stop here

        '''
        # Add Interface: Draw Polygon
        icon_path = ':/plugins/geokkp/images/drawpoly.png'
        self.add_action(icon_path, text=self.tr(u'Gambar Bidang Tanah'),
            callback=self.plotxy, parent=self.iface.mainWindow())

        # Add Interface: Trilateration
        icon_path = ':/plugins/geokkp/images/trilateration.png'
        self.add_action(icon_path, text=self.tr(u'Gambar dengan Trilaterasi'),
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: Distance and Azimuth
        icon_path = ':/plugins/geokkp/images/azimuth.png'
        self.add_action(icon_path, text=self.tr(u'Gambar dengan Sudut dan Jarak'),
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: Triangulation
        icon_path = ':/plugins/geokkp/images/triangulation.png'
        self.add_action(icon_path, text=self.tr(u'Gambar dengan Triangulasi'),
            callback=self.gotoxy, parent=self.iface.mainWindow())

        '''

        # Qmenu End Here

        # Add Interface: Edit Atribut
        self.actionAttribute = QAction(
            icon("editattribute.png"),
            u"Edit Atribut Persil",
            self.iface.mainWindow())
        self.toolbar.addAction(self.actionAttribute)
        self.menu.addAction(self.actionAttribute)
        self.actionAttribute.setCheckable(True)

        self.actionAttribute.triggered.connect(self.edit_parcel_attribute)

        # Add Interface: Auto Adjust
        self.add_action(
            iconPath("autoadjust.png"),
            text=self.tr(u'Auto-Adjust'),
            callback=self.auto_adjust,
            parent=self.iface.mainWindow())

        # Add Interface: Parcel Dimension
        self.actionDimension = QAction(
            icon("dimension.png"),
            u"Gambar Dimensi",
            self.iface.mainWindow())
        self.toolbar.addAction(self.actionDimension)
        self.menu.addAction(self.actionDimension)
        self.actionDimension.setCheckable(True)

        self.actionDimension.triggered.connect(self.set_dimension_style)

        self.toolbar.addSeparator()
        self.menu.addSeparator()

        # Add Interface: Topology
        self.add_action(
            iconPath("topology.png"),
            text=self.tr(u'Cek Topologi'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        # Add Interface: Layout
        self.add_action(
            iconPath("layout.png"),
            text=self.tr(u'Layout Peta'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        self.toolbar.addSeparator()
        self.menu.addSeparator()

        # Add Interface: Coordinate Transformation
        self.add_action(
            iconPath("conversion.png"),
            text=self.tr(u'Transformasi Koordinat'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        # Add Interface: Zoom To
        self.add_action(
            iconPath("zoomto.png"),
            text=self.tr(u'Zoom Ke XY'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        # Add Interface: Georeference
        self.add_action(
            iconPath("georef.png"),
            text=self.tr(u'Georeferencing'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        # Add Interface: Change Basemap
        self.add_action(
            iconPath("basemap.png"),
            text=self.tr(u'Ganti Basemap'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        # Add Interface: OAM
        self.add_action(
            iconPath("openaerialmap.png"),
            text=self.tr(u'OpenAerialMap'),
            callback=self.loadoam,
            parent=self.iface.mainWindow())

        self.toolbar.addSeparator()
        self.menu.addSeparator()

        # Add Interface: Settings
        self.add_action(
            iconPath("settings.png"),
            text=self.tr(u'Pengaturan'),
            callback=self.gotoxy,
            parent=self.iface.mainWindow())

        # Add Interface: Help
        self.add_action(
            iconPath("help.png"),
            text=self.tr(u'Bantuan'),
            callback=self.openhelp,
            parent=self.iface.mainWindow())

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING GeoKKP"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD GeoKKP"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GeoKKP-GIS'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING GeoKKP"

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

            # detect actions
            self.dockwidget.buttonSelectLocation.clicked.connect(self.selectLocation)

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

    def loginGeoKKP(self):
        if self.loginaction is None:
            self.loginaction = LoginDialog()
        self.loginaction.show()

    def loadoam(self):
        if self.oamaction is None:
            self.oamaction = OAMDialog()
        self.oamaction.show()

    def show_atribute(self):
        if self.layer.selectedFeatures():
            fitur = self.layer.selectedFeatures()
            self.iface.openFeatureForm(self.layer, fitur[0])
        print("show")

        # self.mapToolIdentify.activate()

        # edit_by_identify(self.canvas, layer)
        # layer = self.iface.activeLayer()

    def edit_parcel_attribute(self):
        self.layer = self.iface.activeLayer()
        print(is_layer_exist(self.project, 'Persil'))

        if self.actionAttribute.isChecked():
            print("it is checked")
            self.layer.startEditing()
            self.iface.actionSelect().trigger()
            self.layer.selectionChanged.connect(self.show_atribute)
        else:
            print("unchecked")
            self.layer.selectionChanged.disconnect(self.show_atribute)
            self.iface.mainWindow().findChild(QAction, 'mActionToggleEditing').trigger()
            print("stop editing")

        # self.layer.startEditing()
        # f = self.layer.selectedFeatures()[0]

        # fid = feature.id()

        # print ("feature selected : " + str(fid))

    def start_editing(self):
        if self.actionDrawPoly.isChecked():
            print("it is checked")
            layer = self.project.instance().mapLayersByName('Persil')[0]
            self.project.instance().setAvoidIntersectionsLayers([layer])
            activate_editing(layer)
        else:
            print("unchecked")
            self.stop_editing()

    def stop_editing(self):
        self.iface.mainWindow().findChild(QAction, 'mActionToggleEditing').trigger()
        print("stop editing")

    def sudut_jarak(self):
        print("sudut jarak")
        for x in self.iface.advancedDigitizeToolBar().actions():
            print(x.text())
            if x.text() == 'Enable advanced digitizing tools':
                x.trigger()
                print(x)

    def auto_adjust(self):
        if self.adjustaction is None:
            self.adjustaction = AdjustDialog()
        self.adjustaction.show()

    def openhelp(self):
        QDesktopServices.openUrl(QUrl('https://qgis-id.github.io/'))

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
            print(layer.name(), " - ", layername)
            print(layer.name() == layername)
            if (layer.name != layername):
                print("layer exist. deleting..", layername)
                to_be_deleted = QgsProject.instance().mapLayersByName(layer.name())[0]
                self.root.removeLayer(to_be_deleted)
                # self.project.removeMapLayer(to_be_deleted.id())
            else:
                print('existing not deleting,', layer.name())

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
