from qgis.PyQt.QtWidgets import QFileDialog


class ImportGeomFromFile:
    def __init__(self, parent=None, *args, **kwargs):
        self.parent = parent
        self._file = None

    def _show_using_plotxy(self, file):
        self.parent.plotxy()
        with open(file, "r") as f:
            self.parent.plotxyaction.list_coords.setText(f.read())

    def show(self):
        file = QFileDialog.getOpenFileName(self.parent.iface.mainWindow(), "Import CSV", self.parent.plugin_dir,filter="Supported File (*csv *txt)")
        if len(file) == 2 and file[0]:
            self._show_using_plotxy(file[0])
