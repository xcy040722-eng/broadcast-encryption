# SM2 + SM4 多接收者广播加密项目说明

本文件用于课程答辩、代码交付和后续维护。项目默认中文界面，保留 `--lang en_US` 英文回退。

## 1. 项目定位

本项目实现一个基于国产密码算法的多接收者混合加密系统：

- SM2：为每个接收者封装同一个 SM4 内容密钥 K；
- SM4-GCM：对媒体/文件主体只加密一次；
- SM3：仅用于 UI/trace 中显示不可逆指纹，证明对象一致性；
- `.smre`：保存 manifest、每个授权接收者的 SM2 密钥封装 E[i]、以及唯一一份媒体密文。

它适合教学上说明“同一份密文包由多个授权用户分别恢复同一个内容密钥，再解密同一份媒体密文”的广播式场景。

需要准确表述：该方案是**多接收者混合加密 / 广播式分发方案**，不是具有常数大小头部、复杂撤销结构或 Succinct-LWE 安全证明的严格学术 Broadcast Encryption 构造。接收者数量增加时，增长的是每个接收者一份 `E[i]` 的密钥封装头部；媒体主体不会重复加密。

## 2. 核心密码流程

设授权集合为：

```text
S = {u2, u4}
```

每个用户拥有 SM2 密钥对：

```text
(PK_i, SK_i)
```

一次广播只生成一个随机 SM4 内容密钥：

```text
K <- {0,1}^128
```

### 2.1 媒体主体

媒体 M 只进行一次 SM4-GCM 认证加密：

```text
(C_M, T) = SM4-GCM.Enc(K, IV, M, AAD)
```

### 2.2 接收者密钥封装

对每个 `i in S`，构造包含 `package_id + user_id + K` 的 KeyEnvelope：

```text
Envelope_i = Encode(package_id, i, K)
E_i = SM2.Enc(PK_i, Envelope_i)
```

因此示例中只生成：

```text
E[u2]
E[u4]
```

不会生成 `E[u1]` 或 `E[u3]`。

### 2.3 广播包

最终：

```text
P = manifest || {E_i}_{i in S} || C_M
```

所有用户看到的是同一份 `.smre` 文件。

## 3. 授权用户如何解密

以 u2 为例：

```text
SK[u2]
  -> E[u2]
  -> SM2.Dec
  -> Envelope(package_id, u2, K)
  -> 验证 package_id / user_id
  -> 恢复 K
  -> SM4-GCM.Dec(K, IV, C_M, T, AAD)
  -> 明文 M
```

成功时 UI 应展示：

```text
SUCCESS
授权验证通过：SM2 成功恢复内容密钥，SM4-GCM 解密与认证成功。
```

发送端 K 的 SM3 指纹与接收端恢复 K 的 SM3 指纹应完全相同，但 UI 不显示原始 K。

## 4. 两类失败路径

### 4.1 非接收者

u1 正常解密时，广播包没有 `E[u1]`：

```text
NOT_RECIPIENT
非接收者：广播包中不存在属于 u1 的密钥封装 E[u1]。
```

这不是 UI 禁止操作，而是包结构中确实没有 u1 的密钥封装。

### 4.2 错误私钥强制尝试

故意执行：

```text
SK[u1] -> E[u2]
```

真实 native GmSSL 通常在 SM2 解封阶段直接失败：

```text
SM2_UNWRAP_FAILED
错误私钥：SK[u1] 无法解封 E[u2]。
```

后续 K、SM4-GCM、明文步骤均不会伪装为成功。

## 5. 为什么使用 SM4-GCM

SM4 负责高吞吐量媒体加密，SM2 只处理很小的内容密钥封装。这样可以避免用公钥密码直接加密大文件。

GCM 同时提供：

- 机密性；
- 完整性；
- 认证标签校验；
- 被篡改或使用错误 K 时拒绝释放最终明文。

项目实现采用临时文件 + 认证成功后原子释放的策略，避免在 GCM 认证失败时留下最终明文文件。

## 6. InteractiveSession 不变量

前端不是预设动画。鼠标操作直接驱动真实 `InteractiveSession`：

```text
鼠标/按钮
  -> PySide6 Widget / Canvas
  -> InteractiveSession
  -> GmsslBackend
  -> native GmSSL
```

已经锁定的核心不变量：

1. 每次广播只生成一个 K；
2. `wrap_for(u2/u4)` 和 `encrypt_payload()` 使用的是同一个 K；
3. 媒体主体只执行一次 SM4-GCM 加密；
4. `assemble_package()` 不重新加密媒体；
5. 生成会话材料后，授权集合 S 与媒体被冻结；
6. reset 保留用户 SM2 密钥，但清除本轮广播临时状态；
7. 默认 snapshot/trace/UI 不暴露 raw K 或 SM2 私钥正文。

## 7. UI 的四个教学层

### 7.1 六阶段流程条

```text
1 用户与授权集合
2 内容密钥 K
3 SM2 密钥封装
4 SM4-GCM 媒体加密
5 组装广播包
6 接收端验证
```

流程条反映真实 `SessionStage`，不是播放时间轴。

### 7.2 发送端关系图

```text
              SM4 内容密钥 K
              /            \
       PK[u2] -> E[u2]   PK[u4] -> E[u4]
              \            /
               \          /
媒体 M -> SM4-GCM -> 媒体密文
                  
E[u2] + E[u4] + 媒体密文 -> 广播包
```

将 K 拖到 PK 节点会真实调用 `session.wrap_for()`；将 K 拖到 SM4-GCM 会真实调用 `session.encrypt_payload()`。

### 7.3 接收端路径

成功：

```text
SK[u2] -> E[u2] -> SM2 解封 -> K -> SM4-GCM -> M
```

非接收者：

```text
SK[u1] -> 不存在 E[u1] -> 停止
```

错误私钥：

```text
SK[u1] -> E[u2] -> SM2 解封失败 -> 停止
```

### 7.4 原理 / 本次状态

点击关系图或接收端路径中的对象，可查看：

- 作用；
- 输入；
- 核心关系 / 运算；
- 输出；
- 本次真实状态；
- 安全边界。

实时值来自安全投影 `SessionSnapshot` / `ReceiverCanvasState`，而非伪造示例。

## 8. 答辩提示条

v0.5 增加“答辩提示”区域。它只根据当前安全状态告诉演示者下一步建议：

```text
生成密钥 / 选择 S / 选择媒体
-> 生成 K
-> 拖 K 完成 SM2 封装和 SM4-GCM
-> 组装 .smre
-> u2 SUCCESS
-> u1 NOT_RECIPIENT
-> u1 -> u2 SM2_UNWRAP_FAILED
-> 点击对象解释原理与真实状态
```

重要：提示条**不会自动执行任何密码操作，也不会自动推进状态机**。所有关键步骤仍由用户手动操作。

## 9. 代码结构

```text
src/sm2_sm4_mre/
  gmssl_backend.py          native GmSSL 适配
  service.py                KeyGen / wrap / SM4-GCM / decrypt
  interactive_session.py    前端真实状态模型
  package.py                .smre 格式
  envelope.py               package_id + user_id + K
  types.py                  typed results / traces

src/sm2_sm4_workbench/
  window.py                 基础 PySide6 工作台
  relation_canvas.py        发送端关系图
  receiver_canvas.py        接收端真实路径
  principle_inspector.py    原理与本次状态
  result_presenter.py       中英文接收结果呈现
  defense_guide.py          手动答辩提示
  defense_workbench.py      最终答辩外壳
```

## 10. GmSSL ABI 注意事项

当前验证组合：

```text
native GmSSL commit: 24ae4827
GmSSL-Python:         2.2.2
```

官方 Python ctypes 绑定与当前 native 结构体存在 ABI 漂移，本仓库包含可重复 patch：

```bash
python tools/patch_gmssl_python_abi.py --check
```

应看到：

```text
ABI CHECK: PASS
sizeof(Sm2Key)=128
sizeof(Sm4Gcm)=296
```

不要绕过 ABI 检查直接调用 native GmSSL，否则旧绑定可能越界写内存并导致延迟段错误。

## 11. 推荐环境

项目已经在以下环境完整验证：

```text
Windows 11
WSL2 Ubuntu 24.04.4 LTS
WSLg
Python 3.12.x
PySide6 6.x
GmSSL native + gmssl-python 2.2.2 + repository ABI patch
```

一键环境脚本：

```bash
bash scripts/bootstrap_gmssl_wsl.sh
```

中文界面依赖 CJK 字体，bootstrap 会安装 Noto CJK 及常用 Qt/WSLg xcb 依赖。

## 12. 启动

中文版：

```bash
source .venv-sm2-sm4/bin/activate
python tools/patch_gmssl_python_abi.py --check
python -m src.sm2_sm4_workbench --workspace /tmp/sm2-sm4-defense
```

英文回退：

```bash
python -m src.sm2_sm4_workbench \
  --workspace /tmp/sm2-sm4-defense-en \
  --lang en_US
```

## 13. 3～5 分钟答辩演示脚本

推荐提前准备一个小图片或二进制文件。

### 第 1 分钟：说明方案

讲述：

> 本系统使用 SM2 + SM4-GCM 实现多接收者混合加密。大文件只用一个随机 SM4 内容密钥加密一次，再针对每个授权用户使用其 SM2 公钥分别封装同一个 K。随着用户数量增长，增长的是密钥封装头部，而不是媒体密文主体。

### 第 2 分钟：发送端操作

1. 为 u1-u4 生成真实 SM2 密钥；
2. 选择 `S={u2,u4}`；
3. 选择媒体；
4. 生成 K；
5. 在关系图拖 `K -> PK[u2]`；
6. 拖 `K -> PK[u4]`；
7. 拖 `K -> SM4-GCM`；
8. 强调 `payload_encryption_count=1`；
9. 组装 `.smre`。

### 第 3 分钟：授权与拒绝

先 u2：

```text
SUCCESS
```

展示完整绿色接收路径，并点击“恢复的内容密钥 K”，说明发送端和接收端 K 指纹相同。

再 u1：

```text
NOT_RECIPIENT
```

说明广播包中根本不存在 `E[u1]`。

最后 force try：

```text
SK[u1] -> E[u2]
SM2_UNWRAP_FAILED
```

说明这是 native GmSSL 真正拒绝，而不是 UI 禁止按钮。

### 最后 30～60 秒：点击原理层

点击：

- SM2 密钥封装；
- SM4-GCM；
- 广播包；
- SM2 解封。

说明 UI 显示公式、输入输出与本次真实 fingerprint，但不显示 raw K / private key。

## 14. 老师可能追问的问题

### Q1：为什么不直接用 SM2 加密图片？

SM2 是公钥密码，更适合小数据/密钥封装；大媒体用 SM4 对称加密更高效。因此采用混合加密。

### Q2：为什么叫“多接收者”？

同一份媒体密文只生成一次，不同授权接收者各有自己的 SM2-wrapped K；所有人接收同一个 `.smre` 包。

### Q3：u1 为什么解不了？

正常路径中包内没有 `E[u1]`；即使故意拿 `SK[u1]` 去解 `E[u2]`，真实 SM2 解封失败。

### Q4：如何证明 u2 解出的 K 就是发送端的 K？

UI 不泄露 K 本身，而是比较发送端和接收端 K 的 SM3 指纹。授权用户成功时两者完全一致。

### Q5：媒体是否对 u2/u4 分别加密？

不是。媒体仅进行一次 SM4-GCM 加密；按用户增长的是 E[i] 密钥封装。

### Q6：这是不是严格学术意义上的 Broadcast Encryption？

准确说，本项目是使用国产 SM2+SM4 构造的广播式多接收者混合加密系统。它展示广播分发核心语义，但头部随接收者数量线性增长，不宣称具有高级 BE 方案的常数头部、撤销或 Succinct-LWE 等性质。

## 15. 当前验收基线

在 v0.4.0 前已经通过：

```text
38 passed
0 failed
0 skipped
```

覆盖 backend、ABI、真实 GmSSL round-trip、InteractiveSession、PySide6 smoke、Qt6 regressions、发送端 canvas、接收端 canvas、原理 inspector 和本地化 result presenter。

v0.5 新增答辩提示层后，应继续保证所有密码学/交互测试无回归。
