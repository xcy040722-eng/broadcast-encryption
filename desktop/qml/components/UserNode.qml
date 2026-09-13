import QtQuick

// 用户节点：圆形 + uid；recipient 时高亮。
Item {
    id: un
    property int uid: 1
    property bool recipient: false
    property string wfp: ""
    property real radius: 36

    width: radius * 2
    height: radius * 2

    Rectangle {
        id: circle
        anchors.fill: parent
        radius: un.radius
        color: un.recipient ? Qt.rgba(0.31, 0.81, 0.40, un.activeFocus ? 0.34 : 0.22)
                            : Qt.rgba(0.36, 0.40, 0.45, 0.16)
        border.color: un.recipient ? "#51cf66" : "#5c6773"
        border.width: un.recipient ? 3 : 2
    }

    Text {
        anchors.centerIn: parent
        text: "u" + un.uid
        color: un.recipient ? "#8ce99a" : "#8b9bb4"
        font.pixelSize: 22
        font.bold: true
        font.family: "Segoe UI"
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.bottom
        anchors.topMargin: 4
        text: un.wfp
        color: "#5c6773"
        font.pixelSize: 11
        font.family: "Consolas"
    }
}
