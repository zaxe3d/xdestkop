// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: base

    color: "black"
    UM.I18nCatalog { id: catalog; name:"cura"}

    FontLoader { id: zaxeIconFont; source: "../fonts/zaxe.ttf" }

    Timer {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered:
        {
            base.showTooltip(base, {x: 0, y: item.y}, text);
        }
    }

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(base, position.x - UM.Theme.getSize("default_arrow").width, position.y);
        tooltip.show(position);
    }

    function hideTooltip()
    {
        tooltip.hide();
    }

    function onMachineAdded(id)
    {
        console.log("machine added" + id)
    }

    Component.onCompleted: {
        //base.machineAdded.connect(onMachineAdded)
        //machineList = Cura.NetworkMachineManager.machineList
    }

    Connections
    {
        target: Cura.NetworkMachineListModel
        onItemsChanged: machineListModel.update()
    }

    ListModel
    {
        id: machineListModel

        function update()
        {
            console.log("updated")
            for (var i = 0; i < Cura.NetworkMachineListModel.rowCount(); i++)
            {
                var item = Cura.NetworkMachineListModel.getItem(i)

                machineListModel.append(item)
                console.log("adding machine" + item.mName)
            }
        }
    }

    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons

        onWheel:
        {
            wheel.accepted = true;
        }
    }

    Rectangle
    {
        id: page
        color: "#212121"
        anchors.fill: parent
    }

    Component {
        id: nMachineListDelegate
        NetworkMachine { uid: mID; name: mName; ip: mIP }
    }

    ListView {
        id: nMachineList
        x: 10; anchors.top: page.top; anchors.bottomMargin: 20; anchors.topMargin: 20
        height: parent.height
        model: machineListModel
        delegate: nMachineListDelegate
    }

}
