# SM2 + SM4 Workbench v0.3 — 答辩原理 / 本次状态检查器测试说明

目标：验证“关系画布/接收端路径 → 点击对象 → 原理与真实状态解释”链路。该层不得实现或复制密码学，只能消费 `SessionSnapshot` 与 `ReceiverCanvasState` 等安全投影。

## 1. 目标版本

分支：`sm2-sm4-backend`

先执行：

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
git rev-parse HEAD
git status --short
```

工作区应干净。

## 2. 环境

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
```

必须保持：

```text
ABI CHECK: PASS
sizeof(Sm2Key)=128
sizeof(Sm4Gcm)=296
```

## 3. 编译

```bash
python -m compileall -q \
  src/sm2_sm4_mre \
  src/sm2_sm4_workbench \
  tests/test_sm2_sm4_principle_inspector.py
```

## 4. 新增回归测试

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_principle_inspector.py
```

目标：

```text
3 passed
```

重点：

- 发送端 K 解释页显示 128-bit 角色与 K 的 SM3 指纹；
- 不出现 raw K；
- `recipient:u2` 解释页显示真实 E[u2] 指纹和 `SM2.Enc` 关系；
- 接收端 GCM 解释页来自真实 `DecryptResult.trace` 投影；
- 不出现 SM2 私钥 PEM 正文；
- reset 清空当前解释选择。

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
  tests/test_sm2_sm4_relation_canvas.py \
  tests/test_sm2_sm4_receiver_canvas.py \
  tests/test_sm2_sm4_principle_inspector.py
```

理论目标：

```text
33 passed
0 failed
0 skipped
```

## 6. WSLg 手工验证

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v030
```

默认中文。

完成正常发送端流程：

```text
keygen u1-u4
S={u2,u4}
选择媒体
生成 K
K → PK[u2]
K → PK[u4]
K → SM4-GCM
assemble .smre
```

### 6.1 发送端对象点击

在“关系图”中依次点击：

```text
SM4 内容密钥 K
媒体 M
PK[u2] → E[u2]
SM4-GCM
广播包
```

每次应自动切到：

```text
原理 / 本次状态
```

并显示：

```text
作用
输入
核心关系 / 运算
输出
本次真实状态
安全边界
```

重点核对：

- K 页：`K ← {0,1}^128`，只显示 SM3 指纹；
- E[u2] 页：`E_i = SM2.Enc(PK_i, Envelope(...))`，显示本次 E[u2] 指纹；
- SM4-GCM 页：`(C_M, T) = SM4-GCM.Enc(...)`，显示 payload 字节数和 `payload_encryption_count=1`；
- 广播包页：显示 `.smre` 实际路径或是否达到组装条件。

### 6.2 接收端对象点击

先执行 u2 正常解密，自动进入“接收端路径”。然后分别点击：

```text
SK[u2]
E[u2]
SM2 解封
恢复的 K
SM4-GCM 解密 / 认证 → 明文 M
```

应显示对应原理与**本次真实 trace 状态**。

特别核对：

```text
恢复 K 的指纹 == 发送端 K 指纹
GCM authenticated=True
输出文件名正确
```

再执行：

```text
u1 normal decrypt -> NOT_RECIPIENT
u1 force-try u2 -> SM2_UNWRAP_FAILED
```

点击失败节点时，解释页必须反映真实失败状态，而不是把未到达步骤解释成已成功。

## 7. 安全边界

搜索整个“原理 / 本次状态”页文本，确认：

```text
raw 16-byte SM4 K hex 不出现
SM2 private PEM body 不出现
```

允许出现：

```text
SM3 fingerprint
用户 ID
target ID
DecryptStatus
GCM authentication result
output filename
```

## 8. 英文 fallback

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v030-en \
  --lang en_US
```

第四个 Tab 应为：

```text
Principle / live state
```

内部解释应全英文，无中文残留。

## 9. Reset

点击“重置本次广播”后：

- 原理 inspector 回到“选择一个密码学对象”；
- receiver flow 清空；
- 自动回关系图；
- 用户 SM2 keys 保留；
- media 按现有 `keep_media=True` 规则保留。

## 10. 报告模板

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
principle inspector tests:
focused total:
skips:

## Sender inspector
K click:
media click:
recipient E click:
SM4-GCM click:
package click:
formula/live-state accuracy:

## Receiver inspector
SK click:
E click:
SM2 unwrap click:
recovered K click:
GCM/plaintext click:
SUCCESS state:
NOT_RECIPIENT state:
force-try state:

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

本轮不要修改仓库，不要 commit/push。失败时返回 traceback、截图、最小复现和建议最小修复。
