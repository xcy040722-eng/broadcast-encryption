"""Unified PySide6 launcher for the two course-project cryptography modules."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.complete_subtree_workbench.window import CompleteSubtreeWorkbenchWindow
from src.sm2_sm4_workbench.defense_workbench import DefenseWorkbenchWindow
from src.sm2_sm4_workbench.window import LIGHT_STYLE


class BroadcastEncryptionLauncher(QMainWindow):
    """Single entry point for the two verified teaching workbenches."""

    def __init__(
        self,
        *,
        language: str = "zh_CN",
        workspace: Path | None = None,
        cs_users: int = 8,
    ) -> None:
        super().__init__()
        if language not in {"zh_CN", "en_US"}:
            raise ValueError(f"unsupported language: {language}")
        if cs_users < 1 or (cs_users & (cs_users - 1)) != 0:
            raise ValueError("cs_users must be a positive power of two")

        self.language = language
        self.workspace = (
            Path(workspace)
            if workspace is not None
            else Path.home() / ".broadcast-encryption-workbench" / "sm2-sm4"
        )
        self.cs_users = cs_users
        self._children: list[QMainWindow] = []

        self.setWindowTitle(
            self._t("广播加密与多接收者密码工作台", "Broadcast Encryption & Multi-Recipient Cryptography Workbench")
        )
        self.resize(1120, 690)
        self.setStyleSheet(LIGHT_STYLE)
        self._build_ui()

    def _t(self, zh: str, en: str) -> str:
        return zh if self.language == "zh_CN" else en

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel(
            self._t(
                "广播加密与多接收者密码工作台",
                "Broadcast Encryption & Multi-Recipient Cryptography Workbench",
            )
        )
        title.setStyleSheet("font-size:26px;font-weight:700;")
        root.addWidget(title)

        subtitle = QLabel(
            self._t(
                "统一入口 · Complete Subtree 经典广播撤销 + SM2/SM4 多接收者混合加密",
                "Unified entry · Complete Subtree revocation + SM2/SM4 multi-recipient hybrid encryption",
            )
        )
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        note = QLabel(
            self._t(
                "两个模块共享 PySide6、GmSSL、SM3 安全指纹、状态驱动会话与可解释演示层；"
                "算法模型保持独立，便于在答辩中比较“树型共享密钥撤销”和“用户公钥独立封装”两种思路。",
                "Both modules share PySide6, GmSSL, SM3 safe fingerprints, state-driven sessions, "
                "and explainable demo layers while keeping their cryptographic models distinct for comparison.",
            )
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "background:#FFF9E8;color:#6B541A;border:1px solid #E7D59B;"
            "border-radius:8px;padding:9px 12px;"
        )
        root.addWidget(note)

        cards = QHBoxLayout()
        cards.setSpacing(18)
        cards.addWidget(self._module_card(
            object_name="completeSubtreeCard",
            title=self._t("Complete Subtree", "Complete Subtree"),
            badge=self._t("经典广播撤销", "Classic broadcast revocation"),
            description=self._t(
                "基于 NNL01 Complete Subtree：从撤销集合 R 计算 ST(R) 与 Cover，"
                "使用树节点长期密钥 L_i 保护同一个广播内容密钥 K。",
                "NNL01-style Complete Subtree: derive ST(R) and a Cover from revocation set R, "
                "then protect one broadcast content key K with long-lived tree-node keys L_i.",
            ),
            bullets=[
                self._t("R → ST(R) → Cover", "R -> ST(R) -> Cover"),
                self._t("真实 GmSSL SM4-GCM E[L_i](K)", "Real GmSSL SM4-GCM E[L_i](K)"),
                self._t("SUCCESS / REVOKED / HEADER_UNWRAP_FAILED", "SUCCESS / REVOKED / HEADER_UNWRAP_FAILED"),
                self._t("可点击原理 / 本次状态解释层", "Clickable Principle / live state inspector"),
            ],
            button_text=self._t("打开 Complete Subtree", "Open Complete Subtree"),
            callback=self.open_complete_subtree,
        ), 1)
        cards.addWidget(self._module_card(
            object_name="sm2Sm4Card",
            title="SM2 + SM4",
            badge=self._t("多接收者混合加密", "Multi-recipient hybrid encryption"),
            description=self._t(
                "使用单个 SM4-GCM 内容密钥对媒体加密一次，并针对授权集合 S 中每个用户"
                "使用 SM2 公钥独立封装同一个 K。",
                "Encrypt the media once with a single SM4-GCM content key, then independently "
                "wrap the same K with each authorized user's SM2 public key.",
            ),
            bullets=[
                self._t("S → E[u_i] + 单份媒体密文", "S -> E[u_i] + one media ciphertext"),
                self._t("真实 GmSSL SM2 + SM4-GCM", "Real GmSSL SM2 + SM4-GCM"),
                self._t("SUCCESS / NOT_RECIPIENT / SM2_UNWRAP_FAILED", "SUCCESS / NOT_RECIPIENT / SM2_UNWRAP_FAILED"),
                self._t("广播包 .smre 与接收端验证", ".smre package and receiver verification"),
            ],
            button_text=self._t("打开 SM2 + SM4", "Open SM2 + SM4"),
            callback=self.open_sm2_sm4,
        ), 1)
        root.addLayout(cards, 1)

        comparison = QLabel(
            self._t(
                "对比要点：Complete Subtree 的 Header 数量取决于 Cover 大小；"
                "SM2+SM4 每个授权用户增加一个独立 SM2-wrapped key，Header 随 |S| 线性增长。",
                "Comparison: Complete Subtree Header count depends on Cover size; "
                "SM2+SM4 adds one independent SM2-wrapped key per authorized receiver, so its Header grows linearly with |S|.",
            )
        )
        comparison.setWordWrap(True)
        comparison.setObjectName("statusBar")
        root.addWidget(comparison)

        self.setCentralWidget(central)

    def _module_card(
        self,
        *,
        object_name: str,
        title: str,
        badge: str,
        description: str,
        bullets: list[str],
        button_text: str,
        callback,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("panel")
        card.setProperty("moduleCard", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()
        heading = QLabel(title)
        heading.setStyleSheet("font-size:21px;font-weight:700;")
        top.addWidget(heading)
        top.addStretch(1)
        badge_label = QLabel(badge)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_label.setStyleSheet(
            "background:#EEF5FF;border:1px solid #B8D2F5;border-radius:10px;"
            "padding:4px 8px;color:#24589A;font-weight:600;"
        )
        top.addWidget(badge_label)
        layout.addLayout(top)

        body = QLabel(description)
        body.setWordWrap(True)
        body.setObjectName("muted")
        layout.addWidget(body)

        for item in bullets:
            line = QLabel(f"• {item}")
            line.setWordWrap(True)
            layout.addWidget(line)

        layout.addStretch(1)
        button = QPushButton(button_text)
        button.setObjectName("primary")
        button.clicked.connect(callback)
        layout.addWidget(button)

        setattr(self, f"{object_name}_button", button)
        return card

    def open_complete_subtree(self) -> CompleteSubtreeWorkbenchWindow:
        window = CompleteSubtreeWorkbenchWindow(
            n=self.cs_users,
            language=self.language,
        )
        self._track_child(window)
        window.show()
        return window

    def open_sm2_sm4(self) -> DefenseWorkbenchWindow:
        self.workspace.mkdir(parents=True, exist_ok=True)
        window = DefenseWorkbenchWindow(
            workspace=self.workspace,
            language=self.language,
        )
        self._track_child(window)
        window.show()
        return window

    def _track_child(self, window: QMainWindow) -> None:
        self._children.append(window)
        window.destroyed.connect(lambda _obj=None, w=window: self._forget_child(w))

    def _forget_child(self, window: QMainWindow) -> None:
        try:
            self._children.remove(window)
        except ValueError:
            pass
