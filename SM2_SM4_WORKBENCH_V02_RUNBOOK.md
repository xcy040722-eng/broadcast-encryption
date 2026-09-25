# SM2 + SM4 Workbench v0.2 测试手册

目标：验证中文界面、英文回退、六阶段流程条，以及现有真实密码学交互链路没有回归。

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

ABI 必须 PASS。

### 中文字体 / WSLg 前置条件

默认界面语言是 `zh_CN`。WSL/Ubuntu 新环境建议安装：

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk
```

仓库的 `scripts/bootstrap_gmssl_wsl.sh` 已包含 `fonts-noto-cjk` 以及常见 Qt/xcb WSLg 运行库。

若中文出现 tofu/方框，不要修改 Python 源码编码或密码学逻辑；先检查字体：

```bash
fc-list :lang=zh | head
```

仍无法正常显示时可使用英文回退：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v02-en \
  --lang en_US
```

## 3. 编译

```bash
python -m compileall -q \
  src/sm2_sm4_mre \
  src/sm2_sm4_workbench \
  tests/test_sm2_sm4_workbench_smoke.py \
  tests/test_sm2_sm4_workbench_gmssl.py \
  tests/test_sm2_sm4_workbench_qt6_regressions.py
```

## 4. UI 回归

```bash
QT_QPA_PLATFORM=offscreen \
pytest -q tests/test_sm2_sm4_workbench_qt6_regressions.py
```

当前该文件应包含：

- Qt6 password echo 回归
- dropEvent guard
- reset 即时清理
- 中文默认 / 英文 fallback
- workflow strip 状态同步

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
  tests/test_sm2_sm4_workbench_qt6_regressions.py
```

必须 0 failed / 0 skipped。

## 6. WSLg 中文人工检查

不要设置 `QT_QPA_PLATFORM=offscreen`：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v02
```

检查：

1. 标题、按钮、说明、密码对话框正常显示中文；
2. 不出现方框、问号乱码或字符截断；
3. 密码输入仍为掩码；
4. 顶部六阶段流程条可见；
5. EMPTY/CONFIGURING 时第 1 步高亮；
6. READY_FOR_MATERIAL / MATERIAL_READY 时第 2 步高亮；
7. WRAPPING 时第 3 步高亮；
8. PAYLOAD_ENCRYPTED 时第 4 步高亮；
9. READY_TO_ASSEMBLE 时第 5 步高亮；
10. PACKAGE_ASSEMBLED 时第 6 步高亮；
11. u2/u4 正常解密、u1 NOT_RECIPIENT、force-try 失败等原功能不变。

### 第 4 步的观察顺序

`InteractiveSession.stage` 表示“当前整体状态”，不是强制线性播放进度。如果先把全部接收者的 SM2 封装都做完，再执行媒体加密，则媒体加密完成后所有组包条件同时满足，状态会直接进入 `READY_TO_ASSEMBLE`，流程条从第 3 步进入第 5 步；这是正常状态机行为。

若要明确观察第 4 步 `PAYLOAD_ENCRYPTED`，使用下面顺序：

```text
生成 K
→ 先将 K 拖到 SM4-GCM 引擎
→ 此时检查第 4 步高亮
→ 再完成 u2/u4 的 SM2 密钥封装
→ 进入第 5 步
```

标准完整业务流程仍可按“先封装 u2/u4，再加密媒体”的顺序执行。

## 7. 字体 fallback

若中文显示为 tofu/空方框，不要改 Python 编码或密码代码。先运行：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-workbench-v02-en \
  --lang en_US
```

确认英文 fallback 正常。随后报告 WSL 中可用字体情况。

## 8. 报告模板

```text
## Target
branch:
commit:
worktree:

## Automated
compileall:
qt6/ui regressions:
workbench smoke:
workbench real GmSSL:
focused total:
skips:

## Chinese WSLg
Chinese glyph rendering:
password dialog Chinese:
workflow strip:
stage transitions:
full crypto interaction:

## English fallback
--lang en_US:

## Repository state
git status --short:
commit/push performed:

## Conclusion
PASS / FAIL
```

本轮不要修改密码算法，不要重新设计 backend，不要 commit/push。发现 UI 问题先报告最小复现。
