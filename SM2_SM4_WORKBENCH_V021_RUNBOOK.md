# SM2 + SM4 Workbench v0.2.1 关系画布测试手册

本轮目标：验证新的“密码学对象关系图”不是播放动画，而是 `InteractiveSession` 的实时投影，并且在关系图内拖拽 K 会真实触发 SM2 封装 / SM4-GCM 加密。

## 1. 拉取

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
git rev-parse HEAD
git status --short
```

工作区必须干净。

## 2. 环境

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

若是新 WSL 环境，建议直接重新运行 bootstrap。当前 bootstrap 已包含中文字体和常见 WSLg Qt/xcb 运行依赖：

```bash
bash scripts/bootstrap_gmssl_wsl.sh
```

## 3. 编译

```bash
python -m compileall -q \
  src/sm2_sm4_mre \
  src/sm2_sm4_workbench \
  tests/test_sm2_sm4_relation_canvas.py
```

## 4. 关系画布 headless 测试

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_relation_canvas.py
```

预期：

```text
3 passed
```

重点：

- K → PK[u2] drop 发出 `wrapRequested("u2")`
- K → SM4-GCM drop 发出 `encryptRequested()`
- 已经 wrapped 的用户不允许 synthetic/programmatic 重复 drop
- payload 已生成后不允许再次 drop 到 SM4-GCM
- canvas state 只持有 K 的 fingerprint，不持有 raw K
- `payload_encryption_count` 组包前后保持 1

## 5. focused suite

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q -rs \
  tests/test_sm2_sm4_mre_core.py \
  tests/test_sm2_sm4_mre_package_validation.py \
  tests/test_sm2_sm4_interactive_session.py \
  tests/test_sm2_sm4_mre_gmssl_integration.py \
  tests/test_sm2_sm4_workbench_smoke.py \
  tests/test_sm2_sm4_workbench_gmssl.py \
  tests/test_sm2_sm4_workbench_qt6_regressions.py \
  tests/test_sm2_sm4_relation_canvas.py
```

上一轮为 24 passed，本轮新增 3 个画布测试，因此目标：

```text
27 passed
0 failed
0 skipped
```

## 6. WSLg 人工验证

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v021
```

默认应为中文界面。

### 6.1 关系图状态

选择 `S={u2,u4}` 和媒体后，关系图应出现：

```text
SM4 内容密钥 K
媒体 M
PK[u2] → E[u2]
PK[u4] → E[u4]
SM4-GCM
广播包
```

生成 K 后，仅显示其 SM3 fingerprint，不应出现 raw 16-byte key。

### 6.2 必须使用关系图完成真实拖拽

不要只使用旧的 UserCard / EngineCard drop target。本轮至少一次必须从关系图的 K 节点开始拖：

```text
关系图 K → PK[u2]
关系图 K → PK[u4]
关系图 K → SM4-GCM
```

用 probe 或 session events 确认分别真实触发：

```text
session.wrap_for("u2")
session.wrap_for("u4")
session.encrypt_payload()
```

不能只是颜色变化。

### 6.3 视觉状态

- 未完成关系：灰色虚线
- 完成的 SM2 wrap / SM4 encryption：绿色实线 / 绿色节点
- READY_TO_ASSEMBLE：广播包节点显示“已满足组包条件”
- PACKAGE_ASSEMBLED：广播包节点显示已组装
- reset：关系图立即回到未生成 K / 无 E[i] / 无 payload 状态，但保留媒体（keep_media=True）和用户密钥

### 6.4 旧功能回归

仍需验证：

```text
u2/u4 SUCCESS
u1 NOT_RECIPIENT
u1 force-try u2 -> SM2_UNWRAP_FAILED（或 backend 允许的安全失败状态）
payload_encryption_count == 1
```

## 7. 英文 fallback

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v021-en \
  --lang en_US
```

关系图也必须为英文标签，无中文残留。

## 8. 报告模板

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
relation canvas tests:
focused suite:
skips:

## Real interaction canvas
canvas launch/render:
K node draggable:
K -> PK[u2]:
K -> PK[u4]:
K -> SM4-GCM:
real backend probes:
raw K exposure:
payload_encryption_count:
reset sync:

## Visual state
pending edges:
completed edges:
package ready state:
package assembled state:
Chinese labels:
English fallback:

## Regression
u2/u4:
u1 normal:
u1 force-try:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```

本轮不要修改 backend，不要 commit/push。若关系图报错或拖拽不触发，返回 traceback + 最小复现 + 截图。
