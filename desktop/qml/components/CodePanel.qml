import QtQuick
import QtQuick.Controls

// CodePanel：读取**真实源码**（ctrl.code 由 Python 侧按行切片），高亮当前行。
Rectangle {
    id: panel
    color: "#141b2b"
    radius: 10
    border.color: "#223052"
    border.width: 1

    property var code: ctrl.code

    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        Text {
            text: "REAL SOURCE"
            color: "#7fb3ff"
            font.pixelSize: 12
            font.bold: true
            font.family: "Consolas"
        }
        Text {
            text: panel.code.file + "  [" + panel.code.start + "–" + panel.code.end + "]"
            color: "#8b9bb4"
            font.pixelSize: 11
            font.family: "Consolas"
        }
        Rectangle { width: parent.width; height: 1; color: "#223052" }

        ListView {
            id: lv
            width: parent.width
            height: parent.height - 60
            model: panel.code.lines
            clip: true
            interactive: false
            delegate: Rectangle {
                required property var modelData
                width: lv.width
                height: 20
                color: modelData.hl ? Qt.rgba(0.12, 0.44, 0.92, 0.28) : "transparent"

                Text {
                    x: 2
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.n
                    width: 30
                    horizontalAlignment: Text.AlignRight
                    color: modelData.hl ? "#7fb3ff" : "#4a5568"
                    font.pixelSize: 11
                    font.family: "Consolas"
                }
                Text {
                    x: 38
                    anchors.verticalCenter: parent.verticalCenter
                    text: modelData.t
                    color: modelData.hl ? "#e6edf3" : "#8b9bb4"
                    font.pixelSize: 11
                    font.family: "Consolas"
                }
            }
        }
    }
}
