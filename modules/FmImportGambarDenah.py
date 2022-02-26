from operator import truediv
import os
import json
import hashlib
from urllib import response

from qgis.PyQt import QtWidgets


from .utils import readSetting
from .api import endpoints
from .topology import quick_check_topology
from .memo import app_state
from .models.dataset import Dataset
from .desain_gambar_denah import DesainGambarDenah
from .BerkasRumahSusun import BerkasRumahSusun


class FmImportGambarDenah():

    def __init__(self):
        self._autoCloseBerkas = False
        self._gambarUkur = []
        self._newParcels = []
        self._oldParcels = []
        self._delParcels = []
        self._newApartments = []
        self._oldApartments = []
        self._delApartments = []
        self._errorStack = []
        self._oldGugusIds = []
        self._current_layers = []

    def setupFmMin(self):
        self._importGambarDenah = True
        self.setup_workpanel()

    def setupFm(self,nomorBerkas,tahunBerkas,gambarUkur,wilayahId,newGugusId,newParcelNumber,newApartmentNumber,newParcels,oldParcels,newApartments, oldApartment,gantiDesa,current_layers = []):

        self._nomorBerkas=nomorBerkas
        self._tahunBerkas=tahunBerkas
        self._gambarUkur=gambarUkur
        self._wilayahId = wilayahId
        self._oldParcels=oldParcels
        self._newParcels=newParcels
        self._newApartments=newApartments
        self._newParcelNumber=int(newParcelNumber)
        self._newApartmentNumber=int(newApartmentNumber)
        self._newGugusId=newGugusId
        self._oldApartments = oldApartment
        self._gantiDesa=gantiDesa
        self._current_layers = current_layers

        self._gUkurId = ""
        if len(self._gambarUkur) > 0:
            self._gUkurId= str(self._gambarUkur[0])

        self._importGambarDenah = False

        self.setup_workpanel()

    def setup_workpanel(self):

        kantor = readSetting("kantorterpilih", {})

        self._kantor_id = kantor["kantorID"]

        if(self._importGambarDenah):
            self._brs = BerkasRumahSusun()
            self._brs.show()
            self._brs.startBerkas.connect(self.BerkasRumahSusunCall)
        else:
            self._gdd = DesainGambarDenah(self._importGambarDenah,self._nomorBerkas,self._tahunBerkas,self._kantor_id,"DAG",self._gUkurId,self._wilayahId,self._newGugusId,self._newParcelNumber,self._newApartmentNumber,self._newParcels,self._oldParcels,self._newApartments,self._oldApartments,self._gantiDesa,self._current_layers)
            self._gdd.show()

    def BerkasRumahSusunCall(self,bs):
        self._nomorBerkas = bs["nomorBerkas"]
        self._tahunBerkas = bs["tahunBerkas"]
        if(bs["valid"]):
            self._autoCloseBerkas = True
            self._wilayahId = bs["wilayahId"]
            self._newParcelNumber=bs["newParcelNumber"]
            self._newApartmentNumber=bs["newApartmentNumber"]
            self._newGugusId=bs["newGugusId"]
            self._gantiDesa=bs["gantiDesa"]

            if(len(bs["gambarUkurs"])>0):
                self._gambarUkur = [bs["gambarUkurs"]]
            if(len(bs["oldParcels"])>0):
                self._oldParcels = [bs["oldParcels"]]
            if(len(bs["delParcels"])>0):
                self._delParcels = [bs["delParcels"]]
            if(len(bs["newParcels"])>0):
                self._newParcels = [bs["newParcels"]]  
            if(len(bs["oldApartments"])>0):
                self._oldApartments = [bs["oldApartments"]]     
            if(len(bs["delApartments"])>0):
                self._delApartments = [bs["delApartments"]]   
            if(len(bs["newApartments"])>0):
                self._newApartments = [bs["newApartments"]]     
            if(len(bs["oldGugusIds"])>0):
                self._oldGugusIds = [bs["oldGugusIds"]]     
       
            self._gUkurId = ""
            if(len(self._gambarUkur) > 0):
                self._gUkurId = str(self._gambarUkur[0])

            topo_error_message = []
  
            for layer in self._current_layers:
                try:
                    valid, num = quick_check_topology(layer)
                    print(valid, num)
                    if not valid:
                        message = f"Ada {num} topology error di layer {layer.name()}"
                        topo_error_message.append(message)
                except RuntimeError:
                    continue

            if topo_error_message:
                response = endpoints.stop_berkas(self._nomorBerkas,self._tahunBerkas,self._kantor_id)
                QtWidgets.QMessageBox.warning(
                    None, "Perhatian", "\n".join(topo_error_message)
                )
                return

            self._gdd = DesainGambarDenah(self._importGambarDenah,self._nomorBerkas,self._tahunBerkas,self._kantor_id,"DAG",self._gUkurId,self._wilayahId,self._newGugusId,self._newParcelNumber,self._newApartmentNumber,self._newParcels,self._oldParcels,self._newApartments,self._oldApartments,self._gantiDesa,self._current_layers)
            self._gdd.show()

        else:
            if(self._autoCloseBerkas):
                response = endpoints.stop_berkas(self._nomorBerkas,self._tahunBerkas,self._kantor_id)

            QtWidgets.QMessageBox.warning(
                    None, "Perhatian", "\n".join(bs["errorStack"])
            )
            
        
