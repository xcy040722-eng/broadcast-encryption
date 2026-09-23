"""Small bilingual text catalog for the SM2 + SM4 workbench.

The UI defaults to Simplified Chinese, while keeping an English fallback for
machines whose desktop environment does not provide a usable CJK font.
Cryptographic identifiers such as SM2, SM3, SM4-GCM, E[u2] and .smre remain
unchanged so the teaching terminology stays aligned with the backend.
"""

from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_LANGUAGES = ("zh_CN", "en_US")
DEFAULT_LANGUAGE = "zh_CN"


_TEXT: dict[str, dict[str, str]] = {
    "zh_CN": {
        "window_title": "SM2 + SM4 多接收者交互工作台",
        "header_title": "SM2 + SM4 多接收者交互工作台",
        "header_subtitle": "直接操作 → InteractiveSession → 真实 GmSSL",
        "stage": "阶段：{value}",
        "reset_broadcast": "重置本次广播",
        "panel_users": "用户 / 接收者集合 S",
        "panel_users_help": "先为用户生成真实 SM2 密钥，再选择本次广播的接收者。",
        "panel_workspace": "密码学工作区",
        "panel_receiver": "接收端验证",
        "panel_receiver_help": "组装广播包后，可验证授权用户、非接收者以及错误私钥强制尝试。",
        "choose_media": "选择媒体…",
        "no_media": "尚未选择媒体",
        "generate_material": "生成内容密钥与会话材料",
        "wrapped_keys": "已封装的内容密钥",
        "wrapped_none": "暂无 —— 将 SM4 内容密钥拖到已选中的用户上",
        "session_events": "会话事件",
        "act_as_user": "当前接收用户",
        "decrypt_selected": "以该用户身份解密",
        "force_target": "强制尝试目标密钥封装",
        "force_try": "用错误私钥强制尝试",
        "receiver_wait": "请先组装广播包",
        "receiver_ready": "广播包已就绪，可以进行接收端验证",
        "user_key_not_generated": "SM2 密钥：未生成",
        "user_key_ready": "SM2 密钥：已就绪",
        "recipient": "本次接收者",
        "generate_sm2_key": "生成 SM2 密钥",
        "hint_generate_key": "请先生成密钥",
        "hint_wrapped_ready": "内容密钥已封装",
        "hint_material_first": "请先生成内容密钥",
        "hint_drop_wrap": "将 SM4 密钥拖到此处 → 真实执行 SM2 封装",
        "hint_select_recipient": "先勾选为接收者",
        "content_key_title": "SM4 内容密钥 K",
        "not_generated": "尚未生成",
        "content_key_wait": "选择接收者和媒体后，再生成会话材料",
        "content_key_drag": "拖到已选用户的公钥目标，或拖到 SM4-GCM 引擎",
        "engine_title": "SM4-GCM 媒体加密引擎",
        "engine_wait": "等待内容密钥与媒体",
        "engine_drop": "将 SM4 密钥拖到这里",
        "engine_not_ready": "尚未就绪",
        "engine_ready": "已就绪；拖入后将真实执行 SM4-GCM 加密。",
        "engine_done": "SM4-GCM 加密完成",
        "engine_payload_ready": "媒体密文已生成 · {size} 字节",
        "package_title": "广播包",
        "package_not_assembled": "尚未组装",
        "package_ready": "已满足组装条件",
        "package_needs": "需要全部密钥封装 + 媒体密文",
        "package_assemble": "组装 .smre 广播包",
        "package_assembled": "广播包已组装",
        "dialog_generate_title": "为 {user_id} 生成 SM2 密钥",
        "dialog_private_password": "私钥保护口令：",
        "dialog_password_title": "输入 {user_id} 的私钥口令",
        "dialog_password": "口令：",
        "dialog_choose_media": "选择媒体或文件",
        "dialog_save_package": "保存广播包",
        "dialog_save_plaintext": "保存恢复后的明文",
        "dialog_force_output": "强制尝试输出（正常情况下不应生成）",
        "status_ready": "就绪",
        "status_key_generated": "已为 {user_id} 生成真实 SM2 密钥对",
        "status_media_selected": "已选择媒体：{name}",
        "status_recipient_selected": "{user_id}：已加入接收者集合 S",
        "status_recipient_removed": "{user_id}：已从接收者集合 S 移除",
        "status_material_generated": "已生成真实 SM4 内容密钥 · 指纹 {fingerprint}",
        "status_wrapped": "已使用 {user_id} 的 SM2 公钥封装同一个内容密钥 K",
        "status_payload_encrypted": "媒体已使用同一个 K 完成一次 SM4-GCM 加密",
        "status_package_assembled": "广播包已组装：{name}",
        "status_receiver": "{user_id}：{status} · {message}",
        "status_force": "强制尝试 {attacker} → {target}：{status}",
        "status_reset": "已重置广播状态；用户 SM2 密钥仍保留",
        "status_no_force_target": "当前没有可用于强制尝试的密钥封装",
        "flow_1": "1 用户与授权集合",
        "flow_2": "2 内容密钥 K",
        "flow_3": "3 SM2 密钥封装",
        "flow_4": "4 SM4-GCM 媒体加密",
        "flow_5": "5 组装广播包",
        "flow_6": "6 接收端验证",
        "stage_EMPTY": "准备",
        "stage_CONFIGURING": "配置用户与媒体",
        "stage_READY_FOR_MATERIAL": "可生成会话材料",
        "stage_MATERIAL_READY": "内容密钥已生成",
        "stage_WRAPPING": "正在封装内容密钥",
        "stage_PAYLOAD_ENCRYPTED": "媒体已加密",
        "stage_READY_TO_ASSEMBLE": "可组装广播包",
        "stage_PACKAGE_ASSEMBLED": "广播包已组装",
    },
    "en_US": {
        "window_title": "SM2 + SM4 Multi-Recipient Workbench",
        "header_title": "SM2 + SM4 Multi-Recipient Workbench",
        "header_subtitle": "Direct manipulation → InteractiveSession → real GmSSL",
        "stage": "Stage: {value}",
        "reset_broadcast": "Reset broadcast",
        "panel_users": "Users / recipient set S",
        "panel_users_help": "Generate real SM2 keys, then choose recipients before generating K.",
        "panel_workspace": "Cryptography workspace",
        "panel_receiver": "Receiver lab",
        "panel_receiver_help": "After package assembly, try an authorized user, a non-recipient, or force a wrong SM2 key onto another user's wrapped key.",
        "choose_media": "Choose media…",
        "no_media": "No media selected",
        "generate_material": "Generate content material",
        "wrapped_keys": "Wrapped keys",
        "wrapped_none": "None yet — drag the SM4 key onto a selected user",
        "session_events": "Session events",
        "act_as_user": "Act as user",
        "decrypt_selected": "Decrypt as selected user",
        "force_target": "Force target wrapped key",
        "force_try": "Force try wrong private key",
        "receiver_wait": "Assemble a package first",
        "receiver_ready": "Package ready for receiver experiments",
        "user_key_not_generated": "SM2 key: not generated",
        "user_key_ready": "SM2 key: ready",
        "recipient": "Recipient",
        "generate_sm2_key": "Generate SM2 key",
        "hint_generate_key": "Generate key first",
        "hint_wrapped_ready": "Wrapped key ready",
        "hint_material_first": "Generate content material first",
        "hint_drop_wrap": "Drop SM4 key here → real SM2 wrap",
        "hint_select_recipient": "Select as recipient",
        "content_key_title": "SM4 content key K",
        "not_generated": "not generated",
        "content_key_wait": "Select recipients + media, then generate material",
        "content_key_drag": "Drag to a selected user's public-key target, or to the SM4-GCM engine",
        "engine_title": "SM4-GCM media engine",
        "engine_wait": "Waiting for media + content key",
        "engine_drop": "Drop SM4 key here",
        "engine_not_ready": "Not ready",
        "engine_ready": "Ready. The drop performs real SM4-GCM encryption.",
        "engine_done": "SM4-GCM complete",
        "engine_payload_ready": "Encrypted payload ready · {size} bytes",
        "package_title": "Broadcast package",
        "package_not_assembled": "Not assembled",
        "package_ready": "Ready to assemble",
        "package_needs": "Needs all wrapped keys + encrypted payload",
        "package_assemble": "Assemble .smre package",
        "package_assembled": "Package assembled",
        "dialog_generate_title": "Generate SM2 key for {user_id}",
        "dialog_private_password": "Private-key password:",
        "dialog_password_title": "Private key password for {user_id}",
        "dialog_password": "Password:",
        "dialog_choose_media": "Choose media/file",
        "dialog_save_package": "Save broadcast package",
        "dialog_save_plaintext": "Save recovered plaintext",
        "dialog_force_output": "Forced-try output (should not survive)",
        "status_ready": "Ready",
        "status_key_generated": "Generated real SM2 key pair for {user_id}",
        "status_media_selected": "Selected media: {name}",
        "status_recipient_selected": "{user_id}: recipient selected",
        "status_recipient_removed": "{user_id}: recipient removed",
        "status_material_generated": "Generated one real SM4 content key · fingerprint {fingerprint}",
        "status_wrapped": "SM2 wrapped the session content key for {user_id}",
        "status_payload_encrypted": "SM4-GCM encrypted the media exactly once",
        "status_package_assembled": "Assembled broadcast package: {name}",
        "status_receiver": "{user_id}: {status} · {message}",
        "status_force": "Force try {attacker} → {target}: {status}",
        "status_reset": "Broadcast reset; SM2 user keys preserved",
        "status_no_force_target": "No wrapped-key target is available",
        "flow_1": "1 Users & authorization",
        "flow_2": "2 Content key K",
        "flow_3": "3 SM2 key wrapping",
        "flow_4": "4 SM4-GCM media",
        "flow_5": "5 Broadcast package",
        "flow_6": "6 Receiver lab",
        "stage_EMPTY": "Ready",
        "stage_CONFIGURING": "Configuring",
        "stage_READY_FOR_MATERIAL": "Ready for material",
        "stage_MATERIAL_READY": "Content key ready",
        "stage_WRAPPING": "Wrapping keys",
        "stage_PAYLOAD_ENCRYPTED": "Payload encrypted",
        "stage_READY_TO_ASSEMBLE": "Ready to assemble",
        "stage_PACKAGE_ASSEMBLED": "Package assembled",
    },
}


@dataclass(frozen=True)
class Translator:
    language: str = DEFAULT_LANGUAGE

    def __post_init__(self) -> None:
        if self.language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"unsupported UI language {self.language!r}; choose one of {SUPPORTED_LANGUAGES}"
            )

    def __call__(self, key: str, **values: object) -> str:
        try:
            template = _TEXT[self.language][key]
        except KeyError as exc:
            raise KeyError(f"missing UI text key {key!r} for {self.language}") from exc
        return template.format(**values)

    def stage(self, stage_name: str) -> str:
        return self(f"stage_{stage_name}")
