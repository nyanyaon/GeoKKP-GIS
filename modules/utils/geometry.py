import shapely
import shapely.wkt


def get_sdo_point(point, srid=24091960):
    parcel_geom = {}
    parcel_geom["ElemArrayOfInts"] = None
    parcel_geom["OrdinatesArrayOfDoubles"] = None
    parcel_geom["Dimensionality"] = 0
    parcel_geom["LRS"] = 0
    parcel_geom["GeometryType"] = 0
    parcel_geom["SdoElemInfo"] = [1, 1, 1]
    parcel_geom["SdoOrdinates"] = [point.x(), point.y()]
    parcel_geom["SdoGtype"] = 2001
    parcel_geom["SdoSRID"] = srid
    parcel_geom["SdoSRIDAsInt"] = srid
    parcel_geom["SdoPoint"] = None
    return parcel_geom


def get_sdo_polygon(feature, srid=24091960):
    polygon_info = {"id": "", "batas": "", "luas": ""}

    polygon_info["batas"], polygon_info["luas"] = build_sdo_from_polygon(feature, srid)
    return polygon_info


def build_sdo_from_polygon(feature, srid):
    geom_wkt = feature.geometry().asWkt()
    geom_shapely = shapely.wkt.loads(geom_wkt)
    geom_shapely_ccw = shapely.geometry.polygon.orient(geom_shapely, 1.0)

    luas = geom_shapely_ccw.area
    exterior = geom_shapely_ccw.exterior
    interiors = geom_shapely_ccw.interiors

    parcel_geom = {}
    parcel_geom["ElemArrayOfInts"] = None
    parcel_geom["OrdinatesArrayOfDoubles"] = None
    parcel_geom["Dimensionality"] = 0
    parcel_geom["LRS"] = 0
    parcel_geom["GeometryType"] = 0
    parcel_geom["SdoElemInfo"] = [1, 1003, 1]  # start from index 1
    prev_end = len(exterior.coords) * 2
    for interior in interiors:
        curr_start = prev_end + 1
        parcel_geom["SdoElemInfo"].append(
            curr_start
        )  # continue after exterior position
        parcel_geom["SdoElemInfo"].append(2003)
        parcel_geom["SdoElemInfo"].append(1)
        prev_end += len(interior.coords) * 2

    parcel_geom["SdoOrdinates"] = []
    parcel_geom["SdoGtype"] = 2003

    for coord in exterior.coords:
        parcel_geom["SdoOrdinates"] += coord

    for interior in interiors:
        for coord in interior.coords:
            parcel_geom["SdoOrdinates"] += coord

    parcel_geom["SdoSRID"] = srid
    parcel_geom["SdoSRIDAsInt"] = srid

    return parcel_geom, luas
