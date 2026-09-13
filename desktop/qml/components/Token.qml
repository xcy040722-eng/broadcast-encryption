import QtQuick

// 通用 token：圆角块 + 文本。位置/透明度由外层 states 控制。
Rectangle {
    id: tok

    property string label: ""
    property color accent: "#38d9a9"
    property int fontSize: 15
    property bool glow: false

    width: Math.max(62, txt.implicitWidth + 26)
    height: 34
    radius: 8

    color: Qt.rgba(accent.r, accent.g, accent.b, glow ? 0.34 : 0.16)
    border.color: accent
    border.width: glow ? 3 : 2

    opacity: 0
    scale: 1.0
    visible: opacity > 0.01

    Behavior on opacity { NumberAnimation { duration: 260 } }

    Text {
        id: txt
        anchors.centerIn: parent
        text: tok.label
        color: tok.accent
        font.pixelSize: tok.fontSize
        font.family: "Segoe UI"
    }
}
