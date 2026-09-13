# CHW25 DBE 动态可视化设计

> 阶段：Phase 3 · 动态可视化设计（**本文档只做设计，不写 UI**）
> 依据：`src/chw25_dbe/`（Construction 6.4 教学实现）+ `src/chw25_dbe/trace.py`（真实运行数据）
> **铁律**：动画**必须直接消费 `trace.py` 的真实运行数据**；**不允许**为动画伪造公式数值。

---

## 0. 设计原则

1. **数据真实**：所有数字来自一次真实 `decrypt_with_trace()` 调用（含 `c3`、`c2_dot_r_i`、各 `c1_dot_y_*`、`z_before_center`、`z_centered`、`noise_residual`、`decoded_mu`）。
2. **不暴露秘密**：私钥向量、会话密钥明文**不显示**，只显示指纹或派生标量（见 §3）。
3. **不在 UI 层重算密码学**：UI 只做「取数 → 展示 → 动画」，不做任何 DBE 运算。
4. **不影响现有 CS 页面**：新增独立页面，不改 `web/app.py`（见 §9）。

---

## 1. 主流程（固定）

```
① Setup → ② KeyGen → ③ Select S → ④ DBE wrap AES key → ⑤ Broadcast
        → ⑥ Authorized / Unauthorized Decrypt → ⑦ Recover K → ⑧ AES media recovery
```

| 步 | 动作 | 产出的可视对象 |
|---|---|---|
| ① Setup | `setup(Params)` | `A, p, R(=e_i), t`, `params_id` |
| ② KeyGen | `keygen(pp, i)` × N | 每用户 `pk_i=(W_i,{y_{i,j}}_{j≠i})`, `sk_i=y_{i,i}` |
| ③ Select S | 用户多选 | `recipient_ids` |
| ④ DBE wrap | `encrypt_session_key(pp, pks, S, K)` | `K`(32B) → 256 个 bit 密文 |
| ⑤ Broadcast | `build_package` + `package_aad` | 广播包（含 `keyset_id`、`wrapped_key`） |
| ⑥ Decrypt | `decrypt_with_trace(...)` / `decrypt_bit(...)` | 逐 bit trace |
| ⑦ Recover K | `bits_to_bytes` | 32B `K` + SHA-256 指纹 |
| ⑧ AES recovery | `decrypt_file_for_user` | 原媒体文件 + SHA-256 比对 |

**默认演示场景**：`N=4, S={2,4}`（与 spec 和测试一致）。

---

## 2. 页面布局

```
┌───────────────────────────────────────────────────────────────────────┐
│  CHW25 DBE 动态可视化          [N=4] [S: ☑u1 ☐u2 ☑u3 ☐u4]  ▶ Run Demo │  ← 顶部控制条
├──────────────────────────────┬────────────────────────────────────────┤
│  左栏：状态面板 (固定)        │  右栏：主舞台 (动画区)                  │
│  ┌────────────────────────┐  │  ┌──────────────────────────────────┐  │
│  │ Setup                  │  │  │  当前步骤的大幅可视化              │  │
│  │  params_id  n4-m8-...  │  │  │  (SVG，由 JS 驱动动画)             │  │
│  │  keyset_id  a1b2...    │  │  │                                    │  │
│  ├────────────────────────┤  │  │  ┌─ ① Setup 树/参数 ─────────┐     │  │
│  │ KeyGen (N=4)           │  │  │  └───────────────────────────┘     │  │
│  │  u1 ◆ u2 ◆ u3 ◆ u4 ◆   │  │  │  ┌─ ② KeyGen 密钥卡片 ───────┐     │  │
│  ├────────────────────────┤  │  │  └───────────────────────────┘     │  │
│  │ Recipients  S={2,4}    │  │  │  ... (随步骤切换)                  │  │
│  ├────────────────────────┤  │  └──────────────────────────────────┘  │
│  │ AES Session Key        │  │  ┌──────────── 时间线滑块 ───────────┐  │
│  │  K: [HIDDEN] sha256:.. │  │  │ ◀ ▮▮▮▮▮▮▮▮ ▮▮▮▮▮▮▮ ▶  [▶][⏸][↺]│  │
│  ├────────────────────────┤  │  └──────────────────────────────────┘  │
│  │ 解密结果               │  │                                        │
│  │  u2: ✓ authorized      │  │  (取消/阈值动画、AES 恢复动画等在此区) │
│  │  u4: ✓ authorized      │  │                                        │
│  │  u1: ✗ NotRecipient    │  │                                        │
│  │  u3: ✗ NotRecipient    │  │                                        │
│  └────────────────────────┘  │                                        │
└──────────────────────────────┴────────────────────────────────────────┘
```

- **顶部**：`N`、`S` 选择 + `▶ Run Demo`（一键 `N=4,S={2,4}`）。
- **左栏**：常驻状态（public 信息 + 解密结果）；**秘密只显示 `[HIDDEN]` + 指纹**。
- **右栏**：主舞台（SVG 动画）+ 时间线控制。
- 两栏均用 Streamlit 原生组件（`st.columns` / `st.markdown`）搭骨架，**动画区用 HTML 组件**。

---

## 3. 每一步展示哪些变量 / 公开 vs 秘密

| 步骤 | 展示变量 | 公开？ |
|---|---|---|
| ① Setup | `n, m, q, N`、`params_id`、`A`、`p`、`R`、`t`、`keyset_id` | **公开**（全部可显示） |
| ② KeyGen | `W_i`（矩阵）、`{y_{i,j}}_{j≠i}`（**注意：这些在 pk 里，是公开的**）、`sk_i=y_{i,i}` | `W_i`/`y_{i,j}` **公开**；`y_{i,i}` **秘密** |
| ③ S | `recipient_ids` | 公开 |
| ④ wrap | `K` 长度、`K` 的 SHA-256 指纹、256 个 bit 密文计数 | `K` **秘密**（仅指纹） |
| ⑤ Broadcast | `version/algorithm/params_id/keyset_id/recipient_ids/original_*/body`、`wrapped_key` 大小 | 公开 |
| ⑥ Decrypt | `c3`、`c2ᵀr_i`、各 `c1ᵀy_{i,i}/y_{0,i}/y_{j,i}`、`z_centered`、`noise_residual`、`decoded_mu` | 公开（**派生标量**） |
| ⑦ Recover K | `K` 指纹、`bits_to_bytes` 结果 | `K` **秘密**（仅指纹） |
| ⑧ AES | 原/解密文件 SHA-256 | 公开 |

### 3.1 秘密变量的处理规则

| 变量 | 为何秘密 | UI 处理 |
|---|---|---|
| `y_{i,i}`（`sk_i`） | 用户秘密钥 | **不显示**；仅显示「已由 u_i 本地持有」 |
| `r_i`（= `e_i`） | 教学替代下是几何基向量 | 可显示（非秘密，但标注「教学替代」） |
| AES 会话密钥 `K` | 保护文件内容 | 显示 `[HIDDEN]` + `sha256(K)[:8]` |
| `c1ᵀy_{i,i}` 等**派生标量** | 是投影值，不泄露向量 | **可显示**（动画核心） |

> **注意**：`{y_{i,j}}_{j≠i}` 在论文里**是公钥的一部分**（`pk_i=(W_i,{y_{i,j}}_{j≠i})`），因此**可以显示**。这一点与直觉相反，需在 UI 上明确标注。

---

## 4. 动画时间线（一次 Run Demo）

```
t=0.0s  ── ① Setup        显示 pp 生成（A,p,R,t 逐个淡入），params_id / keyset_id 计算
t=1.5s  ── ② KeyGen       4 张密钥卡片依次出现；每张显示 W_i 与 {y_{i,j}}_{j≠i}；
                           标注「y_{i,i} 留在本地（不显示）」
t=3.5s  ── ③ Select S     S={2,4} 高亮；u1/u3 变灰
t=4.5s  ── ④ DBE wrap     32B 密钥 K → 256-bit 网格；每格「加密」动画（K 淡出为密文）
t=7.0s  ── ⑤ Broadcast    广播包卡片组装（含 keyset_id、recipient_ids=…）
t=8.5s  ── ⑥ Decrypt      进入 cancellation 子动画（§5，约 6s）
t=14.5s ── ⑦ Recover K    256 bit 逐格「恢复」→ 拼成 32B K → 显示 SHA-256
t=17s   ── ⑧ AES recovery 媒体文件解密 → 原/解密 SHA-256 比对 → ✓
t=19s   ── 结束            定格总结（覆盖：u2/u4 ✓、u1/u3 ✗）
```

- 时间线可拖动（scrub）、可暂停/重播；
- **每一步的数值必须在该步开始时已从 Python 侧取得**（见 §8 数据契约）。

---

## 5. Cancellation 动画（核心，§5–§6）

### 5.1 u2/u4 成功路径

以 **u2** 为例，动画把 `z = c3 + c2ᵀr_i − c1ᵀ(y_ii + y_0i + Σ_{j∈S\{i}} y_{j,i})` 拆成**累加账本**：

```
        ┌──────────── 累加账本（实时数值）────────────┐
起始      c3                      = 92839
第 1 加    + c2ᵀ r_i               = +14253      → 运行和 2363 (mod q)
第 2 减    − c1ᵀ y_{i,i}           = −(−33805)   → 运行和 …
第 3 减    − c1ᵀ y_{0,i}           = −(−25207)   → 运行和 …
第 4 减    − c1ᵀ y_{4,i}           = −(9011)     → 运行和 52364
                                                     ↑ = μ⌊q/2⌋ (μ=1)
噪声       noise_residual          = 0
```

动画表现：
1. 每一项从右栏「飞入」账本，高亮对应的数学符号；
2. **每减一项 `c1ᵀ y`，同步在对面显示对应的 `W` 项被「抵消」**（用同一个 `y` 的图示连线到 `c2ᵀr_i` 里的 `W r_i`）；
3. 运行和（running sum）以进度条形式逼近 `⌊q/2⌋`；
4. 最终定格：`z = μ⌊q/2⌋ + noise_residual`，`noise_residual` 极小。

> **必须**：每一项的数值直接取自 `trace["c1_dot_y_ii"]` 等字段，**不允许**在 JS 里重算。

### 5.2 u1/u3 非授权路径

以 **u1**（1 ∉ S）为例：

```
① 用户 u1 尝试解密 →  UI 立即显示 "u1 ∉ S"
② 调用 decrypt_bit(...) 返回 DecryptResult(authorized=False, bit=None)
③ 动画：账本无法建立——因为 u1 的位置未被承诺（在本实现中，S 不含 u1）
④ 高亮差异：u2 的账本能凑出 s^T p + s^T t_2；u1 没有对应的量
⑤ 结果卡片："NotRecipient（不是『解密为 0』）"
```

**重点**：UI 必须区分 `authorized=False, bit=None`（非接收者）与 `authorized=True, bit=0`（真 0）——**绝不能把非接收者显示为"成功解密为 0"**。

### 5.3 逐项 cancellation 动画的实现要点

- 账本每一项 = `{label, value, op, running_sum}`，全部来自 trace；
- 「抵消连线」用 SVG 贝塞尔曲线连接 `−c1ᵀy_{j,i}` 与 `c2ᵀr_i` 中的对应分量；
- **逐项**顺序：`y_{i,i}` → `y_{0,i}` → 各 `y_{j,i}`（j 升序），与 trace 的 `c1_dot_y_ji` 键顺序一致。

---

## 6. Noise residual 与 q/4 阈值尺

在主舞台底部常驻一把**阈值尺**（SVG）：

```
 −q/2 ────────── −q/4 ────── 0 ────── +q/4 ────────── +q/2
   │               ├───────────┼───────────┤             │
   │            【解码 1 区】  【解码 0 区】  【解码 1 区】 │
                          ▲
                     z_centered = 52364  (μ=1)
                     noise_residual = 0
```

- **读数来自** `trace["z_centered"]` 与 `trace["noise_residual"]`；
- 指针实时移动（配合 §5 累加账本的运行和）；
- 用颜色区分 `[-q/4, q/4)`（解码 0）与其他（解码 1）；
- 右下角显示 `noise_residual` 占阈值的比例（真实运行约 **0.057%**）与裕度。

> 边界情形（真实存在）：当 μ=1 且噪声使 `z` 越过 `⌊q/2⌋` 时，`z_centered` 会显示为约 `−⌊q/2⌋`（仍在"解码 1 区"）。UI 需正确展示这一真实行为，并说明它不影响判定。

---

## 7. AES session key 动画（加密 → 256 bit 恢复 → media decrypt）

```
阶段 A：加密态
  ┌── 32 bytes = 256 bits ──┐
  │ ▨▨▨▨ ▨▨▨▨ ... (256 格)  │   每格 = 一个 CHW25 bit 密文（ξ,c1,c2,c3）
  └──────────────────────────┘   K 以 [HIDDEN] 显示
              │  encrypt_session_key()
              ▼
  wrapped_key = 256 个密文（约 42 KB）

阶段 B：逐 bit 恢复（授权用户）
  第 k 格：decrypt_bit(...) → authorized=True, bit=b_k
  格子从「密文态」翻转为「明文 bit」；k 从 0..255 逐格动画
  非授权用户：所有格子保持「密文态」，并标注 NotRecipient

阶段 C：拼装 K
  256 个已知 bit → bits_to_bytes() → 32B K
  显示 K 的 SHA-256 指纹（与加密前的指纹比对 ✓）

阶段 D：media recovery
  decrypt_file_for_user() → 原媒体文件
  并排显示 原文件 SHA-256 == 解密 SHA-256 ✓
```

- **每格翻转的 bit 值来自真实解密结果**；非授权路径下格子**不翻转**；
- 「加密前 K 指纹」与「恢复后 K 指纹」并排比对，是"恢复正确"的最直观证据。

---

## 8. Streamlit 与 HTML/CSS/JS/SVG 的职责划分

| 层 | 职责 | 不做什么 |
|---|---|---|
| **Streamlit**（`st.*`） | 页面布局、控件（N/S 选择）、会话状态（`st.session_state`）、**调用 Python DBE**、采集 trace、把 trace 序列化为 JSON 传给组件 | **不做动画**、不在前端重算密码学 |
| **HTML/CSS/JS/SVG**（`st.components.v1.html`） | 渲染 SVG、驱动时间线动画、累加账本、阈值尺、bit 网格翻转、AES 恢复流程动画 | **不发起** DBE 运算、**不伪造**任何数值 |

### 8.1 数据契约（Streamlit → 组件）

组件通过一个 JSON 载荷接收**一次真实运行的**全部数值：

```json
{
  "params": {"n":4,"m":8,"q":104729,"N":4,"half_q":52364,"threshold":26182},
  "params_id": "n4-m8-q104729-N4",
  "keyset_id": "<sha256>",
  "recipient_ids": [2,4],
  "session_key_sha256_8": "<8 hex>",
  "wrapped_key_size_bytes": 42903,
  "decrypt_traces": {
    "2": { "authorized": true, "c3": 92839, "c2_dot_r_i": 14253,
           "c1_dot_y_ii": -33805, "c1_dot_y_0i": -25207,
           "c1_dot_y_ji": {"4": 9011}, "z_centered": 52364,
           "noise_residual": 0, "decoded_mu": 1 },
    "4": { ... },
    "1": { "authorized": false, "decoded_mu": 0, "reason": "i ∉ S" },
    "3": { "authorized": false, "decoded_mu": 0, "reason": "i ∉ S" }
  },
  "media": {"original_sha256": "...", "recovered_sha256": "..."}
}
```

- 载荷**完全来自** `decrypt_with_trace` / `decrypt_bit` / `keyset_id` 的真实返回值；
- JS 侧**只读**该载荷，不生成任何数值。

### 8.2 组件封装建议

```
web/
├── app.py                      # 现有 CS 页面（**不改**）
├── pages/
│   └── 2_chw25_dbe.py          # 新增：CHW25 可视化页（Streamlit 多页机制）
└── components/
    └── chw25_stage.html        # SVG + JS 动画组件（被 st.components.v1.html 加载）
```

---

## 9. 如何保持现有 CS 页面不受影响

1. **不改 `web/app.py`**：CHW25 可视化放在 **Streamlit 多页**目录 `web/pages/2_chw25_dbe.py`，通过侧边栏导航进入。
2. **不改 `web/cs_visualize.py` / `web/media_page.py`**：CHW25 使用**独立的**组件文件 `web/components/chw25_stage.html`。
3. **不共享可变状态**：CHW25 页使用自己的 `st.session_state` 命名前缀（如 `chw25_*`），与 CS 页的 `tree/node_keys/header/...` 隔离。
4. **不修改 `src/`**：UI 只调用 `src/chw25_dbe/` 的公开 API 与 `src/file_crypto/` 的 AES 能力。
5. **回归保障**：新增 `tests/test_ui_smoke.py` 风格的 CHW25 组件数据契约测试（校验载荷字段齐全、来自真实 trace）。

---

## 10. 验收关注点（实现后）

| 项 | 判据 |
|---|---|
| 数据真实性 | 动画显示的每个数字都可在 `trace` 中找到同值字段 |
| 非接收者语义 | u1/u3 显示 `NotRecipient`，**不显示** "解密为 0" |
| 秘密不泄露 | `K` 与 `y_{i,i}` 明文字节不出现在页面任何位置 |
| CS 无回归 | `web/app.py` 及其页面行为不变；原有 147 测试全通过 |
| 边界正确 | μ=1 跨 `⌊q/2⌋` 的 `z_centered` 正确展示 |

---

## 11. 来源

- `src/chw25_dbe/`（Construction 6.4 教学实现）、`src/chw25_dbe/trace.py`（真实 trace）
- `docs/chw25-dbe-implementation-spec.md`（实现规格与教学替代项）
- CHW25 论文 §6.1 Construction 6.4 / Theorem 6.5 / 6.6
- 现有 CS 可视化：`web/app.py`、`web/cs_visualize.py`（作为布局与组件风格的参考，**不改动**）
