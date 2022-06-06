from pathlib import Path

from ...qgissettingmanager import (
    # Bool,
    # Dictionary,
    Scope,
    SettingManager,
    String
)

pluginName = "GeoKKP"


class Preferences(SettingManager):
    def __init__(self):
        SettingManager.__init__(self, pluginName, False)
        home = Path.home()
        self.add_setting(
            String("exportDirectory", Scope.Global, str(home.joinpath("GeoKKP/export")))
        )
