# SM2 + SM4 后端运行与测试手册

> 分支：`sm2-sm4-backend`
>
> 目标：让另一个开发 Agent（例如 Claude）能够**直接拉取代码、安装运行环境、执行真实 GmSSL 集成测试，并把结果完整报告回来**。
>
> 当前阶段只验证后端。**不要实现或修改前端/可视化。**

---

## 1. 后端做什么

本分支实现的是：

**基于 SM2 + SM4-GCM 的多接收者混合加密（Multi-Recipient Hybrid Encryption）**。

核心流程：

1. 每个用户持有独立 SM2 密钥对 `(PK_i, SK_i)`。
2. 每次广播生成新的 16-byte SM4 内容密钥 `K`。
3. 媒体文件只使用 `K` 做 **一次 SM4-GCM 加密**。
4. 对授权集合 `S` 中每个用户，使用其 SM2 公钥独立封装同一个 `K`。
5. 所有人收到同一个 `.smre` 广播包。
6. 授权用户用自己的 SM2 私钥恢复 `K`，再通过 SM4-GCM 认证并恢复文件。
7. 非授权用户没有自己的 wrapped key；`force-try` 可以真实尝试“错误私钥解别人 wrapped key”，用于后续交互式教学演示。

这不是常数长度密文头的经典 Broadcast Encryption；wrapped-key 头大小随 `|S|` 线性增长。

---

## 2. 代码位置

核心代码：

```text
src/sm2_sm4_mre/
├── __init__.py
├── __main__.py
├── backend.py
├── cli.py
├── envelope.py
├── errors.py
├── gmssl_backend.py
├── package.py
├── service.py
└── types.py
```

测试：

```text
tests/test_sm2_sm4_mre_core.py
tests/test_sm2_sm4_mre_package_validation.py
tests/test_sm2_sm4_mre_gmssl_integration.py
```

依赖文件：

```text
requirements-sm2-sm4.txt
```

更详细的设计说明：

```text
docs/sm2-sm4-backend.md
```

---

## 3. Claude / Agent：直接拉取这个分支

如果本机还没有仓库：

```bash
git clone --branch sm2-sm4-backend --single-branch \
  https://github.com/xcy040722-eng/broadcast-encryption.git
cd broadcast-encryption
```

如果已经有仓库：

```bash
git fetch origin
git switch sm2-sm4-backend
git pull --ff-only origin sm2-sm4-backend
```

确认：

```bash
git branch --show-current
git status
```

必须看到：

```text
sm2-sm4-backend
```

测试前不要改源码。

---

## 4. 推荐运行环境

优先建议：

```text
WSL2 / Ubuntu 22.04 或 24.04
Python 3.10+
CMake
GCC / build-essential
GmSSL native shared library
GmSSL-Python
pytest
```

本项目的 `gmssl_backend.py` 使用官方 GmSSL-Python 绑定。它依赖系统中的 `libgmssl` 动态库，所以**只 `pip install gmssl-python` 不一定够**。

---

## 5. 创建 Python 虚拟环境

Linux / WSL：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell（如果选择原生 Windows）：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

后续命令默认均在虚拟环境中执行。

---

## 6. 安装 native GmSSL（WSL / Ubuntu 推荐路径）

先安装编译工具：

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake git
```

然后编译安装官方 GmSSL：

```bash
cd /tmp
git clone https://github.com/guanzhi/GmSSL.git
cd GmSSL
mkdir -p build
cd build
cmake ..
make -j"$(nproc)"
make test
sudo make install
sudo ldconfig
```

检查：

```bash
gmssl help
ldconfig -p | grep gmssl || true
```

如果 `gmssl` 能运行但 Python 仍找不到 `libgmssl.so`，临时检查：

```bash
export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}
```

然后重新运行 Python 诊断。

> 不要用“只编译静态库”的方式安装；GmSSL-Python 需要 shared library。

---

## 7. 安装 Python 依赖

回到本仓库根目录：

```bash
pip install -r requirements-sm2-sm4.txt
```

依赖当前是：

```text
gmssl-python
pytest>=8.0
```

---

## 8. 环境诊断：必须先做

```bash
python - <<'PY'
import sys
print("python:", sys.version)

try:
    import gmssl
    print("gmssl-python import: OK")
    print("GMSSL_PYTHON_VERSION:", getattr(gmssl, "GMSSL_PYTHON_VERSION", "<missing>"))
    print("GMSSL_LIBRARY_VERSION:", getattr(gmssl, "GMSSL_LIBRARY_VERSION", "<missing>"))
except Exception as exc:
    print("gmssl-python import: FAILED")
    print(type(exc).__name__ + ":", exc)
    raise

from src.sm2_sm4_mre.gmssl_backend import GmsslBackend
print("GmsslBackend.is_available():", GmsslBackend.is_available())
backend = GmsslBackend()
print("SM4 key size:", backend.sm4_key_size)
print("SM4 GCM IV size:", backend.sm4_gcm_iv_size)
print("SM4 GCM tag size:", backend.sm4_gcm_tag_size)
PY
```

这里必须成功。

如果 `GmsslBackend.is_available()` 是 `False`，不要继续把 integration test 的 `SKIPPED` 当成通过；先解决 native GmSSL / Python binding 环境。

---

## 9. 第一阶段测试：纯 Python / 业务逻辑

先检查语法：

```bash
python -m compileall -q src/sm2_sm4_mre tests/test_sm2_sm4_mre_*.py
```

再执行：

```bash
pytest -q tests/test_sm2_sm4_mre_core.py
pytest -q tests/test_sm2_sm4_mre_package_validation.py
```

这些测试覆盖 envelope、package、授权/越权逻辑、tamper、fresh randomness、文件 round-trip 等后端行为。

任何失败都要保存完整 traceback。

---

## 10. 第二阶段测试：真实 GmSSL 集成

执行：

```bash
pytest -q -rs tests/test_sm2_sm4_mre_gmssl_integration.py
```

### 验收标准

目标必须是：

```text
1 passed
```

如果看到：

```text
1 skipped
```

说明环境里真实 GmSSL backend 没有可用。对于本阶段来说，**skip 不能算最终通过**。

请根据 `-rs` 给出的 skip reason 修复环境，然后重跑。

---

## 11. 第三阶段：一次跑完本方案全部测试

```bash
pytest -q -rs tests/test_sm2_sm4_mre_*.py
```

验收目标：

```text
所有 SM2/SM4 MRE tests passed
0 failed
0 skipped（真实 GmSSL 环境已经正确安装时）
```

旧 CHW25 / UI 测试不是这一阶段的验收重点，不要因为旧方向留下的测试而去修改本方案后端。

---

## 12. CLI 端到端实测

### 12.1 创建测试文件

不依赖图片素材，直接生成一个二进制测试文件：

```bash
python - <<'PY'
from pathlib import Path
Path("demo.bin").write_bytes((b"SM2-SM4-MRE-DEMO\n" * 65536))
print("demo.bin created")
PY
```

### 12.2 生成四个用户的 SM2 密钥

```bash
python -m src.sm2_sm4_mre keygen --user u1 --password pass-u1 --key-root keys
python -m src.sm2_sm4_mre keygen --user u2 --password pass-u2 --key-root keys
python -m src.sm2_sm4_mre keygen --user u3 --password pass-u3 --key-root keys
python -m src.sm2_sm4_mre keygen --user u4 --password pass-u4 --key-root keys
```

应该生成：

```text
keys/u1/sm2_public.pem
keys/u1/sm2_private.pem
...
keys/u4/sm2_public.pem
keys/u4/sm2_private.pem
```

### 12.3 向 S={u2,u4} 广播

```bash
python -m src.sm2_sm4_mre encrypt \
  --input demo.bin \
  --output demo.smre \
  --recipient u2=keys/u2/sm2_public.pem \
  --recipient u4=keys/u4/sm2_public.pem
```

检查广播包公开元数据：

```bash
python -m src.sm2_sm4_mre inspect --package demo.smre
```

应能看到 recipient set 中只有：

```text
u2
u4
```

### 12.4 授权用户 u2 解密

```bash
python -m src.sm2_sm4_mre decrypt \
  --package demo.smre \
  --user u2 \
  --private-key keys/u2/sm2_private.pem \
  --password pass-u2 \
  --output recovered-u2.bin
```

应返回：

```text
SUCCESS
```

验证文件完全相同：

```bash
cmp demo.bin recovered-u2.bin
sha256sum demo.bin recovered-u2.bin
```

### 12.5 授权用户 u4 解密

```bash
python -m src.sm2_sm4_mre decrypt \
  --package demo.smre \
  --user u4 \
  --private-key keys/u4/sm2_private.pem \
  --password pass-u4 \
  --output recovered-u4.bin
```

然后：

```bash
cmp demo.bin recovered-u4.bin
```

必须一致。

### 12.6 非授权用户 u1 正常尝试

```bash
python -m src.sm2_sm4_mre decrypt \
  --package demo.smre \
  --user u1 \
  --private-key keys/u1/sm2_private.pem \
  --password pass-u1 \
  --output should-not-exist-u1.bin
```

预期：失败，CLI 返回非 0；原因应为该用户不是 recipient / 没有自己的 wrapped-key entry。

`should-not-exist-u1.bin` 不应得到可用明文。

### 12.7 u1 强制攻击 u2 的 wrapped key

这是教学演示最重要的负向路径之一：

```bash
python -m src.sm2_sm4_mre force-try \
  --package demo.smre \
  --attacker-user u1 \
  --attacker-private-key keys/u1/sm2_private.pem \
  --password pass-u1 \
  --target-recipient u2 \
  --output should-not-exist-force.bin
```

预期：

```text
失败
```

且不得释放合法媒体明文。

这里不是 UI 人为禁止操作，而是真实执行错误 SM2 私钥对 `u2` wrapped key 的解密尝试。

---

## 13. 测试结束后的检查

执行：

```bash
git status --short
```

测试产生的：

```text
.venv/
keys/
demo.bin
demo.smre
recovered-*.bin
should-not-exist-*.bin
```

都是本地测试产物，不应该提交到仓库。

尤其严禁提交真实或测试 SM2 私钥。

---

## 14. 如果失败，Claude 必须怎样处理

### 情况 A：GmSSL native library 找不到

优先检查：

```bash
gmssl help
ldconfig -p | grep gmssl
python -c "import gmssl; print(gmssl.GMSSL_LIBRARY_VERSION)"
```

不要修改密码算法来绕过环境问题。

### 情况 B：GmSSL-Python API 与 `gmssl_backend.py` 不匹配

记录：

```text
Python version
GmSSL native version
GmSSL-Python version
完整 traceback
出错 API 名称
```

**不要静默改用另一个叫 `gmssl` 的第三方包，也不要把 SM4-GCM 降级成 ECB。**

先报告差异，再针对官方 API 修正 adapter。

### 情况 C：integration test 被 skip

把它视为：

```text
环境未完成
```

而不是：

```text
测试通过
```

### 情况 D：业务测试失败

不要先重写算法。先给出：

1. 失败测试名；
2. traceback；
3. 最小复现命令；
4. 推测发生在哪个模块；
5. 建议的最小修复。

---

## 15. Claude 最终报告模板

运行完成后，请按下面格式返回：

```text
## Environment
OS:
Python:
GmSSL native:
GmSSL-Python:
GmsslBackend.is_available():

## Test results
compileall:
core tests:
package validation tests:
gmssl integration tests:
all sm2_sm4_mre tests:

## CLI E2E
keygen u1-u4:
encrypt S={u2,u4}:
inspect recipients:
u2 decrypt + cmp:
u4 decrypt + cmp:
u1 normal decrypt:
u1 force-try u2:

## Failures / warnings
完整错误或 None

## Repository state
git status --short:

## Conclusion
PASS / BLOCKED
```

最终只有在真实 GmSSL integration test 通过、u2/u4 round-trip 成功、u1 负向路径失败时，才可报告 `PASS`。

---

## 16. 当前阶段禁止事项

在上述后端验收完成前，不要：

- 实现 Qt / QML / Streamlit 前端；
- 设计播放式动画；
- 修改旧 CHW25 可视化；
- 更换密码库而不说明；
- 将 SM2+SM4 误称为常数头广播加密；
- 将测试密钥、私钥、`.smre` 测试包提交到 GitHub。

后端完成后，前端才进入下一阶段，并且必须采用：

```text
用户交互动作
    ↓
真实 backend API
    ↓
真实密码学操作
    ↓
状态/对象改变
```

而不是预录或自动播放的动画。
