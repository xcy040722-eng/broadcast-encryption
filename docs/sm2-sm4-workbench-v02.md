# SM2 + SM4 Workbench v0.2

v0.2 starts the visual/interaction redesign while preserving the validated v0.1 action path.

## Goals

- Simplified Chinese is the default UI language.
- English remains available as a fallback with `--lang en_US`.
- Cryptographic identifiers remain unchanged: `SM2`, `SM3`, `SM4-GCM`, `K`, `E[u2]`, `.smre`.
- Add a six-stage workflow strip so the teacher can see where the current session is in the cryptographic process.
- Preserve the invariant that all crypto actions still call `InteractiveSession` and the real GmSSL backend.

## Language behavior

Default:

```bash
python -m src.sm2_sm4_workbench --workspace /tmp/sm2-sm4-demo
```

English fallback:

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-demo \
  --lang en_US
```

Python source files are UTF-8 and Qt/PySide6 use Unicode strings, so Chinese text does not conflict with the cryptographic byte strings. The only environment-specific risk is the system font. If WSLg renders Chinese as empty squares/tofu, install a CJK font or run with `--lang en_US`; do not change crypto code.

## Workflow strip

The top strip shows:

1. 用户与授权集合
2. 内容密钥 K
3. SM2 密钥封装
4. SM4-GCM 媒体加密
5. 组装广播包
6. 接收端验证

It is view-only. It reflects `InteractiveSession.stage`; clicking it does not advance the session.

## Security/UI boundary

The Chinese localization layer only owns display strings. It does not receive raw SM4 keys or SM2 private-key material. The content-key card continues to display only the SM3 fingerprint.

Backend event details remain technical English text for now. They are deliberately left unchanged so debugging output is not transformed or reinterpreted by the UI localization layer.
