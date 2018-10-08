# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QModelIndex, QVariant

from UM.Application import Application
from UM.Logger import Logger
from UM.Qt.ListModel import ListModel

from cura.NetworkMachineManager import NetworkMachineManager

import json

#
# QML Model for network machines
#
class NetworkMachineListModel(ListModel):

    def __init__(self, parent = None):
        super().__init__(parent)

        self._application = Application.getInstance()
        self._machine_manager = self._application.getNetworkMachineManager()

        self._machine_manager.machineAdded.connect(self._itemAdded)
        self._machine_manager.machineRemoved.connect(self._itemRemoved)
        self._machine_manager.machineNewMessage.connect(self._itemUpdate)

    temperatureProgressEnabled = False

    # general events
    itemAdded = pyqtSignal(int)
    itemRemoved = pyqtSignal(int)

    # update events
    tempChange = pyqtSignal(str, int)
    nameChange = pyqtSignal(str, str)
    calibrationProgress = pyqtSignal(str, float)
    printProgress = pyqtSignal(str, float)
    tempProgress = pyqtSignal(str, float)
    materialChange = pyqtSignal(str, str)
    nozzleChange = pyqtSignal(str, float)
    fileChange = pyqtSignal(str, str, float, str)
    stateChange = pyqtSignal(str, QVariant)
    pinChange = pyqtSignal(str, bool)

    def _getItem(self, networkMachine):
        item = {
            "mID": networkMachine.id,
            "mName": networkMachine.name,
            "mIP": networkMachine.ip,
            "mMaterial": networkMachine.material,
            "mNozzle": networkMachine.nozzle,
            "mDeviceModel": networkMachine.deviceModel,
            "mFWVersion": networkMachine.fwVersion,
            "mPrintingFile": networkMachine.printingFile,
            "mElapsedTime": networkMachine.elapsedTime,
            "mEstimatedTime": networkMachine.estimatedTime,
            "mHasPin": networkMachine.hasPin,
            "mStates": networkMachine.getStates()
        }


        Logger.log("d", "get item  material: %s " % networkMachine.material)
        return item

    # machine update start

    def _onTempChange(self, uuid, extActual, extTarget, bedActual, bedTarget):
        extActual = min(extActual, extTarget)
        bedActual = min(bedActual, bedTarget)
        extRatio = 1
        bedRatio = 1
        if extTarget > 0:
            extRatio =  float(extActual) / float(extTarget)
        if bedTarget > 0:
            bedRatio = float(bedActual) / float(bedTarget)
        percentage = int(extRatio * 50) + int(bedRatio * 50)

        self.tempChange.emit(uuid, min(100, percentage))

    def _onFileChange(self, uuid, networkMachine):
        self.fileChange.emit(
            uuid,
            networkMachine.printingFile,
            networkMachine.elapsedTime,
            networkMachine.estimatedTime
        )

    def _compareVersion(self, idx, networkMachine):
        Logger.log("d", "comparing version")

    # machine update end

    def _itemUpdate(self, eventArgs):
        uuid = eventArgs.machine.id
        message = eventArgs.message['message']

        if message['event'] == "temperature_change":
            # new firmware calculates temperature on machine it self
            if self.temperatureProgressEnabled:
                return
            self._onTempChange(
                uuid,
                float(message['ext_actual']),
                float(message['ext_target']),
                float(message['bed_actual']),
                float(message['bed_target'])
            )
        elif message['event'] == "calibration_progress":
            self.calibrationProgress.emit(uuid, float(message["progress"]) / 100)
        elif message['event'] == "print_progress":
            self.printProgress.emit(uuid, float(message["progress"]) / 100)
        elif message['event'] == "new_name":
            self.nameChange.emit(uuid, message["name"])
        if message['event'] in ["material_change", "hello"]:
            self.materialChange.emit(uuid, eventArgs.machine.material)
        if message['event'] in ["nozzle_change", "hello"]:
            self.nozzleChange.emit(uuid, eventArgs.machine.nozzle)
        if message["event"] == "temperature_progress":
            self.temperatureProgressEnabled = True
            self.tempProgress.emit(uuid, float(message["progress"]) / 100)
        if message['event'] in ["start_print", "hello"]:
            self._onFileChange(uuid, eventArgs.machine)
        if message['event'] in ["states_update", "hello"]:
            self.stateChange.emit(uuid, eventArgs.machine.getStates())
        if message["event"] in ["pin_change", "hello"]:
            self.pinChange.emit(uuid, bool(eventArgs.machine.hasPin))
        if message["event"] == "hello":
            self._compareVersion(uuid, eventArgs.machine)

    def _itemAdded(self, networkMachine):
        Logger.log("d", "adding machine {model_class_name}.".format(model_class_name = self.__class__.__name__))
        index = len(self._items)
        self.beginInsertRows(QModelIndex(), index, index)
        self._items.insert(index, self._getItem(networkMachine))
        self.endInsertRows()
        self.itemAdded.emit(index)

    def _itemRemoved(self, mId):
        index = self.find("mID", mId)
        Logger.log("d", "removing machine idx: %s" % index)
        if index == -1:
            return
        self.beginRemoveRows(QModelIndex(), index, index)
        del self._items[index]
        self.endRemoveRows()
        self.itemRemoved.emit(index)
