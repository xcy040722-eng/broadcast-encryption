# SM2 + SM4 多接收者交互工作台

本分支是课程项目的最终实现方向：使用国产密码算法 **SM2 + SM4-GCM** 构造一个可交互、可解释、可验证的多接收者混合加密 / 广播式分发系统。

> 准确定位：本项目不是常数大小头部、复杂撤销或 Succinct-LWE 类严格学术 Broadcast Encryption 构造。媒体主体只加密一次；每个授权接收者增加一个 SM2-wrapped 内容密钥 `E[i]`，因此头部随接收者数量增长。

## 1. 核心思路

一次广播只生成一个 128-bit SM4 内容密钥 `K`：

```text
K <- {0,1}^128
```

媒体只执行一次 SM4-GCM：

```text
(C_M, T) = SM4-GCM.Enc(K, IV, M, AAD)
```

对于授权集合 `S` 中的每个用户 `i`：

```text
Envelope_i = Encode(package_id, i, K)
E_i = SM2.Enc(PK_i, Envelope_i)
```

最终所有人收到同一份 `.smre` 广播包：

```text
P = manifest || {E_i}_{i in S} || C_M
```

示例 `S={u2,u4}` 时，包中只有 `E[u2]`、`E[u4]` 和一份媒体密文。

## 2. 三条接收端验证路径

### 授权用户

```text
SK[u2] -> E[u2] -> SM2 解封 -> K -> SM4-GCM 解密/认证 -> M
```

预期状态：

```text
SUCCESS
```

### 非接收者

```text
u1 not in S -> 包中不存在 E[u1]
```

预期状态：

```text
NOT_RECIPIENT
```

### 错误私钥强制尝试

```text
SK[u1] -> E[u2] -> native SM2 unwrap failure
```

预期状态：

```text
SM2_UNWRAP_FAILED
```

失败不是 UI 人为拦截，而是实际调用 GmSSL 后端得到的密码学结果。

## 3. 交互式可视化

默认启动中文界面：

```bash
python -m src.sm2_sm4_workbench --workspace /tmp/sm2-sm4-demo
```

英文回退：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-demo-en \
  --lang en_US
```

界面包含：

- 六阶段真实状态条；
- 用户 / 接收者集合 `S`；
- 发送端密码学对象关系图；
- `K -> PK[u2] / PK[u4] / SM4-GCM` 真实拖拽操作；
- 广播包组装；
- 接收端真实解密路径；
- `SUCCESS / NOT_RECIPIENT / SM2_UNWRAP_FAILED` 三类可视化；
- 点击对象查看“作用 / 输入 / 核心关系 / 输出 / 本次真实状态 / 安全边界”；
- 状态驱动的答辩提示条。

答辩提示只读取安全快照，不会自动执行密码学操作或推进状态机。

## 4. 安全展示边界

默认 UI / trace 不显示：

```text
raw SM4 K
SM2 private key bytes / PEM body
```

界面只使用安全投影信息，例如：

```text
SM3 fingerprint
backend status
user / target id
GCM authentication result
output filename
```

因此可通过发送端 / 接收端 `K` 的 SM3 指纹一致性证明“恢复的是同一个 K”，而无需把 `K` 本身暴露在屏幕上。

## 5. 环境

推荐环境：

```text
Windows 11
└─ WSL2 Ubuntu 24.04
   ├─ Python 3.12
   ├─ PySide6
   ├─ GmSSL native
   └─ GmSSL-Python 2.2.2 + repository ABI patch
```

项目已验证过 native GmSSL / GmSSL-Python 的 ctypes ABI 漂移问题。不要手工长期修改 `site-packages`；使用仓库脚本：

```bash
bash scripts/bootstrap_gmssl_wsl.sh
```

现有环境可检查：

```bash
python tools/patch_gmssl_python_abi.py --check
```

详细说明：

```text
SM2_SM4_GMSSL_ABI.md
SM2_SM4_BACKEND_RUNBOOK.md
```

## 6. 运行测试

当前冻结验收基线（v0.5）：

```text
43 passed
0 failed
0 skipped
```

测试覆盖：

- backend core；
- package validation；
- InteractiveSession；
- real GmSSL integration；
- PySide6 smoke；
- Qt6 regressions；
- sender relation canvas；
- receiver path canvas；
- principle inspector；
- localized result presenter；
- defense guide。

完整测试命令见：

```text
SM2_SM4_WORKBENCH_V050_RUNBOOK.md
```

## 7. 推荐答辩流程

3～5 分钟演示建议：

1. 生成 u1-u4 真实 SM2 密钥；
2. 设置 `S={u2,u4}` 并选择媒体；
3. 生成唯一 SM4 内容密钥 `K`；
4. 在关系图拖 `K -> PK[u2]`；
5. 拖 `K -> PK[u4]`；
6. 拖 `K -> SM4-GCM`，强调媒体只加密一次；
7. 组装 `.smre`；
8. u2 正常解密：`SUCCESS`；
9. u1 正常解密：`NOT_RECIPIENT`；
10. `SK[u1] -> E[u2]`：`SM2_UNWRAP_FAILED`；
11. 点击关系图 / 接收端节点解释公式与实时状态；
12. 最后展示发送端 K 指纹与授权接收端恢复 K 指纹相同。

## 8. 项目结构

```text
src/sm2_sm4_mre/              真实密码后端、包格式、InteractiveSession
src/sm2_sm4_workbench/        PySide6 交互工作台与安全可视化投影
tests/                        单元 / 集成 / UI 回归测试
scripts/bootstrap_gmssl_wsl.sh 环境搭建
tools/patch_gmssl_python_abi.py ABI 检查与受控修复
```

## 9. 进一步阅读

首先阅读：

```text
SM2_SM4_PROJECT_GUIDE.md
SM2_SM4_DEFENSE_CHECKLIST.md
```

前者是完整原理、架构和答辩技术底稿；后者是答辩前最后检查清单。
