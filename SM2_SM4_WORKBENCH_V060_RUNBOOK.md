# SM2 + SM4 Workbench v0.6 Final Delivery Runbook

本轮目标：**不新增密码学功能**，只做最终交付确认。

目标分支：

```text
sm2-sm4-backend
```

本轮新增的是根目录 `README.md` 与 `SM2_SM4_DEFENSE_CHECKLIST.md`。程序功能基线仍为 v0.5，测试目标仍是：

```text
43 passed
0 failed
0 skipped
```

## 1. 拉取并确认工作区

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
git rev-parse HEAD
git status --short
```

要求 worktree 干净。

## 2. 环境检查

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

要求：

```text
ABI CHECK: PASS
sizeof(Sm2Key)=128
sizeof(Sm4Gcm)=296
```

## 3. 编译检查

```bash
python -m compileall -q src/sm2_sm4_mre src/sm2_sm4_workbench tests
```

要求 exit 0。

## 4. 最终 focused suite

执行 v0.5 已验证的 focused suite：

```bash
QT_QPA_PLATFORM=offscreen pytest -q -rs \
  tests/test_sm2_sm4_mre_core.py \
  tests/test_sm2_sm4_mre_package_validation.py \
  tests/test_sm2_sm4_interactive_session.py \
  tests/test_sm2_sm4_mre_gmssl_integration.py \
  tests/test_sm2_sm4_workbench_smoke.py \
  tests/test_sm2_sm4_workbench_gmssl.py \
  tests/test_sm2_sm4_workbench_qt6_regressions.py \
  tests/test_sm2_sm4_relation_canvas.py \
  tests/test_sm2_sm4_receiver_canvas.py \
  tests/test_sm2_sm4_principle_inspector.py \
  tests/test_sm2_sm4_result_presenter.py \
  tests/test_sm2_sm4_defense_guide.py
```

目标：

```text
43 passed
0 failed
0 skipped
```

## 5. README 审计

检查 `README.md` 必须明确：

```text
SM2 + SM4 多接收者混合加密 / 广播式分发
媒体主体只加密一次
每个授权用户增加 E[i]
头部随接收者数量增长
```

不得宣称：

```text
constant-size header
完整撤销型 BE
Succinct-LWE security
```

运行命令应可直接复制：

```bash
python -m src.sm2_sm4_workbench --workspace /tmp/sm2-sm4-demo
```

## 6. 答辩 Checklist 审计

完整阅读：

```text
SM2_SM4_DEFENSE_CHECKLIST.md
```

确认其中覆盖：

- 环境 / ABI；
- 43 tests 基线；
- S={u2,u4}；
- 唯一 K；
- 两个 E[i]；
- SM4-GCM 仅一次；
- `.smre`；
- SUCCESS；
- NOT_RECIPIENT；
- SM2_UNWRAP_FAILED；
- 原理解释层；
- 安全术语边界；
- 常见提问。

## 7. WSLg 最终彩排

中文：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-final-defense
```

完整手动执行：

```text
u1-u4 keygen
S={u2,u4}
选择媒体
生成 K
K -> PK[u2]
K -> PK[u4]
K -> SM4-GCM
assemble
u2 SUCCESS
u1 NOT_RECIPIENT
u1 -> u2 force try = SM2_UNWRAP_FAILED
```

确认：

```text
payload_encryption_count == 1
u2 plaintext byte-for-byte equal
u1 failure paths emit no plaintext
sender K fingerprint == authorized receiver recovered K fingerprint
```

## 8. 英文 fallback 快速检查

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-final-defense-en \
  --lang en_US
```

确认：

- 无 CJK 泄漏；
- 无全角冒号；
- 关系图、Receiver path、Principle / live state、Defense guide 均为英文。

## 9. 最终报告模板

```text
## Target
branch:
commit:
worktree:

## Environment
ABI check:
PySide6:
GmSSL native:
GmSSL-Python:

## Automated
compileall:
focused suite:
skips:

## Documentation
README audit:
Defense checklist audit:
terminology boundary:

## Final rehearsal
Chinese launch:
full sender flow:
SUCCESS:
NOT_RECIPIENT:
SM2_UNWRAP_FAILED:
payload_encryption_count:
K fingerprint match:
plaintext safety:
English fallback:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```

本轮若 PASS，即可把程序主体视为课程交付版本；之后只建议修复明确缺陷，不再扩展算法功能。
