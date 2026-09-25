# SM2 + SM4 Workbench v0.2.2 测试手册

目标：验证新增的“接收端真实解密路径”画布。该画布只能投影真实 `DecryptResult`，不能伪造解密步骤，也不能接触 raw SM2 私钥或 raw SM4 内容密钥。

## 1. 拉取

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
git rev-parse HEAD
git status --short
```

## 2. 环境

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

必须 ABI CHECK: PASS。

## 3. 编译与新测试

```bash
python -m compileall -q \
  src/sm2_sm4_mre \
  src/sm2_sm4_workbench \
  tests/test_sm2_sm4_receiver_canvas.py

QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_receiver_canvas.py
```

目标：

```text
3 passed
```

## 4. focused suite

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
  tests/test_sm2_sm4_relation_canvas.py \
  tests/test_sm2_sm4_receiver_canvas.py
```

理论目标：

```text
30 passed
0 failed
0 skipped
```

## 5. WSLg 手动验证

启动：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v022
```

先正常完成：

```text
u1-u4 keygen
S={u2,u4}
选择媒体
生成 K
关系图 K -> PK[u2]
关系图 K -> PK[u4]
关系图 K -> SM4-GCM
组装 .smre
```

然后重点验证右侧接收端操作和中央“接收端路径” tab。

### A. 授权用户 u2

右侧选择 `u2` 并真实解密。预期中央自动切换到“接收端路径”，显示：

```text
SK[u2] -> E[u2] -> SM2 解封 -> K -> SM4-GCM 解密/认证 -> 明文 M
```

所有实际成功步骤应为绿色，且：

- `trace.wrapped_key_fingerprint` 可显示；
- `trace.content_key_fingerprint` 可显示；
- `gcm_authenticated == True`；
- 输出文件与原文逐字节一致；
- 不得显示 raw SM4 K 或 raw SM2 私钥。

### B. 非接收者 u1

右侧选择 `u1` 正常解密。预期：

```text
SK[u1] -> 不存在 E[u1]
```

在“非接收者”处红色停止；后面的 SM2/K/SM4 节点应显示未到达。真实 backend 状态必须是：

```text
NOT_RECIPIENT
```

不得产生明文文件。

### C. u1 强行尝试 E[u2]

右侧当前用户 `u1`，force target 选 `u2`。预期图显示：

```text
SK[u1] + E[u2] -> SM2 解封失败
```

应在 SM2 解封节点红色停止。真实 GmSSL 环境通常应返回：

```text
SM2_UNWRAP_FAILED
```

不得产生明文文件。

### D. reset

`Reset broadcast` 后：

- receiver canvas 清空结果；
- package_ready=False；
- 自动回到第一个“关系图” tab；
- 用户密钥仍保留；
- 媒体按 keep_media=True 保留。

## 6. 英文 fallback

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v022-en \
  --lang en_US
```

“Receiver path” 及其节点必须全部英文，不得混入中文。

## 7. 安全边界

重点检查：

- `ReceiverFlowCanvas.state` 只包含 user id、target id、status、fingerprint、GCM auth 状态、输出文件名；
- 不得包含 raw `content_key`；
- 不得包含 private-key bytes/PEM；
- 图上的成功/失败必须来自真实 `DecryptResult.trace`，不能根据 UI 所选用户猜测。

## 8. 报告模板

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
receiver canvas tests:
focused total:
skips:

## Authorized receiver
u2 status:
SM2 unwrap path:
content key fingerprint:
GCM auth:
plaintext compare:

## Non-recipient
u1 status:
stop point:
plaintext emitted:

## Force try
u1 -> u2 status:
stop point:
plaintext emitted:

## Security boundary
raw K exposure:
private key exposure:
result source:

## Reset / language
reset sync:
English fallback:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```

本轮不要修改 backend，不要 commit/push。发现问题先报告最小复现和截图。
