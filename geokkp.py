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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction,QMessageBox
from qgis.core import Qgis, QgsVectorLayer, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem


# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
import os.path
import json
import re
from .geokkp_dockwidget import GeoKKPDockWidget

# Modules
from .modules.gotoxy import GotoXYDialog
from .modules.plotcoord import PlotCoordinateDialog


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
        self.project = QgsProject
        self.root = QgsProject.instance().layerTreeRoot()

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
        self.menu = self.tr(u'&GeoKKP-GIS')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeoKKP')
        self.toolbar.setObjectName(u'GeoKKP')

        #change title, for fun
        title = self.iface.mainWindow().windowTitle()
        new_title = title.replace('QGIS', 'GeoKKP-GIS')
        self.iface.mainWindow().setWindowTitle(new_title)

        self.pluginIsActive = False

        #self.canvasClicked = pyqtSignal('QgsPointXY')

        #self.dockwidget = None
        self.dockwidget = GeoKKPDockWidget()
        self.gotoxyaction = GotoXYDialog()
        self.plotxyaction = PlotCoordinateDialog()



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

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Add Interface: Docked Main Panel GeoKKP
        icon_path = ':/plugins/geokkp/images/icon.png'
        icon = QIcon(icon_path)
        self.iface.mainWindow().setWindowIcon(icon)
        self.add_action(icon_path,text=self.tr(u'Panel GeoKKP'), 
            callback=self.run,parent=self.iface.mainWindow())
        
        # Add Interface: Login Dialog
        icon_path = ':/plugins/geokkp/images/login.png'
        self.add_action(icon_path, text=self.tr(u'Login Pengguna'),
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: Download Parcel GeoKKP Database Dialog
        icon_path = ':/plugins/geokkp/images/getparcel.png'
        self.add_action(icon_path, text=self.tr(u'Unduh Bidang Tanah'), 
            callback=self.addWMSParcel, parent=self.iface.mainWindow())

        self.toolbar.addSeparator()

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

        # Add Interface: Parcel Dimension
        icon_path = ':/plugins/geokkp/images/dimension.png'
        self.add_action(icon_path, text=self.tr(u'Gambar Dimensi'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())
        
        self.toolbar.addSeparator()

        # Add Interface: Topology
        icon_path = ':/plugins/geokkp/images/topology.png'
        self.add_action(icon_path, text=self.tr(u'Cek Topologi'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: Layout
        icon_path = ':/plugins/geokkp/images/layout.png'
        self.add_action(icon_path, text=self.tr(u'Layout Peta'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

        self.toolbar.addSeparator()

        # Add Interface: Coordinate Transformation
        icon_path = ':/plugins/geokkp/images/conversion.png'
        self.add_action(icon_path, text=self.tr(u'Transformasi Koordinat'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: Zoom To
        icon_path = ':/plugins/geokkp/images/zoomto.png'
        self.add_action(icon_path, text=self.tr(u'Zoom Ke XY'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: Change Basemap
        icon_path = ':/plugins/geokkp/images/basemap.png'
        self.add_action(icon_path, text=self.tr(u'Ganti Basemap'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

        # Add Interface: OAM
        icon_path = ':/plugins/geokkp/images/openaerialmap.png'
        self.add_action(icon_path, text=self.tr(u'OpenAerialMap'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

        self.toolbar.addSeparator()

        # Add Interface: Settings
        icon_path = ':/plugins/geokkp/images/settings.png'
        self.add_action(icon_path, text=self.tr(u'Pengaturan'), 
            callback=self.gotoxy, parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING GeoKKP"

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

        #print "** UNLOAD GeoKKP"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GeoKKP-GIS'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------    

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING GeoKKP"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
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
            self.dockwidget.buat_basisdata.clicked.connect(self.createDb)

    def gotoxy(self):
        if self.gotoxyaction == None:
                # Create the dockwidget (after translation) and keep reference
                self.gotoxyaction = GotoXYDialog()
        self.gotoxyaction.selectProj.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

            # connect to provide cleanup on closing of dockwidget
        #self.gotoxyaction.closingPlugin.connect(self.onClosePlugin)

        # show the dialog
        #self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.gotoxyaction.show()

    def plotxy(self):
        if self.plotxyaction == None:
                # Create the dockwidget (after translation) and keep reference
                self.plotxyaction = PlotCoordinateDialog()
        self.plotxyaction.listCoordsProj.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

            # connect to provide cleanup on closing of dockwidget
        #self.gotoxyaction.closingPlugin.connect(self.onClosePlugin)

        # show the dialog
        #self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.plotxyaction.show()


        


#--------------------------------------------------------------------------
# Methods for GeoKKP Dock Widget
    
    def selectLocation(self):
        """ what to do when user clicks location selection """

        urlWithParams = "http://mt0.google.com/vt/lyrs%3Ds%26hl%3Den%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D"
        self.loadXYZ(urlWithParams, 'Google Basemap')
        #self.delIfLayerExist('Google Basemap')

        selectedLocation = json.dumps(self.dockwidget.loadLocation())
        #self.delIfLayerExist('Wilayah Kerja')

        wilkerLayer = self.iface.addVectorLayer(selectedLocation, '' , 'ogr')
        wilkerLayer.setName('Wilayah Kerja')
        self.iface.actionZoomToLayer().trigger()
        wilkerLayer.renderer().symbol().setColor(QColor("transparent"))
        wilkerLayer.renderer().symbol().symbolLayer(0).setStrokeColor(QColor(255,0,0))
        wilkerLayer.renderer().symbol().symbolLayer(0).setStrokeWidth(1)
        wilkerLayer.triggerRepaint()        
        #self.project.instance().addMapLayer(wilkerLayer)
    
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
                #self.project.removeMapLayer(to_be_deleted.id())
            else:
                print('existing not deleting,', layer.name())

    #--------------------------------------------------------------------------

    def createDb(self):
        projectName = self.dockwidget.nama_kegiatan.text().lower()
        userName = self.dockwidget.nama_pelaksana.text().lower()
        projectName = self.properify(projectName)
        userName = self.properify(userName)
        uri = 'geopackage:/plugins/geokkp/projects/' + userName + '.gpkg?projectName='+ projectName
        print(self.project.instance().write(uri))
        #curr = self.dockwidget.tabGeoKKP.currentIndex()
        #print("current tab:", curr)
        #self.dockwidget.tabGeoKKP.setCurrentIndex(curr+1)


    def properify(self, text):
        # Remove all non-word characters (everything except numbers and letters)
        text = re.sub(r"[^\w\s]", '', text)

        # Replace all runs of whitespace with a single dash
        text = re.sub(r"\s+", '_', text)

        return text

    def addWMSParcel(self):
        wms_url= "url=https://103.123.13.78/geoserver/umum/wms&format=image/png&layers=PersilHak&styles=&crs=EPSG:4326"
        rasterLyr = QgsRasterLayer(wms_url, "Bidang Tanah", "wms")
        self.project.instance().addMapLayer(rasterLyr)
        self.iface.messageBar().pushMessage("Sukses", "Berhasil menambahkan layer Bidang Tanah", level=Qgis.Success, duration=4)
        #self.delIfLayerExist('Bidang Tanah')





    


