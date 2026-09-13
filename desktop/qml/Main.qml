import QtQuick
import QtQuick.Controls
import "components"

ApplicationWindow {
    id: root
    width: 1440
    height: 820
    visible: true
    color: "#0f1420"
    title: "CHW25 DBE — Desktop POC  (N=4, S={2,4}, u2, mu=1)"

    property int step: ctrl.step
    property var tr: ctrl.trace
    property var ct: ctrl.ct
    property var pm: ctrl.params
    property int mu: ctrl.mu
    property int uid: ctrl.focusUser

    // 数轴映射
    property real nlX0: 130
    property real nlX1: 900
    function nlPos(frac) { return nlX0 + (frac + 1) / 2 * (nlX1 - nlX0) }
    function zFrac() {
        var f = tr.z_centered / pm.half_q
        return Math.max(-1, Math.min(1, f))
    }

    // ================= 舞台 =================
    // 设计：token 的 x/y 是「静止位置」（写在声明里），states 只切 opacity，
    //       步内的移动用显式 SequentialAnimation / ParallelAnimation。
    //       这样隐藏时只淡出、不会飞向 (0,0)。
    Rectangle {
        id: stage
        x: 16; y: 16; width: 1020; height: 700
        color: "#141b2b"; radius: 10
        border.color: "#223052"; border.width: 1
        clip: true

        Text {
            x: 14; y: 10
            text: "CHW25 Construction 6.4  —  DBE"
            color: "#7fb3ff"; font.pixelSize: 13; font.bold: true; font.family: "Segoe UI"
        }

        // ---------- 用户节点（始终保留） ----------
        Repeater {
            model: ctrl.users
            delegate: UserNode {
                required property var modelData
                required property int index
                uid: modelData.id
                recipient: modelData.recipient
                wfp: modelData.W_fp
                x: 130 + index * 200 - 36
                y: 600
                opacity: {
                    if (root.step === 0) return modelData.recipient ? 1.0 : 0.36
                    return modelData.recipient ? 0.95 : 0.24
                }
                Behavior on opacity { NumberAnimation { duration: 380 } }
            }
        }

        // ---------- 聚合步骤的 token（静止位置已写死） ----------
        Token { id: w2Tok;  label: "W2"; accent: "#38d9a9"; x: 400; y: 330 }
        Token { id: w4Tok;  label: "W4"; accent: "#38d9a9"; x: 560; y: 330 }
        Token { id: wsTok;  label: "W_S = W2 + W4"; accent: "#38d9a9"; x: 415; y: 262; fontSize: 16; glow: true }

        Token { id: sTok;   label: "s"; accent: "#4dabf7"; x: 40;  y: 190 }
        Token { id: eTok;   label: "e"; accent: "#ff922b"; x: 910; y: 190 }
        Token { id: aTok;   label: "A"; accent: "#4dabf7"; x: 210; y: 110 }
        Token { id: w0sTok; label: "W0 + W_S"; accent: "#38d9a9"; x: 420; y: 110 }
        Token { id: pTok;   label: "p"; accent: "#4dabf7"; x: 700; y: 110 }
        Token { id: c1Tok;  label: "c1 = " + ct.c1_0; accent: "#ffd43b"; x: 150; y: 320 }
        Token { id: c2Tok;  label: "c2 = " + ct.c2_0; accent: "#ffd43b"; x: 420; y: 320 }
        Token { id: c3Tok;  label: "c3 = " + ct.c3; accent: "#ffd43b"; x: 690; y: 320 }
        Token { id: capTok; label: "ct = (xi, c1, c2, c3)"; accent: "#ffd43b"; x: 360; y: 500; fontSize: 17; glow: true }

        Token { id: y22Tok; label: "y" + uid + uid; accent: "#ff922b"; x: 110; y: 170 }
        Token { id: y02Tok; label: "y0" + uid; accent: "#ff922b"; x: 110; y: 470 }
        Token { id: y4Tok;  label: "y4" + uid; accent: "#ff922b"; x: 830; y: 170 }
        Token { id: y2Tok;  label: "Y" + uid; accent: "#3fb950"; x: 450; y: 330; fontSize: 17; glow: true }

        Rectangle {
            id: sigma
            x: 470; y: 300
            width: 78; height: 78; radius: 39
            color: Qt.rgba(0.25, 0.72, 0.31, 0.18)
            border.color: "#3fb950"; border.width: 3
            opacity: 0
            Text {
                anchors.centerIn: parent; text: "SUM"
                color: "#8ce99a"; font.pixelSize: 15; font.bold: true; font.family: "Segoe UI"
            }
        }

        // ---------- Cancellation ----------
        Item {
            id: cancelRoot
            anchors.fill: parent
            opacity: 0

            Column {
                x: 150; y: 150; spacing: 22
                Text { id: lHead; opacity: 0; text: "L = c3 + c2^T r" + root.uid; color: "#cfe3ff"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: l0; opacity: 0; text: "mu*floor(q/2)"; color: "#e6edf3"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: l1; opacity: 0; text: "+ s^T p"; color: "#e64980"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: l2; opacity: 0; text: "+ s^T (W0+WS) r" + root.uid; color: "#e64980"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: l3; opacity: 0; text: "+ e~2"; color: "#e6edf3"; font.pixelSize: 17; font.family: "Consolas" }
            }
            Column {
                x: 660; y: 150; spacing: 22
                Text { id: rHead; opacity: 0; text: "R = c1^T Y" + root.uid; color: "#cfe3ff"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: r0; opacity: 0; text: "+ s^T p"; color: "#e64980"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: r1; opacity: 0; text: "+ s^T (W0+WS) r" + root.uid; color: "#e64980"; font.pixelSize: 17; font.family: "Consolas" }
                Text { id: r2; opacity: 0; text: "+ e~1"; color: "#e6edf3"; font.pixelSize: 17; font.family: "Consolas" }
            }

            Rectangle { id: conn1; height: 2; color: "#e64980"; opacity: 0 }
            Rectangle { id: conn2; height: 2; color: "#e64980"; opacity: 0 }

            Text {
                id: zRes; x: 150; y: 470; opacity: 0
                text: "z = mu*floor(q/2) - e~1 + e~2   =   " + tr.z_centered
                color: "#3fb950"; font.pixelSize: 22; font.family: "Consolas"
            }
            Text {
                id: zNoise; x: 150; y: 512; opacity: 0
                text: "noise = " + tr.noise_residual
                color: "#8b9bb4"; font.pixelSize: 15; font.family: "Consolas"
            }
        }

        // ---------- Threshold ----------
        Item {
            id: thrRoot
            anchors.fill: parent
            opacity: 0

            Rectangle { x: root.nlX0; y: 330; width: root.nlX1 - root.nlX0; height: 2; color: "#8b9bb4" }
            Rectangle {
                x: root.nlPos(-0.5); y: 326; width: root.nlPos(0.5) - root.nlPos(-0.5)
                height: 10; color: Qt.rgba(0.25, 0.72, 0.31, 0.35)
            }
            Repeater {
                model: [
                    { f: -1.0, t: "-q/2" }, { f: -0.5, t: "-q/4" }, { f: 0.0, t: "0" },
                    { f: 0.5, t: "q/4" }, { f: 1.0, t: "q/2" }
                ]
                delegate: Item {
                    required property var modelData
                    x: root.nlPos(modelData.f) - 30; y: 332
                    width: 60; height: 30
                    Rectangle { anchors.horizontalCenter: parent.horizontalCenter; width: 1; height: 10; color: "#8b9bb4" }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter; y: 12
                        text: modelData.t; color: "#8b9bb4"; font.pixelSize: 13; font.family: "Consolas"
                    }
                }
            }
            Rectangle { id: marker; width: 18; height: 18; radius: 9; color: "#ff922b"; y: 322; x: root.nlPos(0) - 9 }
            Text {
                x: root.nlX0; y: 430
                text: "z_centered = " + tr.z_centered + "   ->   mu = " + tr.decoded_mu
                color: "#3fb950"; font.pixelSize: 22; font.family: "Consolas"
            }
        }

        // ================= states：只切 opacity =================
        states: [
            State {
                name: "s0"
            },
            State {
                name: "s1"
                PropertyChanges { target: w2Tok; opacity: 1 }
                PropertyChanges { target: w4Tok; opacity: 1 }
                PropertyChanges { target: wsTok; opacity: 1 }
            },
            State {
                name: "s2"
                PropertyChanges { target: sTok; opacity: 1 }
                PropertyChanges { target: eTok; opacity: 1 }
                PropertyChanges { target: aTok; opacity: 1 }
                PropertyChanges { target: w0sTok; opacity: 1 }
                PropertyChanges { target: pTok; opacity: 1 }
                PropertyChanges { target: c1Tok; opacity: 1 }
                PropertyChanges { target: c2Tok; opacity: 1 }
                PropertyChanges { target: c3Tok; opacity: 1 }
                PropertyChanges { target: capTok; opacity: 1 }
            },
            State {
                name: "s3"
                PropertyChanges { target: sigma; opacity: 1 }
                PropertyChanges { target: y22Tok; opacity: 1 }
                PropertyChanges { target: y02Tok; opacity: 1 }
                PropertyChanges { target: y4Tok; opacity: 1 }
                PropertyChanges { target: y2Tok; opacity: 1 }
            },
            State {
                name: "s4"
                PropertyChanges { target: cancelRoot; opacity: 1 }
            },
            State {
                name: "s5"
                PropertyChanges { target: thrRoot; opacity: 1 }
            }
        ]

        transitions: [
            Transition {
                from: "*"; to: "*"
                NumberAnimation { properties: "opacity"; duration: 300; easing.type: Easing.OutQuad }
            }
        ]

        // ---------- 步内移动动画（Play / Animate Step / Next 时触发） ----------

        // ② Build W_S：W2/W4 从 u2/u4 上方飞入并汇聚
        ParallelAnimation {
            id: wsAnim
            NumberAnimation { target: w2Tok; property: "x"; from: 300; to: 400; duration: 560; easing.type: Easing.InOutCubic }
            NumberAnimation { target: w2Tok; property: "y"; from: 470; to: 330; duration: 560; easing.type: Easing.InOutCubic }
            NumberAnimation { target: w4Tok; property: "x"; from: 620; to: 560; duration: 560; easing.type: Easing.InOutCubic }
            NumberAnimation { target: w4Tok; property: "y"; from: 470; to: 330; duration: 560; easing.type: Easing.InOutCubic }
        }

        // ④ Build Y_2：三个 y 分量飞向 SUM 节点
        ParallelAnimation {
            id: y2Anim
            NumberAnimation { target: y22Tok; property: "x"; from: 60;  to: 300; duration: 520; easing.type: Easing.InOutCubic }
            NumberAnimation { target: y22Tok; property: "y"; from: 90;  to: 220; duration: 520; easing.type: Easing.InOutCubic }
            NumberAnimation { target: y02Tok; property: "x"; from: 60;  to: 300; duration: 520; easing.type: Easing.InOutCubic }
            NumberAnimation { target: y02Tok; property: "y"; from: 520; to: 390; duration: 520; easing.type: Easing.InOutCubic }
            NumberAnimation { target: y4Tok;  property: "x"; from: 900; to: 690; duration: 520; easing.type: Easing.InOutCubic }
            NumberAnimation { target: y4Tok;  property: "y"; from: 90;  to: 220; duration: 520; easing.type: Easing.InOutCubic }
        }

        // ⑤ Cancellation：逐项展开 → 连线 → 同步划消 → 结果
        SequentialAnimation {
            id: cancellationAnim
            ParallelAnimation {
                NumberAnimation { target: lHead; property: "opacity"; to: 1; duration: 170 }
                NumberAnimation { target: rHead; property: "opacity"; to: 1; duration: 170 }
                NumberAnimation { target: l0; property: "opacity"; to: 1; duration: 170 }
            }
            ParallelAnimation {
                NumberAnimation { target: l1; property: "opacity"; to: 1; duration: 210 }
                NumberAnimation { target: r0; property: "opacity"; to: 1; duration: 210 }
            }
            ParallelAnimation {
                NumberAnimation { target: l2; property: "opacity"; to: 1; duration: 210 }
                NumberAnimation { target: r1; property: "opacity"; to: 1; duration: 210 }
            }
            ParallelAnimation {
                NumberAnimation { target: l3; property: "opacity"; to: 1; duration: 210 }
                NumberAnimation { target: r2; property: "opacity"; to: 1; duration: 210 }
            }
            ParallelAnimation {
                NumberAnimation { target: conn1; property: "x"; from: 150 + 130; to: 660 - 8; duration: 330 }
                NumberAnimation { target: conn1; property: "width"; from: 0; to: (660 - 8) - (150 + 130); duration: 330 }
                NumberAnimation { target: conn1; property: "y"; to: 150 + 22 + 9; duration: 1 }
                NumberAnimation { target: conn1; property: "opacity"; to: 1; duration: 330 }
                NumberAnimation { target: conn2; property: "x"; from: 150 + 190; to: 660 - 8; duration: 330 }
                NumberAnimation { target: conn2; property: "width"; from: 0; to: (660 - 8) - (150 + 190); duration: 330 }
                NumberAnimation { target: conn2; property: "y"; to: 150 + 44 + 9; duration: 1 }
                NumberAnimation { target: conn2; property: "opacity"; to: 1; duration: 330 }
            }
            PauseAnimation { duration: 240 }
            ParallelAnimation {
                NumberAnimation { target: l1; property: "opacity"; to: 0.12; duration: 520 }
                NumberAnimation { target: l2; property: "opacity"; to: 0.12; duration: 520 }
                NumberAnimation { target: r0; property: "opacity"; to: 0.12; duration: 520 }
                NumberAnimation { target: r1; property: "opacity"; to: 0.12; duration: 520 }
                NumberAnimation { target: conn1; property: "opacity"; to: 0; duration: 520 }
                NumberAnimation { target: conn2; property: "opacity"; to: 0; duration: 520 }
            }
            ParallelAnimation {
                NumberAnimation { target: zRes; property: "opacity"; to: 1; duration: 420 }
                NumberAnimation { target: zNoise; property: "opacity"; to: 1; duration: 420 }
            }
        }

        // ⑥ Threshold：marker 移动到真实 z_centered
        NumberAnimation {
            id: markerAnim
            target: marker; property: "x"
            to: root.nlPos(root.zFrac()) - 9
            duration: 900; easing.type: Easing.InOutCubic
        }
    }

    // ================= 步骤驱动 =================
    function resetCancellation() {
        lHead.opacity = 0; l0.opacity = 0; l1.opacity = 0; l2.opacity = 0; l3.opacity = 0
        rHead.opacity = 0; r0.opacity = 0; r1.opacity = 0; r2.opacity = 0
        zRes.opacity = 0; zNoise.opacity = 0
        conn1.opacity = 0; conn2.opacity = 0
    }

    function enterStep(s) {
        stage.state = "s" + s
        if (s === 1) wsAnim.restart()
        if (s === 3) y2Anim.restart()
        if (s === 4) { resetCancellation(); cancellationAnim.restart() }
        if (s === 5) { marker.x = root.nlPos(0) - 9; markerAnim.restart() }
    }

    Connections {
        target: ctrl
        function onStepChanged() { root.enterStep(ctrl.step) }
        function onReplayRequested() { root.enterStep(ctrl.step) }
    }

    Component.onCompleted: { ctrl.reset(); root.enterStep(0) }

    // ================= 右栏 =================
    CodePanel { x: 1048; y: 16; width: 376; height: 400 }
    FormulaPanel { x: 1048; y: 428; width: 376; height: 288 }

    // ================= 控制（只手动推进） =================
    StepControls {
        x: 16; y: 724; width: 1408; height: 60
        onPreviousClicked: ctrl.previous()
        onAnimateClicked: ctrl.animateStep()
        onNextClicked: ctrl.next()
        onResetClicked: ctrl.reset()
    }
}
