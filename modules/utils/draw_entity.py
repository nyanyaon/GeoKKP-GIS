import json
from qgis.PyQt import QtWidgets
from ..api import endpoints
from ..utils import get_block_definition_by_type, get_layer_config_by_type, sdo_to_layer, get_project_crs


class DrawEntity:
    def __init__(self, gugus_id, get_riwayat):
        response = endpoints.get_spatial_document_sdo(gugus_id, get_riwayat)
        self._udr = json.loads(response.content)
        print(self._udr)

    def draw(self):
        if self._udr["status"] == False:
            QtWidgets.QMessageBox.error(
                None, "GeoKKP", "Proses Unduh Geometri gagal"
            )
            return

        if self._udr["geoKkpPolygons"]:
            sdo_by_type = {}
            for p in self._udr["geoKkpPolygons"]:
                sdo_by_type[p["type"]] = p
            for type, sdo in sdo_by_type.items():
                layer_config = get_layer_config_by_type(type)

                if sdo["boundary"]:
                    epsg = get_project_crs()
                    sdo_to_layer(
                        sdo=sdo,
                        name=layer_config["Nama Layer"],
                        symbol=layer_config["Style Path"],
                        crs=epsg,
                        coords_field="boundary"
                    )
                if sdo["text"]:
                    label = sdo["label"].lower()
                    if type == "BidangTanah":
                        if label.startswith("m.") or label.startswith("u.") or label.startswith("b.") or label.startswith("p.") or label.startswith("l.") or label.startswith("w."):
                            layer_config = get_layer_config_by_type("NomorHak")
                        elif label.startswith("su.") or label.startswith("gs.") or label.startswith("pll.") or label.startswith("gt.") or label.startswith("sus."):
                            layer_config = get_layer_config_by_type("NomorGSSU")
                        else:
                            layer_config = get_layer_config_by_type("NomorBidang")
                    else:
                        layer_config = get_layer_config_by_type("TeksLain")
                    print("teks")
                    print(layer_config)

                    sdo_to_layer(
                        sdo=sdo,
                        name=layer_config["Nama Layer"],
                        symbol=layer_config["Style Path"],
                        crs=epsg,
                        coords_field="text"
                    )

        if self._udr["geoKkpTitiks"]:
            for p in self._udr["geoKkpGariss"]:
                sdo_by_type[p["type"]] = p
            for type, sdo in sdo_by_type.items():
                layer_config = get_layer_config_by_type(type)

                if sdo["pointPosition"]:
                    block_config = get_block_definition_by_type(type)

                    epsg = get_project_crs()
                    if block_config:
                        nama_layer = f"({block_config['pointName']}) {block_config['remark']}"
                        sdo_to_layer(
                            sdo=sdo,
                            name=nama_layer,
                            symbol="simpletitik.qml",
                            crs=epsg,
                            coords_field="pointPosition"
                        )
                    else:
                        sdo_to_layer(
                            sdo=sdo,
                            name=layer_config["Nama Layer"],
                            symbol=layer_config["Style Path"],
                            crs=epsg,
                            coords_field="pointPosition"
                        )

        if self._udr["geoKkpGariss"]:
            for p in self._udr["geoKkpGariss"]:
                sdo_by_type[p["type"]] = p
            for type, sdo in sdo_by_type.items():
                layer_config = get_layer_config_by_type(type)

                if sdo["line"]:
                    epsg = get_project_crs()
                    sdo_to_layer(
                        sdo=sdo,
                        name=layer_config["Nama Layer"],
                        symbol=layer_config["Style Path"],
                        crs=epsg,
                        coords_field="line"
                    )

        # TODO: support dimensi type
        # TODO: support setting orientation, height, etc
