import QtQuick
import QtQuick.Controls

// 步骤控制：Previous / Animate Step / Next / Reset —— **只手动推进，不自动播放**。
Rectangle {
    id: sc
    color: "#141b2b"
    radius: 10
    border.color: "#223052"
    border.width: 1

    signal previousClicked()
    signal animateClicked()
    signal nextClicked()
    signal resetClicked()

    property int step: ctrl.step
    property var names: ctrl.stepNames

    Row {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        component Btn: Button {
            id: b
            property color accent: "#33507f"
            width: 118; height: 34
            background: Rectangle {
                radius: 7
                color: b.down ? "#2c4270" : "#223052"
                border.color: b.accent
                border.width: 1
            }
            contentItem: Text {
                text: b.text
                color: "#e6edf3"
                font.pixelSize: 13
                font.family: "Segoe UI"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Btn { text: "◀  Previous"; onClicked: sc.previousClicked() }
        Btn { text: "▶  Animate Step"; accent: "#1f6feb"; onClicked: sc.animateClicked() }
        Btn { text: "Next  ▶"; onClicked: sc.nextClicked() }
        Btn { text: "↺  Reset"; accent: "#d29922"; onClicked: sc.resetClicked() }

        Item { width: 6; height: 1 }

        // 步骤指示（6 个 pill，无自动播放）
        Repeater {
            model: sc.names
            delegate: Rectangle {
                required property int index
                required property var modelData
                width: 108; height: 34
                radius: 7
                color: index === sc.step ? "#1f6feb" : "#1b2540"
                border.color: index === sc.step ? "#1f6feb" : "#223052"
                Text {
                    anchors.centerIn: parent
                    text: (index + 1) + ". " + modelData
                    color: index === sc.step ? "#ffffff" : "#8b9bb4"
                    font.pixelSize: 11
                    font.family: "Segoe UI"
                }
            }
        }
    }
}
