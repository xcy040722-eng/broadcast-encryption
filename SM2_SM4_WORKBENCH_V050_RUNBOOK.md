# SM2 + SM4 Workbench v0.5.0 验证说明

目标：验证 v0.5 新增的“答辩提示条”只做**手动演示引导**，不会自动执行密码学操作，也不会破坏 v0.4 已验证的真实 GmSSL 链路。

## 1. 目标分支

```text
branch: sm2-sm4-backend
```

先确认：

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

必须：

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
  tests/test_sm2_sm4_defense_guide.py
```

## 4. 新增提示层单测

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_defense_guide.py
```

预期：

```text
5 passed
```

## 5. 完整 focused suite

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
  tests/test_sm2_sm4_principle_inspector.py \
  tests/test_sm2_sm4_result_presenter.py \
  tests/test_sm2_sm4_defense_guide.py
```

v0.4 基线为 38 passed，本轮新增 5 个测试，因此理论目标：

```text
43 passed
0 failed
0 skipped
```

## 6. WSLg 中文手动检查

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v050
```

检查中央工作区标题下方新增浅黄色“答辩提示”区域。

### 初始阶段

提示应引导演示者：

```text
生成 u1-u4 SM2 密钥
选择 S
选择媒体
```

注意：提示出现后，不应自动生成任何密钥、不应自动选择用户、不应改变 SessionStage。

### READY_FOR_MATERIAL

选择 `S={u2,u4}` + 媒体后，应提示：

```text
点击“生成内容密钥与会话材料”
强调每次广播只生成一个 SM4 K
```

### MATERIAL_READY / WRAPPING

生成 K 后，应提示将 K 拖到：

```text
PK[u2]
PK[u4]
SM4-GCM
```

顺序可任意。

必须用 probe / session events 确认：

```text
K -> PK[u2]   => session.wrap_for("u2")
K -> PK[u4]   => session.wrap_for("u4")
K -> SM4-GCM  => session.encrypt_payload()
```

提示条本身不得调用这三个方法。

### READY_TO_ASSEMBLE

应提示：

```text
组装 .smre 广播包
```

并强调媒体密文只有一份。

### PACKAGE_ASSEMBLED

未做接收端实验前，应提示三条路径：

```text
u2 normal -> SUCCESS
u1 normal -> NOT_RECIPIENT
u1 force u2 -> SM2_UNWRAP_FAILED
```

然后实际逐条执行。

完成 u2 SUCCESS 后，提示应更新为：

```text
接下来选择 u1 正常解密
```

完成 u1 NOT_RECIPIENT 后，应更新为：

```text
最后执行 u1 -> u2 错误私钥强制尝试
```

完成 force-try 后，应更新为：

```text
核心演示完成
可点击关系图 / 接收端路径节点解释原理与本次真实状态
```

## 7. 安全与架构检查

确认 `defense_guide.py`：

- 只消费 `SessionSnapshot` 与 `ReceiverCanvasState`；
- 不持有 raw K；
- 不持有私钥；
- 不调用 `InteractiveSession` 方法；
- 不修改 recipients / media / package / trace；
- 只返回字符串提示。

提示层不是 autoplay / Next 按钮系统。

## 8. Reset

点击“重置本次广播”后：

- 用户 SM2 keys 保留；
- 广播状态清空；
- 接收端结果清空；
- 提示条回到配置阶段建议；
- 媒体按现有 `keep_media=True` 逻辑保留。

## 9. 英文 fallback

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v050-en \
  --lang en_US
```

提示条必须全部英文。

检查：

```text
Defense guide
Next step
Direct manipulation
Three receiver checks
Core demo complete
```

不得出现 CJK 字符或全角冒号 `：`。

## 10. 项目文档检查

阅读：

```text
SM2_SM4_PROJECT_GUIDE.md
```

确认其中没有把本方案错误宣传成：

```text
constant-size broadcast header
advanced revocation BE
Succinct-LWE security
```

应明确描述为：

```text
SM2 + SM4 多接收者混合加密 / 广播式分发方案
媒体只加密一次
E[i] 头部随接收者数量增长
```

## 11. 报告模板

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
defense guide tests:
focused total:
skips:

## Chinese defense guide
initial:
ready for material:
material ready:
ready to assemble:
package assembled:
after SUCCESS:
after NOT_RECIPIENT:
after force-try:
no auto execution:

## Crypto regression
real wrap u2/u4:
real SM4-GCM:
payload_encryption_count:
u2 SUCCESS:
u1 NOT_RECIPIENT:
u1 force-try:
plaintext safety:

## Security boundary
guide reads raw K:
guide reads private key:
guide mutates session:

## English fallback
CJK leakage:
full-width colon count:

## Documentation
SM2_SM4_PROJECT_GUIDE.md:
terminology accuracy:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```

本轮不要修改 backend，不要重构密码学流程，不要 commit / push。失败时先返回 traceback、最小复现与建议修复。
