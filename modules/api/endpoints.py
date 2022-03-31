import platform
from qgis.core import QgsExpressionContextUtils
from .base import api


ARCH = platform.processor()
QGIS_VERSION = QgsExpressionContextUtils.globalScope().variable("qgis_version")
DEFAULT_PROVIDER = "OracleMembershipProvider"
DEFAULT_APP_NAME = "KKPWeb"
DEFAULT_APP_VERSION = "4.3.0.0"


# Login Sequence
@api(endpoint="validateUser")
def login(username, password, **kwargs):
    return {
        "providerName": DEFAULT_PROVIDER,
        "applicationName": DEFAULT_APP_NAME,
        "versi": DEFAULT_APP_VERSION,
        "username": username,
        "password": password,
    }


@api(endpoint="getUserByUserName")
def get_user_by_username(username, user_is_online=True, **kwargs):
    return {
        "providerName": DEFAULT_PROVIDER,
        "applicationName": DEFAULT_APP_NAME,
        "username": username,
        "userIsOnline": user_is_online,
    }


@api(endpoint="getEntityByUserName")
def get_entity_by_username(username, **kwargs):
    return {"username": username}


@api(endpoint="getUserEntityByUserName")
def get_user_entity_by_username(
    username, kantor_id, only_valid=True, app_version="", processor_arch="", **kwargs
):
    return {
        "username": username,
        "OnlyValid": only_valid,
        "kantorid": kantor_id,
        "clientAppVersion": app_version,
        "clientProcessorArch": processor_arch,
    }


@api(endpoint="getPetugasUkur")
def get_petugas_ukur(kantor_id, **kwargs):
    return {"kantorId": kantor_id}


@api(endpoint="isESertipikat")
def get_is_e_sertifikat(kantor_id):
    return {"kantorId": str(kantor_id)}


@api(endpoint="getPropinsi")
def get_provinsi_by_kantor(kantor_id, tipe_kantor_id, **kwargs):
    tipe_kantor_id = str(tipe_kantor_id) if tipe_kantor_id else ""
    return {"kantorId": kantor_id, "tipeKantorId": tipe_kantor_id}


@api(endpoint="getKabupaten")
def get_kabupaten_by_kantor(kantor_id, tipe_kantor_id, propinsi_id, **kwargs):
    return {
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "propinsiId": propinsi_id,
    }


@api(endpoint="getKecamatan")
def get_kecamatan_by_kantor(kantor_id, tipe_kantor_id, kabupaten_id, **kwargs):
    return {
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "kabupatenId": kabupaten_id,
    }


@api(endpoint="getDesa")
def get_desa_by_kantor(kantor_id, tipe_kantor_id, kecamatan_id, **kwargs):
    return {
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "kecamatanId": kecamatan_id,
    }


@api(endpoint="getProfileGeo")
def get_profile_geo(kantor_id, user_id, **kwargs):
    return {"kantorId": kantor_id, "userId": user_id}


@api(endpoint="getProgram")
def get_program_by_kantor(kantor_id, **kwargs):
    return {"kantorId": kantor_id}


@api(endpoint="getProgramInvent")
def get_program_invent_by_kantor(kantor_id, **kwargs):
    return {"kantorId": kantor_id}


@api(endpoint="getProgramParticipatoryMapping")
def get_program_participatory_mapping_by_kantor(kantor_id, **kwargs):
    return {"kantorId": kantor_id}


@api(endpoint="getNotifikasi")
def get_notifikasi_by_kantor(kantor_id, **kwargs):
    return {"kantorId": kantor_id}


# Buka Berkas Sequence
@api(endpoint="getBerkas")
def get_berkas(
    kantor_id,
    tahun_berkas=None,
    nomor_berkas="",
    tipe_kantor_id=None,
    start=0,
    limit=20,
    count=-1,
    **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="startBerkasSpasial")
def start_berkas_spasial(
    nomor_berkas, tahun_berkas, kantor_id, tipe_kantor_id, username, **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "userName": username,
        "versi": DEFAULT_APP_VERSION,
    }


@api(endpoint="getSpatialDocumentSdo")
def get_spatial_document_sdo(gugus_ids, include_riwayat=False, **kwargs):
    return {"gugusId": gugus_ids, "getRiwayat": include_riwayat}


@api(endpoint="getBlankoByBerkasId")
def get_blanko_by_berkas_id(berkas_id, status_blanko="P", **kwargs):
    return {"berkasId": berkas_id, "statusBlanko": status_blanko}


# Simpan Berkas Sequence
@api(endpoint="getWilayahPrior")
def get_wilayah_prior(wilayah_id, **kwargs):
    return {"wilayahId": wilayah_id}


@api(endpoint="getParcels")
def get_parcels(persil_ids, **kwargs):
    return persil_ids


@api(endpoint="getApartments")
def get_apartments(apartment_ids, **kwargs):
    return apartment_ids


@api(endpoint="submitSdo")
def submit_sdo(
    nomor_berkas,
    tahun_berkas,
    kantor_id,
    tipe_kantor_id,
    wilayah_id,
    petugas_id,
    user_id,
    gugus_ids,
    gu_id,
    sistem_koordinat="TM3",
    keterangan="",
    reset302=False,
    sdo_to_submit={},
    **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "wilayahId": wilayah_id,
        "sistemKoordinat": sistem_koordinat,
        "keterangan": keterangan,
        "namapetugas": petugas_id,
        "gugusId": gugus_ids,
        "guId": gu_id,
        "reset302": reset302,
        "userid": user_id,
        "sts": sdo_to_submit,
    }


@api(endpoint="getParcelNotLinkedTo302")
def get_parcel_not_linked_to_302(berkas_id, pengukuran_ulang=True, **kwargs):
    return {"berkasId": berkas_id, "pengukuranUlang": pengukuran_ulang}


@api(endpoint="getParcelNotLinkedTo302A")
def get_parcel_not_linked_to_302a(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="get302NotLinkedToParcel")
def get_302_not_linked_to_parcel(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="get302ANotLinkedToParcel")
def get_302a_not_linked_to_parcel(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="getParcelLinkedTo302")
def get_parcel_linked_to_302(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="getParcelLinkedTo302A")
def get_parcel_linked_to_302a(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="removeParcelFromDI302")
def remove_parcel_from_di302(di302, **kwargs):
    return {"di302": di302}


@api(endpoint="removeParcelFromDI302A")
def remove_parcel_from_di302a(di302a, **kwargs):
    return {"di302A": di302a}


@api(endpoint="updateDI302")
def update_di302(di302, id_persil, nib, luas_persil, **kwargs):
    return {
        "di302": di302,
        "idPersil": id_persil,
        "nib": nib,
        "luasPersil": luas_persil,
    }


@api(endpoint="updateDI302A")
def update_di302a(di302a, id_persil, nib, luas_persil, **kwargs):
    return {
        "di302A": di302a,
        "idPersil": id_persil,
        "nib": nib,
        "luasPersil": luas_persil,
    }


@api(endpoint="unlinkAllParcelsToDI302")
def unlink_all_parcels_to_di302(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="unlinkAllParcelsToDI302A")
def unlink_all_parcels_to_di302a(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="autoLinkParcelToDI302")
def autolink_parcel_to_302(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="autoLinkParcelToDI302A")
def autolink_parcel_to_302a(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="checkPetaBidang")
def check_peta_bidang(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="createPetaBidang")
def create_peta_bidang(berkas_id, mode, kantor_id, wilayah_id, petugas_id, **kwargs):
    return {
        "berkasId": berkas_id,
        "mode": mode,
        "kantorId": kantor_id,
        "wilayahId": wilayah_id,
        "petugas": petugas_id,
    }


@api(endpoint="stopBerkas")
def stop_berkas(nomor_berkas, tahun_berkas, kantor_id, **kwargs):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
    }


# Utilities
@api(endpoint="GetZonaTm3ByBerkas")
def get_zona_tm3_by_berkas(nomor_berkas, tahun_berkas, kantor_id, **kwargs):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
    }


# Wilayah
@api(endpoint="unduhWilayahSdo")
def get_wilayah_sdo(wilayah_id, tipe_wilayah, srs, **kwargs):
    return {"wilayahId": wilayah_id, "tipeWilayah": tipe_wilayah, "srsName": srs}


@api(endpoint="gantiDesa")
def ganti_desa(
    nomor_berkas,
    tahun_berkas,
    kantor_id,
    tipe_kantor_id,
    wilayah_baru,
    object_name,
    object_lama,
    user_id,
    **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
        "tipeKantorId": tipe_kantor_id,
        "wilayahBaru": wilayah_baru,
        "objectName": object_name,
        "objectLama": object_lama,
        "userId": user_id,
    }


@api(endpoint="getProcessInfo")
def get_process_info(
    nomor_berkas, tahun_berkas, kantor_id, wilayah_id, gu_id, **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
        "wilayahId": wilayah_id,
        "guId": gu_id,
    }


@api(endpoint="getLandUseData")
def get_landuse_data(**kwargs):
    return None


@api(endpoint="getAlatUkur")
def get_alat_ukur(**kwargs):
    return None


@api(endpoint="getMetodeUkur")
def get_metode_ukur(**kwargs):
    return None


@api(endpoint="getParcelInfo")
def get_parcel_info(persil_id, **kwargs):
    return {"persilId": persil_id}


@api(endpoint="updatePersil")
def update_persil(dataset):
    return {"dSet": dataset}


@api(endpoint="getPBTForApbn")
def get_pbt_for_apbn(
    nomor_pbt="",
    tahun_pbt="",
    kantor_id="",
    proyek="",
    tipe_pbt="",
    start=0,
    limit=20,
    count=-1,
    **kwargs
):
    return {
        "nomorPBT": nomor_pbt,
        "tahunPBT": tahun_pbt,
        "kantorId": kantor_id,
        "proyek": proyek,
        "tipePBT": tipe_pbt,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="createNewPetaNominatif")
def create_new_peta_normatif(
    petugas, kendali_id, berkas_id, wilayah_id, kantor_id, pegawai_id, **kwargs
):
    return {
        "petugas": petugas,
        "kendaliId": kendali_id,
        "berkasId": berkas_id,
        "wilayahId": wilayah_id,
        "kantorId": kantor_id,
        "pegawaiId": pegawai_id,
    }


@api(endpoint="createNewPBTForApbn")
def create_new_pbt_for_apbn(
    petugas, program_id, wilayah_id, kantor_id, tipe_pbt, **kwargs
):
    return {
        "petugas": petugas,
        "programId": program_id,
        "wilayahId": wilayah_id,
        "kantorId": kantor_id,
        "tipePBT": tipe_pbt,
    }


@api(endpoint="startEditPBTForApbn")
def start_edit_pbt_for_apbn(dokumen_pengukuran_id, username, **kwargs):
    return {"dokumenPengukuranId": dokumen_pengukuran_id, "userName": username}


@api(endpoint="getRincikanbyPbt")
def get_rincikan_by_pbt(peta_bidang_id, **kwargs):
    return {"petabidangid": peta_bidang_id}


@api(endpoint="getLimitPersilPbt")
def get_limit_persil_pbt(peta_bidang_id="", kantor_id="", **kwargs):
    return {"petabidangId": peta_bidang_id, "kantorId": kantor_id}


@api(endpoint="submitForPtslKtRedis")
def submit_for_ptsl_kt_redis(
    dokumen_pengukuran_id="",
    program_id="",
    kantor_id="",
    wilayah_id="",
    sistem_koordinat="",
    keterangan="",
    petugas="",
    sts={},
    gugus_id="",
    gu_id="",
    user_id="",
    jumlah_persil="",
    **kwargs
):
    return {
        "dokumenPengukuranId": dokumen_pengukuran_id,
        "programId": program_id,
        "kantorId": kantor_id,
        "wilayahId": wilayah_id,
        "sistemKoordinat": sistem_koordinat,
        "keterangan": keterangan,
        "petugas": petugas,
        "sts": sts,
        "gugusId": gugus_id,
        "guId": gu_id,
        "userId": user_id,
        "jumlahPersil": jumlah_persil,
    }


@api(endpoint="stopPBT")
def stop_pbt(dokumen_pengukuran_id, **kwargs):
    return {"dokumenPengukuranId": dokumen_pengukuran_id}


@api(endpoint="uploadDxfPbtSkb")
def upload_dxf_pbt_skb(
    kantor_id="", mitra_kerja_id="", dok_ukur_id="", file="", **kwargs
):
    return {
        "kantorId": kantor_id,
        "mitrakerjaId": mitra_kerja_id,
        "dokukurId": dok_ukur_id,
        "theFile": file,
    }


@api(endpoint="cekMapping")
def cek_mapping(persil_ids, **kwargs):
    return persil_ids


@api(endpoint="finnishPBT")
def finish_pbt(dokumen_pengukuran_id, **kwargs):
    return {"dokumenPengukuranId": dokumen_pengukuran_id}


@api(endpoint="UnduhPersilSdo")
def unduh_persil_sdo(wilayah_id, str_nib, srs_name, start, limit, count, **kwargs):
    return {
        "wilayahId": wilayah_id,
        "strNib": str_nib,
        "srsName": srs_name,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="parcelWindowSdo")
def parcel_window_sdo(minX, minY, maxX, maxY, srsName, **kwargs):
    return {
        "minX": minX,
        "minY": minY,
        "maxX": maxX,
        "maxY": maxY,
        "srsName": srsName,
    }


@api(endpoint="getUnlinkedPBTBerkas")
def get_unlinked_pbt_berkas(dokumen_pengukuran_id, **kwargs):
    return {"dokumenPengukuranId": dokumen_pengukuran_id}


@api(endpoint="getBerkasForApbn")
def get_berkas_for_apbn(
    nomor_berkas, tahun_berkas, kantor_id, program_id, start, limit, count, **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "kantorId": kantor_id,
        "programId": program_id,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="entryPersilKeBerkasApbn")
def entry_persil_ke_berkas_apbn(
    persil_id,
    nomor_induk_bidang,
    luas_bidang,
    berkas_id,
    dokumen_pengukuran_id,
    kantor_id,
    petugas,
    **kwargs
):
    return {
        "persilId": persil_id,
        "nomorIndukBidang": nomor_induk_bidang,
        "luasBidang": luas_bidang,
        "berkasId": berkas_id,
        "dokumenPengukuranId": dokumen_pengukuran_id,
        "kantorId": kantor_id,
        "petugas": petugas,
    }


@api(endpoint="getParcelInPBT")
def get_parcel_in_pbt(dokumen_pengukuran_id, **kwargs):
    return {"dokumenPengukuranId": dokumen_pengukuran_id}


@api(endpoint="getParcelPropertyForApbn")
def get_parcel_property_for_apbn(persil_id, **kwargs):
    return {"persilId": persil_id}


@api(endpoint="getBerkasApbnByPBTId")
def get_berkas_apbn_by_pbt_id(
    nomor_berkas, tahun_berkas, dokumen_pengukuran_id, start, limit, count, **kwargs
):
    return {
        "nomorBerkas": nomor_berkas,
        "tahunBerkas": tahun_berkas,
        "dokumenPengukuranId": dokumen_pengukuran_id,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="getGambarUkurApbnByBerkas")
def get_gambar_ukur_apbn_by_berkas(berkas_id, **kwargs):
    return {"berkasId": berkas_id}


@api(endpoint="addPetugasUkurGU")
def add_petugas_ukur_gu(
    gambar_ukur_id, pegawai_id, tgl_mulai, tgl_selesai, user_id, **kwargs
):
    return {
        "gambarUkurId": gambar_ukur_id,
        "pegawaiId": pegawai_id,
        "tglMulai": tgl_mulai,
        "tglSelesai": tgl_selesai,
        "userId": user_id,
    }


@api(endpoint="addTetanggaGU")
def add_tetangga_gu(gambar_ukur_id, arah, nama_tetangga, user_id, **kwargs):
    return {
        "gambarUkurId": gambar_ukur_id,
        "arah": arah,
        "namaTetangga": nama_tetangga,
        "userId": user_id,
    }


@api(endpoint="deleteGUPetugasUkur")
def delete_gu_petugas_ukur(petugas_ukur_id, gambar_ukur_id, **kwargs):
    return {"petugasUkurId": petugas_ukur_id, "gambarUkurId": gambar_ukur_id}


@api(endpoint="deleteTetangga")
def delete_tetangga(tetangga_id, gambar_ukur_id, **kwargs):
    return {"tetanggaId": tetangga_id, "gambarUkurId": gambar_ukur_id}


@api(endpoint="updateTetangga")
def update_tetangga(
    tetangga_id, arah_tetangga, nama_tetangga, gambar_ukur_id, **kwargs
):
    return {
        "tetanggaId": tetangga_id,
        "arahTetangga": arah_tetangga,
        "namaTetangga": nama_tetangga,
        "gambarUkurId": gambar_ukur_id,
    }


@api(endpoint="updatePetugasGU")
def update_petugas_ukur_gu(
    petugas_ukur_lama_id,
    gambar_ukur_id,
    petugas_ukur_baru_id,
    tgl_mulai,
    tgl_selesai,
    **kwargs
):
    return {
        "petugasUkuraLamaId": petugas_ukur_lama_id,
        "gambarUkurId": gambar_ukur_id,
        "petugasUkurBaruId": petugas_ukur_baru_id,
        "tglMulai": tgl_mulai,
        "tglSelesai": tgl_selesai,
    }


@api(endpoint="getGambarDenah")
def getGambarDenah(wilayahId, kantorId, nomorGD, tahunGD, start, limit, count, **kwargs):
    return {
        "wilayahId": wilayahId,
        "kantorId": kantorId,
        "nomorGD": nomorGD,
        "tahunGD": tahunGD,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="startBerkasSpasialByDokumenPengukuranId")
def startBerkasSpasialByDokumenPengukuranId(dokumenPengukuranId, kantorId, userName, **kwargs):
    return {
        "dokumenPengukuranId": dokumenPengukuranId,
        "kantorId": kantorId,
        "userName": userName,
        "versi": DEFAULT_APP_VERSION,
    }


@api(endpoint="getBerkasHMSRS")
def getBerkasHMSRS(nomorBerkas, tahunBerkas, kantorId, start, limit, count, **kwargs):
    return {
        "nomorBerkas": nomorBerkas,
        "tahunBerkas": tahunBerkas,
        "kantorId": kantorId,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="getSuratUkur")
def get_surat_ukur(
    wilayah_id, tipe_su, nomor_su, tahun_su, start, limit, count, **kwargs
):
    return {
        "wilayahId": wilayah_id,
        "tipeSU": tipe_su,
        "nomorSU": nomor_su,
        "tahunSU": tahun_su,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="startImportDokumenPengukuran")
def start_import_dokumen_pengukuran(surat_ukur_id, **kwargs):
    return{"suratUkurId": surat_ukur_id}


@api(endpoint="getDetailMapInfoByPersilId")
def get_detail_map_info_by_persil_id(persil_id, **kwargs):
    return {
        "persilId": persil_id
    }


@api(endpoint="getDetailMapInfo")
def get_detail_map_info(wilayah_id, nomor_bidang, **kwargs):
    return {
        "wilayahId": wilayah_id,
        "nomorBidang": nomor_bidang
    }


@api(endpoint="getDetailMapInfo2")
def get_detail_map_info_2(wilayah_id, tipe_su, nomor_su, tahun_su, **kwargs):
    return {
        "wilayahId": wilayah_id,
        "tipeSu": tipe_su,
        "nomorSu": nomor_su,
        "tahunSu": tahun_su
    }


@api(endpoint="getDetailMapInfo1")
def get_detail_map_info_1(wilayah_id, tipe_hak, nomor_hak, **kwargs):
    return {
        "wilayahId": wilayah_id,
        "tipaHak": tipe_hak,
        "nomorHak": nomor_hak
    }


@api(endpoint="updateGeometriPersilSdo")
def update_geometri_persil_sdo(pp, **kwargs):
    return pp


@api(endpoint="createPersilMapSdo")
def create_persil_map_sdo(wilayah_id, pp, **kwargs):
    return {
        "wilayahId": wilayah_id,
        "pp": pp
    }


@api(endpoint="updateGeometriPersilByNibSdo")
def update_geometry_persil_by_nib_sdo(pemper, **kwargs):
    return pemper


@api(endpoint="updateGeometriPersilByHakSdo")
def update_geometry_persil_by_hak_sdo(pemper, **kwargs):
    return pemper


@api(endpoint="updateGeometriPersilBySUSdo")
def update_geometry_persil_by_su_sdo(pemper, **kwargs):
    return pemper


@api(endpoint="updateGeometriPersilLegalSdo")
def update_geometri_persil_legal_sdo(
        kantor_id, nama_petugas, sts, gugus_id, user_id, **kwargs):
    return {
        "kantorId": kantor_id,
        "namapetugas": nama_petugas,
        "sts": sts,
        "gugusId": gugus_id,
        "userid": user_id
    }


@api(endpoint="unduhPersilParSdo")
def unduh_persil_par_sdo(
        jenis_hak, no_sertipikat, wilayah_id, kantor_id, username, srs_name, start, limit, count,  **kwargs):
    return {
        "jenisHak": jenis_hak,
        "noSertipikat": no_sertipikat,
        "wilayahId": wilayah_id,
        "kantorId": kantor_id,
        "username": username,
        "srsName": srs_name,
        "start": start,
        "limit": limit,
        "count": count,
    }


@api(endpoint="getTandaTerimaPtslPM")
def get_tanda_terima_ptsl_pm(kantor_id, nomor, tahun, program_id, wilayah_id, **kwargs):
    return{
        "kantorId": kantor_id,
        "nomor": nomor,
        "tahun": tahun,
        "programId": program_id,
        "wilayahId": wilayah_id,
    }


@api(endpoint="unduhPersilParPTSLSdo")
def unduh_persil_par_ptsl_sdo(gugus_id, kantor_id, username, srs_name, **kwargs):
    return {
        "gugusId": gugus_id,
        "kantorId": kantor_id,
        "username": username,
        "srsName": srs_name,
    }


@api(endpoint="submitPTSLPMSdo")
def submit_ptsl_pm_sdo(tanda_terima_id, kantor_id, wilayah_id, gambar_ukur_id, tm3srid, keterangan, user_id, jumlah_persil, sts):
    return {
        "tandaTerimaId": tanda_terima_id,
        "kantorId": kantor_id,
        "wilayahId": wilayah_id,
        "gambarukurId": gambar_ukur_id,
        "tm3srid": tm3srid,
        "keterangan": keterangan,
        "userid": user_id,
        "jumlahPersil": jumlah_persil,
        "sts": sts,
    }


@api(endpoint="unduhWilayahSdo")
def unduh_wilayah_sdo(wilayah_id, srs_name, tipe_wilayah, **kwargs):
    return {
        "wilayahId": wilayah_id,
        "srsName": srs_name,
        "tipeWilayah": tipe_wilayah
    }

@api(endpoint="getWilayahPtslSkb")
def get_wilayah_ptsl_skb(kantor_id):
    return {
        "kantorId": kantor_id
    }

@api(endpoint="GetTandaTerimaPtslSkb")
def get_tanda_terima_ptsl_skb(kantor_id, nomor, tahun, program_id, surveyor_id, wilayah_id):
    return {
        "kantorId": kantor_id,
        "nomor": nomor,
        "tahun": tahun,
        "programId": program_id,
        "surveyorId": surveyor_id,
        "wilayahId": wilayah_id
    }

@api(endpoint="tolakPBTForPtslSkb")
def tolak_pbt_for_ptsl_skb(user_id, kantor_id, tandaterima_id, catatan):
    return{
        "userId": user_id,
        "kantorId": kantor_id,
        "tandaterimaId": tandaterima_id,
        "catatan": catatan
    }

@api(endpoint="createNewPBTForPtslSkb")
def create_new_pbt_for_ptsl_skb(user_id,program_id,wilayah_id,surveyor_id,tandaterima_id):
    return{
        "userId": user_id,
        "programId": program_id,
        "wilayahId": wilayah_id,
        "surveyorId": surveyor_id,
        "tandaterimaId": tandaterima_id
    }