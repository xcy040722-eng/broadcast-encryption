"""Small Chinese-first text catalog for the Complete Subtree workbench."""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("zh_CN", "en_US")
DEFAULT_LANGUAGE = "zh_CN"

_TEXT = {
    "zh_CN": {
        "window_title": "Complete Subtree 广播撤销工作台",
        "header_title": "Complete Subtree · 树型广播撤销",
        "header_subtitle": "NNL01 Cover 算法 + GmSSL SM4-GCM 密钥头",
        "panel_revocation": "撤销集合 R",
        "panel_revocation_help": "勾选需要撤销的用户，然后计算 ST(R) 与 Cover。",
        "compute_cover": "计算 ST(R) / Cover",
        "generate_material": "生成广播内容密钥 K",
        "wrap_all": "封装全部 Cover 节点",
        "reset": "重置本次广播",
        "content_key": "内容密钥 K",
        "not_generated": "尚未生成",
        "drag_hint": "拖动 K 到绿色 Cover 根节点，执行真实 SM4-GCM E[L_i](K)",
        "tree_title": "Complete Subtree 关系图",
        "receiver": "接收端验证",
        "receiver_help": "选择用户恢复 K；撤销用户应无匹配 Cover 节点。",
        "recover": "以该用户恢复 K",
        "force_target": "强制尝试目标 Header",
        "force_try": "错误路径密钥强制尝试",
        "result_wait": "等待接收端验证。",
        "log": "对象细节 / 日志",
        "guide_initial": "答辩提示 · 先选择撤销集合 R，再计算 Steiner Tree 与 Cover。",
        "guide_cover": "下一步 · 生成唯一广播内容密钥 K。Cover 根决定哪些节点密钥用于保护 K。",
        "guide_material": "直接操作 · 将 K 拖到每个绿色 Cover 根节点；每次拖拽执行真实 GmSSL SM4-GCM。",
        "guide_wrapping": "继续封装尚未完成的 Cover 根节点，直到 Header Ready。",
        "guide_ready": "Header 已就绪 · 先验证授权用户 SUCCESS，再验证撤销用户 REVOKED，并做错误路径密钥 force-try。",
        "stage_config": "1 撤销集合",
        "stage_cover": "2 Cover",
        "stage_key": "3 内容密钥 K",
        "stage_header": "4 Header 封装",
        "stage_receiver": "5 接收验证",
        "status_ready": "就绪",
        "status_cover": "已计算 Cover：{roots}",
        "status_material": "已生成 K · SM3 指纹 {fp}",
        "status_wrapped": "已生成 E[L{node}](K)",
        "status_recover": "u{user}：{status} · {message}",
        "status_force": "u{user} → v{target}：{status} · {message}",
        "status_reset": "已重置本次广播，长期树密钥保持不变。",
        "stage_badge": "阶段：{stage}",
        "cover_summary": "R={revoked} · ST={st} · Cover={cover}",
        "fp": "SM3 指纹：{fp}",
        "header_ready": "Header Ready",
    },
    "en_US": {
        "window_title": "Complete Subtree Revocation Workbench",
        "header_title": "Complete Subtree · Tree-based broadcast revocation",
        "header_subtitle": "NNL01 cover algorithm + GmSSL SM4-GCM key headers",
        "panel_revocation": "Revocation set R",
        "panel_revocation_help": "Select revoked users, then compute ST(R) and Cover.",
        "compute_cover": "Compute ST(R) / Cover",
        "generate_material": "Generate broadcast content key K",
        "wrap_all": "Wrap all Cover nodes",
        "reset": "Reset broadcast",
        "content_key": "Content key K",
        "not_generated": "not generated",
        "drag_hint": "Drag K onto a green Cover root to run real SM4-GCM E[L_i](K)",
        "tree_title": "Complete Subtree object graph",
        "receiver": "Receiver verification",
        "receiver_help": "Recover K as a user; revoked users should match no Cover node.",
        "recover": "Recover K as user",
        "force_target": "Force-try target Header",
        "force_try": "Force try with wrong path key",
        "result_wait": "Waiting for receiver verification.",
        "log": "Object details / log",
        "guide_initial": "Defense guide · Choose revocation set R, then compute the Steiner tree and Cover.",
        "guide_cover": "Next · Generate the unique broadcast content key K. Cover roots select the node keys that protect K.",
        "guide_material": "Direct manipulation · Drag K onto each green Cover root; every drop runs real GmSSL SM4-GCM.",
        "guide_wrapping": "Continue wrapping remaining Cover roots until Header Ready.",
        "guide_ready": "Header Ready · Verify an authorized SUCCESS, a revoked REVOKED result, then a wrong-path-key force try.",
        "stage_config": "1 Revocation",
        "stage_cover": "2 Cover",
        "stage_key": "3 Content key K",
        "stage_header": "4 Header wrap",
        "stage_receiver": "5 Receiver",
        "status_ready": "Ready",
        "status_cover": "Computed Cover: {roots}",
        "status_material": "Generated K · SM3 fingerprint {fp}",
        "status_wrapped": "Created E[L{node}](K)",
        "status_recover": "u{user}: {status} · {message}",
        "status_force": "u{user} -> v{target}: {status} · {message}",
        "status_reset": "Broadcast reset; long-lived tree keys were preserved.",
        "stage_badge": "Stage: {stage}",
        "cover_summary": "R={revoked} · ST={st} · Cover={cover}",
        "fp": "SM3 fingerprint: {fp}",
        "header_ready": "Header Ready",
    },
}


class Translator:
    def __init__(self, language: str = DEFAULT_LANGUAGE):
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"unsupported language: {language}")
        self.language = language

    def __call__(self, key: str, **kwargs) -> str:
        text = _TEXT[self.language].get(key, _TEXT["en_US"].get(key, key))
        return text.format(**kwargs)
