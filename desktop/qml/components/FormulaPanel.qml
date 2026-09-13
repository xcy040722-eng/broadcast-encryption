import QtQuick

// FormulaPanel：当前步骤的**核心公式**（辅助说明）；真实数值来自 trace。
Rectangle {
    id: fp
    color: "#141b2b"
    radius: 10
    border.color: "#223052"
    border.width: 1

    property int step: ctrl.step
    property var tr: ctrl.trace
    property var ct: ctrl.ct
    property int mu: ctrl.mu
    property int focusUser: ctrl.focusUser

    Column {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 5

        Text {
            text: ["Select S", "Build W_S", "Build Ciphertext", "Build Y_2",
                   "Cancellation", "Threshold"][fp.step]
            color: "#7fb3ff"; font.pixelSize: 13; font.bold: true; font.family: "Consolas"
        }
        Rectangle { width: parent.width; height: 1; color: "#223052" }

        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: "#cfe3ff"
            font.pixelSize: 12
            font.family: "Consolas"
            lineHeight: 1.35
            text: {
                switch (fp.step) {
                case 0: return "S = {" + ctrl.recipients.join(", ") + "}"
                case 1: return "W_S = " + ctrl.ct.WS_parts.map(function (j) { return "W" + j }).join(" + ")
                                + "\nfp " + ctrl.ct.WS_fp
                case 2: return "c1 = s^T A + e^T\nc2 = s^T (W0+W_S) + e^T K_W\nc3 = s^T p + e^T k_p + mu*floor(q/2)"
                                + "\n\nc1[0]=" + ctrl.ct.c1_0 + "  c2[0]=" + ctrl.ct.c2_0 + "  c3=" + ctrl.ct.c3
                case 3: return "Y" + fp.focusUser + " = y" + fp.focusUser + fp.focusUser
                                + " + y0" + fp.focusUser + " + y4" + fp.focusUser
                                + "\n\nc1^T Y = " + fp.tr.c1_term_total
                case 4: return "L = c3 + c2^T r" + fp.focusUser + "   =  " + (fp.tr.c3 + fp.tr.c2_dot_r_i)
                                + "\nR = c1^T Y" + fp.focusUser + "   =  " + fp.tr.c1_term_total
                                + "\n\nz = " + fp.tr.z_centered + "   noise = " + fp.tr.noise_residual
                case 5: return "q/4 threshold = " + fp.tr.threshold
                                + "\nz_centered = " + fp.tr.z_centered
                                + "\n\nmu = " + fp.tr.decoded_mu + "   (encrypted mu = " + fp.mu + ")"
                }
                return ""
            }
        }

        Item { width: 1; height: 6 }

        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            color: "#8b9bb4"
            font.pixelSize: 11
            font.family: "Consolas"
            text: "q=" + ctrl.params.q + "  floor(q/2)=" + ctrl.params.half_q
                  + "\nparams_id " + ctrl.paramsId + "\nkeyset_id " + ctrl.keysetId.substring(0, 12) + "..."
        }
    }
}
