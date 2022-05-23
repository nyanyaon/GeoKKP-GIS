import os
from qgis.PyQt import QtWidgets, uic
from qgis.utils import iface

# create the dialog for GeoCoding
class PlaceSelectionDialog(QtWidgets.QDialog):

  def __init__(self):
    super(PlaceSelectionDialog, self).__init__()
    uic.loadUi(os.path.join(os.path.dirname(__file__), '../ui/geocode_pilihlokasi.ui'), self)