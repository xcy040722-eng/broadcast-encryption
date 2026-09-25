"""Defense-oriented principle/status inspector for the SM2 + SM4 workbench.

The inspector explains one visible cryptographic object at a time.  It is fed
only safe UI projections (SessionSnapshot and ReceiverCanvasState); it never
receives the raw SM4 content key or SM2 private-key bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from src.sm2_sm4_mre.interactive_session import SessionSnapshot

from .i18n import Translator
from .receiver_canvas import ReceiverCanvasState


@dataclass(frozen=True)
class TopicSpec:
    title_zh: str
    title_en: str
    role_zh: str
    role_en: str
    formula: str
    input_zh: str
    input_en: str
    output_zh: str
    output_en: str
    boundary_zh: str
    boundary_en: str


_TOPICS: dict[str, TopicSpec] = {
    "key": TopicSpec(
        "SM4 内容密钥 K",
        "SM4 content key K",
        "每次广播只生成一次的 128-bit 对称密钥；同一个 K 同时用于媒体加密，并被分别封装给授权接收者。",
        "A fresh 128-bit symmetric key generated once per broadcast; the same K encrypts the media and is wrapped separately for authorized recipients.",
        "K ← {0,1}^128",
        "密码学安全随机数生成器",
        "cryptographically secure random generator",
        "会话内容密钥 K（UI 仅显示 SM3 指纹）",
        "session content key K (UI shows only its SM3 fingerprint)",
        "原始 K 不进入默认 trace、画布或广播包明文；广播包只保存各接收者的 SM2 密钥封装。",
        "Raw K is not exposed by the default trace/canvas or stored in plaintext in the package; only SM2-wrapped copies are packaged.",
    ),
    "media": TopicSpec(
        "媒体明文 M",
        "Media plaintext M",
        "待保护的图片、视频或普通文件。媒体主体只执行一次 SM4-GCM 加密。",
        "The image, video, or file being protected. The payload is encrypted exactly once with SM4-GCM.",
        "M → SM4-GCM(K, IV, AAD)",
        "原始媒体文件 M",
        "original media file M",
        "媒体密文 C_M 与认证标签 T",
        "media ciphertext C_M and authentication tag T",
        "系统采用流式处理，不要求把整个大文件一次性读入内存。",
        "The implementation streams the payload and does not require loading a large file into memory at once.",
    ),
    "engine": TopicSpec(
        "SM4-GCM 媒体加密",
        "SM4-GCM media encryption",
        "用同一个会话密钥 K 对媒体做认证加密，同时提供机密性与完整性。",
        "Authenticated encryption of the media with the same session key K, providing confidentiality and integrity.",
        "(C_M, T) = SM4-GCM.Enc(K, IV, M, AAD)",
        "K、IV、媒体 M、AAD",
        "K, IV, media M, and AAD",
        "媒体密文 C_M 与认证标签 T",
        "media ciphertext C_M and authentication tag T",
        "错误密钥或被篡改的密文不能通过 GCM 认证；明文仅在认证成功后释放。",
        "A wrong key or tampered ciphertext fails GCM authentication; plaintext is released only after authentication succeeds.",
    ),
    "package": TopicSpec(
        "广播包 .smre",
        "Broadcast package .smre",
        "把 manifest、授权集合中每个用户的 SM2 密钥封装以及唯一一份媒体密文组合成同一个广播对象。",
        "Combines the manifest, one SM2-wrapped key per authorized recipient, and one encrypted media payload into a single broadcast object.",
        "P = manifest ∥ {E_i}_{i∈S} ∥ C_M",
        "manifest、E_i、C_M",
        "manifest, E_i values, and C_M",
        "所有用户收到的同一份 .smre 广播包",
        "the same .smre package delivered to all users",
        "媒体不会按接收者重复加密；随接收者数量增长的是密钥封装头部。",
        "The media is not re-encrypted per recipient; only the wrapped-key header grows with the recipient set.",
    ),
    "recipient": TopicSpec(
        "SM2 密钥封装 E[i]",
        "SM2 wrapped key E[i]",
        "发送者使用接收者 i 的 SM2 公钥封装包含 K 的 KeyEnvelope。",
        "The sender uses recipient i's SM2 public key to wrap a KeyEnvelope containing K.",
        "E_i = SM2.Enc(PK_i, Envelope(package_id, i, K))",
        "PK_i、package_id、user_id=i、K",
        "PK_i, package_id, user_id=i, and K",
        "仅属于接收者 i 的密钥封装 E_i",
        "wrapped key E_i bound to recipient i",
        "Envelope 同时绑定 package_id 与 user_id，防止把合法封装错误地移植到其他包或用户。",
        "The envelope binds both package_id and user_id, preventing a valid wrapped key from being transplanted to another package or user.",
    ),
    "receiver:sk": TopicSpec(
        "接收者 SM2 私钥 SK[i]",
        "Receiver SM2 private key SK[i]",
        "用户本地持有的 SM2 私钥，仅用于解开属于自己的密钥封装。",
        "The user's local SM2 private key, used only to unwrap the wrapped content key intended for that user.",
        "SK_i + E_i → SM2.Dec → Envelope_i",
        "口令保护的 SM2 私钥文件与 E_i",
        "password-protected SM2 private key file and E_i",
        "解出的 KeyEnvelope，或密码学失败",
        "decoded KeyEnvelope, or a cryptographic failure",
        "画布只显示 SK[i] 这一逻辑对象，从不显示 PEM 私钥正文。",
        "The canvas shows only the logical SK[i] object and never the private-key PEM body.",
    ),
    "receiver:wrapped": TopicSpec(
        "接收端密钥封装 E[target]",
        "Receiver wrapped key E[target]",
        "广播包中为某个目标接收者保存的 SM2 密文。正常解密时 target=user；force-try 时可故意选择别人的 E[target]。",
        "The SM2 ciphertext stored for a target recipient. In normal decryption target=user; a force-try deliberately chooses another user's E[target].",
        "E_target = SM2.Enc(PK_target, Envelope_target)",
        "广播包中的 wrapped-key entry",
        "wrapped-key entry from the package",
        "交给 SM2 解封步骤的密文",
        "ciphertext input to SM2 unwrap",
        "UI 只显示 E[target] 的指纹，不显示内部 K。",
        "The UI shows only an E[target] fingerprint and never the embedded K.",
    ),
    "receiver:unwrap": TopicSpec(
        "SM2 解封",
        "SM2 unwrap",
        "使用接收者私钥真实执行 SM2 解密，然后验证 KeyEnvelope 的 package_id 与 user_id 绑定。",
        "Performs real SM2 decryption with the receiver private key, then validates the KeyEnvelope package_id and user_id binding.",
        "Envelope = SM2.Dec(SK_i, E_target)",
        "SK_i 与 E_target",
        "SK_i and E_target",
        "恢复 K，或 SM2_UNWRAP_FAILED / ENVELOPE_MISMATCH",
        "recovered K, or SM2_UNWRAP_FAILED / ENVELOPE_MISMATCH",
        "错误私钥通常在 native SM2 解密处直接失败；后续 K 和 GCM 步骤不会被伪造为成功。",
        "A wrong private key normally fails in native SM2 decryption; later K/GCM stages are not fabricated as successful.",
    ),
    "receiver:key": TopicSpec(
        "恢复的内容密钥 K",
        "Recovered content key K",
        "授权用户从自己的 KeyEnvelope 中恢复出的同一个会话密钥 K。",
        "The same session content key K recovered by an authorized user from their KeyEnvelope.",
        "K_receiver = DecodeEnvelope(SM2.Dec(SK_i, E_i)).K",
        "已验证的 KeyEnvelope",
        "validated KeyEnvelope",
        "供 SM4-GCM 解密使用的 K",
        "K used for SM4-GCM decryption",
        "只显示 SM3 指纹，用于证明发送端 K 与接收端恢复 K 一致，而不泄露密钥本身。",
        "Only an SM3 fingerprint is shown so sender/receiver key equality can be demonstrated without exposing the key itself.",
    ),
    "receiver:gcm": TopicSpec(
        "SM4-GCM 解密与认证",
        "SM4-GCM decryption and authentication",
        "接收者使用恢复的 K、manifest 中的 IV/AAD 对媒体密文做真实解密和认证。",
        "The receiver uses recovered K plus IV/AAD from the manifest to perform real media decryption and authentication.",
        "M = SM4-GCM.Dec(K, IV, C_M, T, AAD)",
        "K、IV、AAD、C_M、T",
        "K, IV, AAD, C_M, and T",
        "认证成功后的明文 M，或 GCM_AUTH_FAILED",
        "authenticated plaintext M, or GCM_AUTH_FAILED",
        "实现先写入临时文件，只有 GCM 认证成功后才原子释放最终明文。",
        "The implementation writes to a temporary file and releases the final plaintext atomically only after GCM authentication succeeds.",
    ),
}


class PrincipleInspector(QWidget):
    """Explain a selected visual object using only non-secret session state."""

    def __init__(self, i18n: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.topic: str | None = None
        self._last_snapshot: SessionSnapshot | None = None
        self._last_receiver = ReceiverCanvasState()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.title = QLabel(self._choose("密码学原理与本次状态", "Cryptographic principle & live state"))
        self.title.setObjectName("objectTitle")
        layout.addWidget(self.title)

        self.help = QLabel(
            self._choose(
                "点击“关系图”或“接收端路径”中的对象，这里会解释它的角色、输入、输出、公式以及本次真实状态。",
                "Click an object in Object graph or Receiver path to inspect its role, inputs, outputs, formula, and live state.",
            )
        )
        self.help.setObjectName("muted")
        self.help.setWordWrap(True)
        layout.addWidget(self.help)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        layout.addWidget(self.browser, 1)
        self._render_idle()

    def _choose(self, zh: str, en: str) -> str:
        return zh if self.i18n.language == "zh_CN" else en

    def clear(self) -> None:
        self.topic = None
        self._render_idle()

    def show_topic(
        self,
        topic: str,
        *,
        snapshot: SessionSnapshot,
        receiver_state: ReceiverCanvasState | None = None,
    ) -> None:
        normalized = "recipient" if topic.startswith("recipient:") else topic
        if normalized not in _TOPICS:
            raise KeyError(f"unknown principle topic {topic!r}")
        self.topic = topic
        self._last_snapshot = snapshot
        self._last_receiver = receiver_state or ReceiverCanvasState()
        self._render()

    def refresh_state(
        self,
        *,
        snapshot: SessionSnapshot,
        receiver_state: ReceiverCanvasState | None = None,
    ) -> None:
        self._last_snapshot = snapshot
        self._last_receiver = receiver_state or self._last_receiver
        if self.topic:
            self._render()

    def _render_idle(self) -> None:
        text = self._choose(
            "<h3>选择一个密码学对象</h3><p>这里不会显示原始 SM4 K 或 SM2 私钥，只展示公式、指纹和真实后端状态。</p>",
            "<h3>Select a cryptographic object</h3><p>This panel never shows raw SM4 K or SM2 private keys; it shows formulas, fingerprints, and real backend state.</p>",
        )
        self.browser.setHtml(text)

    def _render(self) -> None:
        assert self.topic is not None
        assert self._last_snapshot is not None
        base = "recipient" if self.topic.startswith("recipient:") else self.topic
        spec = _TOPICS[base]
        zh = self.i18n.language == "zh_CN"
        title = spec.title_zh if zh else spec.title_en
        role = spec.role_zh if zh else spec.role_en
        inputs = spec.input_zh if zh else spec.input_en
        outputs = spec.output_zh if zh else spec.output_en
        boundary = spec.boundary_zh if zh else spec.boundary_en
        state = self._live_state(self.topic, self._last_snapshot, self._last_receiver)

        labels = {
            "role": "作用" if zh else "Role",
            "inputs": "输入" if zh else "Inputs",
            "operation": "核心关系 / 运算" if zh else "Core relation / operation",
            "outputs": "输出" if zh else "Outputs",
            "state": "本次真实状态" if zh else "Live state",
            "boundary": "安全边界" if zh else "Security boundary",
        }
        html = f"""
        <h2>{escape(title)}</h2>
        <p><b>{labels['role']}：</b>{escape(role)}</p>
        <p><b>{labels['inputs']}：</b>{escape(inputs)}</p>
        <p><b>{labels['operation']}：</b><code>{escape(spec.formula)}</code></p>
        <p><b>{labels['outputs']}：</b>{escape(outputs)}</p>
        <hr/>
        <p><b>{labels['state']}：</b>{escape(state)}</p>
        <p><b>{labels['boundary']}：</b>{escape(boundary)}</p>
        """
        self.browser.setHtml(html)

    def _live_state(
        self,
        topic: str,
        snap: SessionSnapshot,
        receiver: ReceiverCanvasState,
    ) -> str:
        zh = self.i18n.language == "zh_CN"
        yes, no = (("是", "否") if zh else ("yes", "no"))
        if topic == "key":
            return (
                (f"已生成；SM3 指纹 {snap.content_key_fingerprint}" if zh else f"generated; SM3 fingerprint {snap.content_key_fingerprint}")
                if snap.content_key_fingerprint
                else ("尚未生成" if zh else "not generated")
            )
        if topic == "media":
            return snap.input_path or ("尚未选择媒体" if zh else "no media selected")
        if topic == "engine":
            if snap.payload_path:
                return (
                    f"媒体密文已生成；payload={snap.payload_size} 字节；本次加密次数={snap.payload_encryption_count}"
                    if zh
                    else f"payload ready; {snap.payload_size} bytes; encryption_count={snap.payload_encryption_count}"
                )
            return "等待执行 SM4-GCM" if zh else "waiting for SM4-GCM"
        if topic == "package":
            if snap.package_path:
                return (f"已组装：{snap.package_path}" if zh else f"assembled: {snap.package_path}")
            return (
                f"是否具备组装条件：{yes if snap.stage.value == 'READY_TO_ASSEMBLE' else no}"
                if zh
                else f"ready to assemble: {yes if snap.stage.value == 'READY_TO_ASSEMBLE' else no}"
            )
        if topic.startswith("recipient:"):
            user = topic.split(":", 1)[1]
            fp = snap.wrapped_key_fingerprints.get(user)
            if fp:
                return (f"E[{user}] 已生成；指纹 {fp}" if zh else f"E[{user}] generated; fingerprint {fp}")
            return (f"E[{user}] 尚未生成" if zh else f"E[{user}] not generated")
        if topic == "receiver:sk":
            return (
                f"当前用户 {receiver.user_id or '-'}；画布不读取私钥正文"
                if zh
                else f"current user {receiver.user_id or '-'}; private-key bytes are never read by the canvas"
            )
        if topic == "receiver:wrapped":
            return (
                f"目标 {receiver.target_recipient_id or '-'}；指纹 {receiver.wrapped_key_fingerprint or '-'}"
                if zh
                else f"target {receiver.target_recipient_id or '-'}; fingerprint {receiver.wrapped_key_fingerprint or '-'}"
            )
        if topic == "receiver:unwrap":
            return (
                f"后端状态 {receiver.status or '-'}；恢复 K 指纹 {receiver.content_key_fingerprint or '-'}"
                if zh
                else f"backend status {receiver.status or '-'}; recovered-K fingerprint {receiver.content_key_fingerprint or '-'}"
            )
        if topic == "receiver:key":
            return (
                f"恢复 K 指纹 {receiver.content_key_fingerprint or '-'}"
                if zh
                else f"recovered-K fingerprint {receiver.content_key_fingerprint or '-'}"
            )
        if topic == "receiver:gcm":
            auth = receiver.gcm_authenticated
            auth_text = "未到达" if auth is None and zh else "not reached" if auth is None else yes if auth else no
            return (
                f"GCM 认证={auth_text}；输出 {receiver.output_name or '-'}"
                if zh
                else f"GCM authenticated={auth_text}; output {receiver.output_name or '-'}"
            )
        return "-"
