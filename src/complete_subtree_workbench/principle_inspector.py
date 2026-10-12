"""Defense-oriented principle/live-state inspector for Complete Subtree.

The inspector consumes only CsSessionSnapshot and a safe receiver projection.
It never receives raw node keys L_i or the raw broadcast content key K.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.complete_subtree_mre.interactive_session import CsSessionSnapshot
from src.complete_subtree_mre.types import CsRecoverResult

from .i18n import Translator


@dataclass(frozen=True)
class CsReceiverState:
    mode: str | None = None
    user_id: int | None = None
    status: str | None = None
    path_nodes: tuple[int, ...] = ()
    matched_node_id: int | None = None
    attempted_key_node_id: int | None = None
    header_fingerprint: str | None = None
    content_key_fingerprint: str | None = None

    @classmethod
    def from_result(cls, result: CsRecoverResult, *, mode: str) -> "CsReceiverState":
        trace = result.trace
        return cls(
            mode=mode,
            user_id=trace.user_id,
            status=result.status.value,
            path_nodes=trace.user_path_nodes,
            matched_node_id=trace.matched_node_id,
            attempted_key_node_id=trace.attempted_key_node_id,
            header_fingerprint=trace.header_fingerprint,
            content_key_fingerprint=trace.content_key_fingerprint,
        )


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
    "revocation": TopicSpec(
        "撤销集合 R",
        "Revocation set R",
        "本次广播中被排除的接收者集合。Complete Subtree 从 R 出发计算 Steiner Tree 与非撤销用户覆盖。",
        "The receivers excluded from this broadcast. Complete Subtree derives the Steiner tree and non-revoked cover from R.",
        "R ⊆ U",
        "全体用户 U 与本次撤销选择",
        "user universe U and the current revocation choice",
        "撤销集合 R",
        "revocation set R",
        "撤销集合只是算法输入；真正阻止撤销用户恢复 K 的是后续 Cover 与路径密钥关系。",
        "R is an algorithm input; actual denial comes from the later Cover/path-key relationship, not a UI-only check.",
    ),
    "steiner": TopicSpec(
        "Steiner Tree ST(R)",
        "Steiner tree ST(R)",
        "连接根节点与所有撤销用户叶子的最小树；它标记了不能直接作为授权覆盖子树使用的路径。",
        "The minimal tree connecting the root to every revoked leaf; it marks paths that cannot themselves serve as authorized cover subtrees.",
        "ST(R) = ⋃_{u∈R} Path(root, u)",
        "撤销集合 R 与用户叶节点",
        "revocation set R and user leaves",
        "Steiner Tree 节点集合",
        "the Steiner-tree node set",
        "ST(R) 不包含任何秘密，只描述树结构；节点长期密钥 L_i 从不显示。",
        "ST(R) contains no secret material; it describes only tree structure, and long-lived node keys L_i are never displayed.",
    ),
    "cover": TopicSpec(
        "Complete Subtree Cover",
        "Complete Subtree Cover",
        "选择挂在 ST(R) 之外的完整子树，使它们互不相交并恰好覆盖所有非撤销用户。",
        "Select complete subtrees hanging off ST(R) so they are disjoint and cover exactly all non-revoked users.",
        "Cover(R) = {S_v : v hangs off ST(R)}",
        "ST(R) 与完整二叉树",
        "ST(R) and the full binary tree",
        "Cover 根节点集合与 U \\ R 的划分",
        "cover roots and a partition of U \\ R",
        "撤销用户不属于任何 Cover 子树，因此其根到叶路径不会命中 Header 中的 Cover 节点。",
        "A revoked user belongs to no Cover subtree, so its root-to-leaf path matches no Cover node represented in the Header.",
    ),
    "nodekey": TopicSpec(
        "节点长期密钥 L[i]",
        "Long-lived node key L[i]",
        "每个树节点独立持有一把长期对称密钥；用户只获得自己根到叶路径上的节点密钥。",
        "Every tree node owns an independent long-lived symmetric key; a receiver obtains only keys on its root-to-leaf path.",
        "L_i ← {0,1}^128",
        "GmSSL 安全随机源与节点 v_i",
        "GmSSL secure randomness and node v_i",
        "节点密钥 L_i（UI 不显示原值）",
        "node key L_i (raw value is never shown)",
        "CsSessionSnapshot 与 CsRecoverTrace 只暴露节点编号和状态，不包含任何 L_i 字节。",
        "CsSessionSnapshot and CsRecoverTrace expose node IDs and state only; no L_i bytes are present.",
    ),
    "key": TopicSpec(
        "广播内容密钥 K",
        "Broadcast content key K",
        "每次广播新生成一次的 128-bit 内容/会话密钥；所有授权用户最终恢复同一个 K。",
        "A fresh 128-bit content/session key generated once per broadcast; every authorized receiver ultimately recovers the same K.",
        "K ← {0,1}^128",
        "GmSSL 安全随机源",
        "GmSSL secure random generator",
        "广播内容密钥 K（UI 仅显示 SM3 指纹）",
        "broadcast content key K (UI shows only its SM3 fingerprint)",
        "原始 K 只保留在后端会话内部；默认 UI、Snapshot 和 Trace 均不显示。",
        "Raw K remains inside the backend session and is never exposed by the default UI, Snapshot, or Trace.",
    ),
    "header": TopicSpec(
        "Cover Header 条目 E[L_i](K)",
        "Cover header entry E[L_i](K)",
        "使用 Cover 根节点长期密钥 L_i 对包含 package_id、node_id 与 K 的 Envelope 做真实 SM4-GCM 认证加密。",
        "Uses the Cover-root key L_i to perform real SM4-GCM authenticated encryption of an envelope containing package_id, node_id, and K.",
        "H_i = SM4-GCM.Enc(L_i, IV_i, Envelope(package_id, i, K), AAD_i)",
        "Cover 根节点密钥 L_i、package_id、node_id=i、K",
        "Cover-root key L_i, package_id, node_id=i, and K",
        "Header 条目 E[L_i](K)",
        "header entry E[L_i](K)",
        "每个条目使用独立 IV，并通过 AAD/Envelope 绑定 package_id 与 node_id；UI 只显示 Header 指纹。",
        "Each entry uses its own IV and binds package_id/node_id through AAD and the envelope; the UI shows only a header fingerprint.",
    ),
    "receiver": TopicSpec(
        "接收者路径与 K 恢复",
        "Receiver path and K recovery",
        "接收者沿根到叶路径查找唯一 Cover 根；命中后使用自己持有的 L_i 解开对应 Header。撤销用户没有命中节点。",
        "The receiver searches its root-to-leaf path for the unique Cover root, then uses its L_i to unwrap that Header. A revoked receiver has no match.",
        "v* = Path(u) ∩ Cover;  K = Dec_{L_v*}(H_v*)",
        "接收者路径密钥集合与 Complete Subtree Header",
        "receiver path-key set and Complete Subtree Header",
        "SUCCESS + K，或 REVOKED / HEADER_UNWRAP_FAILED",
        "SUCCESS + K, or REVOKED / HEADER_UNWRAP_FAILED",
        "正常接收只读取安全 Trace；force-try 会真实调用 GmSSL SM4-GCM，用错误路径密钥时认证失败。",
        "Normal receiving exposes only a safe trace; force-try invokes real GmSSL SM4-GCM and a wrong path key fails authentication.",
    ),
}


class CompleteSubtreePrincipleInspector(QWidget):
    """Explain Complete Subtree objects from safe live state only."""

    topicRequested = Signal(str)

    def __init__(self, i18n: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.topic: str | None = None
        self._snapshot: CsSessionSnapshot | None = None
        self._receiver = CsReceiverState()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel(self._choose("密码学原理与本次状态", "Cryptographic principle & live state"))
        title.setObjectName("objectTitle")
        layout.addWidget(title)

        help_text = QLabel(
            self._choose(
                "点击下面的对象，或点击关系图中的节点，查看算法角色、公式和本次真实状态。",
                "Choose an object below, or click a tree node, to inspect its role, formula, and live state.",
            )
        )
        help_text.setObjectName("muted")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        shortcuts = QHBoxLayout()
        shortcut_topics = (
            ("revocation", "R"),
            ("steiner", "ST(R)"),
            ("cover", "Cover"),
            ("key", "K"),
            ("receiver", self._choose("接收路径", "Receiver path")),
        )
        for topic, label in shortcut_topics:
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, t=topic: self.request_topic(t))
            shortcuts.addWidget(button)
        shortcuts.addStretch(1)
        layout.addLayout(shortcuts)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        layout.addWidget(self.browser, 1)
        self._render_idle()

    def _choose(self, zh: str, en: str) -> str:
        return zh if self.i18n.language == "zh_CN" else en

    def set_state(
        self,
        *,
        snapshot: CsSessionSnapshot,
        receiver: CsReceiverState | None = None,
    ) -> None:
        self._snapshot = snapshot
        if receiver is not None:
            self._receiver = receiver
        if self.topic is not None:
            self._render()

    def clear(self) -> None:
        self.topic = None
        self._receiver = CsReceiverState()
        self._render_idle()

    def request_topic(self, topic: str) -> None:
        self.topicRequested.emit(topic)
        if self._snapshot is not None:
            self.show_topic(topic, snapshot=self._snapshot, receiver=self._receiver)

    def show_topic(
        self,
        topic: str,
        *,
        snapshot: CsSessionSnapshot,
        receiver: CsReceiverState | None = None,
    ) -> None:
        base = self._base_topic(topic)
        if base not in _TOPICS:
            raise KeyError(f"unknown Complete Subtree principle topic {topic!r}")
        self.topic = topic
        self._snapshot = snapshot
        if receiver is not None:
            self._receiver = receiver
        self._render()

    @staticmethod
    def _base_topic(topic: str) -> str:
        if ":" in topic:
            return topic.split(":", 1)[0]
        return topic

    @staticmethod
    def _topic_node(topic: str) -> int | None:
        if ":" not in topic:
            return None
        try:
            return int(topic.split(":", 1)[1])
        except ValueError:
            return None

    def _render_idle(self) -> None:
        self.browser.setHtml(
            self._choose(
                "<h3>选择一个 Complete Subtree 对象</h3>"
                "<p>这里不会显示原始 K 或任何节点长期密钥 L_i，只展示公式、SM3 指纹和真实后端状态。</p>",
                "<h3>Select a Complete Subtree object</h3>"
                "<p>This panel never shows raw K or long-lived node keys L_i; it shows formulas, SM3 fingerprints, and real backend state.</p>",
            )
        )

    def _render(self) -> None:
        assert self.topic is not None
        assert self._snapshot is not None
        base = self._base_topic(self.topic)
        spec = _TOPICS[base]
        zh = self.i18n.language == "zh_CN"
        title = spec.title_zh if zh else spec.title_en
        node = self._topic_node(self.topic)
        if node is not None and base in {"nodekey", "header", "cover", "steiner"}:
            title += f" · v{node}"
        role = spec.role_zh if zh else spec.role_en
        inputs = spec.input_zh if zh else spec.input_en
        outputs = spec.output_zh if zh else spec.output_en
        boundary = spec.boundary_zh if zh else spec.boundary_en
        state = self._live_state(self.topic, self._snapshot, self._receiver)

        labels = {
            "role": "作用" if zh else "Role",
            "inputs": "输入" if zh else "Inputs",
            "operation": "核心关系 / 运算" if zh else "Core relation / operation",
            "outputs": "输出" if zh else "Outputs",
            "state": "本次真实状态" if zh else "Live state",
            "boundary": "安全边界" if zh else "Security boundary",
        }
        sep = "：" if zh else ": "
        self.browser.setHtml(
            f"""
            <h2>{escape(title)}</h2>
            <p><b>{labels['role']}{sep}</b>{escape(role)}</p>
            <p><b>{labels['inputs']}{sep}</b>{escape(inputs)}</p>
            <p><b>{labels['operation']}{sep}</b><code>{escape(spec.formula)}</code></p>
            <p><b>{labels['outputs']}{sep}</b>{escape(outputs)}</p>
            <hr/>
            <p><b>{labels['state']}{sep}</b>{escape(state)}</p>
            <p><b>{labels['boundary']}{sep}</b>{escape(boundary)}</p>
            """
        )

    def _live_state(
        self,
        topic: str,
        snap: CsSessionSnapshot,
        receiver: CsReceiverState,
    ) -> str:
        zh = self.i18n.language == "zh_CN"
        base = self._base_topic(topic)
        node = self._topic_node(topic)

        def nodes(values: tuple[int, ...]) -> str:
            return "{" + ",".join(f"v{i}" for i in values) + "}"

        def users(values: tuple[int, ...]) -> str:
            return "{" + ",".join(f"u{i}" for i in values) + "}"

        if base == "revocation":
            return (
                f"R={users(snap.revoked_users)}"
                if snap.revoked_users
                else ("R=∅，尚未选择撤销用户" if zh else "R=∅; no revoked users selected")
            )
        if base == "steiner":
            if not snap.steiner_nodes:
                return "尚未计算 ST(R)" if zh else "ST(R) not computed yet"
            suffix = f"；当前点击 v{node}" if zh and node else f"; selected v{node}" if node else ""
            return f"ST(R)={nodes(snap.steiner_nodes)}{suffix}"
        if base == "cover":
            if not snap.cover_roots:
                return "尚未计算 Cover" if zh else "Cover not computed yet"
            suffix = f"；当前点击 v{node}" if zh and node else f"; selected v{node}" if node else ""
            if zh:
                return f"Cover={nodes(snap.cover_roots)}；覆盖用户={users(snap.covered_users)}{suffix}"
            return f"Cover={nodes(snap.cover_roots)}; covered users={users(snap.covered_users)}{suffix}"
        if base == "nodekey":
            if node is None:
                return "-"
            memberships: list[str] = []
            if node in snap.steiner_nodes:
                memberships.append("ST(R)")
            if node in snap.cover_roots:
                memberships.append("Cover")
            if node in snap.wrapped_nodes:
                memberships.append("Header")
            label = ", ".join(memberships) if memberships else ("普通树节点" if zh else "ordinary tree node")
            return (
                f"v{node}；状态={label}；L[{node}] 原值不显示"
                if zh
                else f"v{node}; state={label}; raw L[{node}] is hidden"
            )
        if base == "key":
            if snap.content_key_fingerprint:
                return (
                    f"已生成；SM3 指纹 {snap.content_key_fingerprint}"
                    if zh
                    else f"generated; SM3 fingerprint {snap.content_key_fingerprint}"
                )
            return "尚未生成" if zh else "not generated"
        if base == "header":
            if node is None:
                return "-"
            fp = snap.header_fingerprints.get(node)
            if fp:
                return (
                    f"E[L{node}](K) 已生成；Header 指纹 {fp}"
                    if zh
                    else f"E[L{node}](K) generated; header fingerprint {fp}"
                )
            return (
                f"v{node} 尚未生成 Header 条目"
                if zh
                else f"no header entry has been generated for v{node}"
            )
        if base == "receiver":
            if receiver.user_id is None:
                return "尚未执行接收端验证" if zh else "receiver verification has not run"
            path = nodes(receiver.path_nodes)
            if zh:
                return (
                    f"模式={receiver.mode or '-'}；用户=u{receiver.user_id}；状态={receiver.status or '-'}；"
                    f"路径={path}；命中节点={f'v{receiver.matched_node_id}' if receiver.matched_node_id else '-'}；"
                    f"尝试密钥节点={f'v{receiver.attempted_key_node_id}' if receiver.attempted_key_node_id else '-'}；"
                    f"恢复 K 指纹={receiver.content_key_fingerprint or '-'}"
                )
            return (
                f"mode={receiver.mode or '-'}; user=u{receiver.user_id}; status={receiver.status or '-'}; "
                f"path={path}; matched node={f'v{receiver.matched_node_id}' if receiver.matched_node_id else '-'}; "
                f"attempted key node={f'v{receiver.attempted_key_node_id}' if receiver.attempted_key_node_id else '-'}; "
                f"recovered-K fingerprint={receiver.content_key_fingerprint or '-'}"
            )
        return "-"
