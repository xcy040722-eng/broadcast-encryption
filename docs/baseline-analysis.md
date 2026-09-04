# 经典广播加密方案 Baseline 分析

> 阶段：M1 · Prompt 01
> 目标：为课程设计选定一个「早期/经典」广播加密 Baseline，作为完整可运行闭环的基础。

## 1. 方案总览比较表

| 维度 | Fiat–Naor (FN93) | Complete Subtree (CS, NNL01) | Subset Difference (SD, NNL01) | Boneh–Gentry–Waters (BGW05) | Delerablée (Del07) | Boneh–Waters (BW06) |
|---|---|---|---|---|---|---|
| 论文 | *Broadcast Encryption* | *Revocation and Tracing Schemes for Stateless Receivers* | 同左 | *Collusion Resistant Broadcast Encryption with Short Ciphertexts and Private Keys* | *Identity-Based Broadcast Encryption with Constant Size Ciphertexts and Private Keys* | *A Fully Collusion Resistant Broadcast, Trace, and Revoke System* |
| 作者 | A. Fiat, M. Naor | D. Naor, M. Naor, J. Lotspiech | 同左 | D. Boneh, C. Gentry, B. Waters | C. Delerablée | D. Boneh, B. Waters |
| 年份 | 1993 | 2001 | 2001 | 2005 | 2007 | 2006 |
| 安全模型 | k-resilient（至多 k 个合谋者） | 完全抗合谋（信息论） | 完全抗合谋（计算） | 完全抗合谋，选择性安全 | 完全抗合谋，IND-sID-CCA | 完全抗合谋，自适应安全 |
| 密码学假设 | 信息论（1-resilient 用合数/RSA） | 无（信息论安全） | 单向函数 / PRG | BDHE（双线性配对） | GDDHE（双线性配对） | 配对类 q-DHE 系列 |
| 公钥/对称 | 对称 | 对称 | 对称 | 公钥 | 公钥（IBBE） | 公钥 |
| 用户私钥大小 | ∑ᵢ₌₀ᵏ C(n−1,i)（基本）/ O(k log k log n)（主） | O(log N) | O(log² N) | O(1)（2 个群元素） | O(1) | O(√N) |
| 密文大小 | O(k² log² k log n)（主） | O(r log N) | O(r)（约 2r−1） | O(1) | O(1) | O(√N) |
| 公钥大小 | —（对称） | —（对称） | —（对称） | O(n) | O(m)（最大接收集大小） | O(N) |
| 主要数学工具 | 组合 / 子集枚举 / XOR | 二叉树 / PRG | 二叉树 / PRG / Steiner 覆盖 | 椭圆曲线 + 双线性配对 | 椭圆曲线 + 配对 + IBE | 椭圆曲线 + 配对 + 追踪 |
| 实现难度 | 低 | 低 | 中 | 中高 | 中高 | 高 |
| Python 工程难度 | 低（纯 stdlib） | 低（纯 stdlib） | 中（覆盖算法） | 中高（需配对库） | 中高（需配对库） | 高 |
| 可靠开源实现 | 少，自研容易 | 少，自研容易 | 有 C/C++（AACS 生态） | charm/petrelic 等配对库 | 少 | 少 |
| 适合课程设计 | 一般（概念简单但密文大） | **很好** | **很好** | 好（数学美，但需配对） | 一般 | 一般 |
| 适合图片/视频可视化 | 一般 | **很好** | **很好** | 好 | 好 | 一般 |
| 主要优点 | 概念最原始、信息论清晰 | 思想直观、实现极简 | 密文 O(r)、有真实 DRM 背景 | 常数密文/私钥、公钥密码学 | 常数密文、无需预先固定用户数 | 自适应安全 + 可追踪 |
| 主要缺点 | 密文/密钥随 k 快速膨胀 | 密文 O(r log N) 偏大 | 推导/覆盖算法稍复杂 | 需配对库、公钥 O(n) | 依赖较强配对假设 | 实现复杂 |

> 说明：上表 `n`/`N` 为用户总数，`r` 为被撤销用户数，`k` 为合谋上界，`m` 为接收集大小上界。复杂度按各论文原文表述。

## 2. 各方案要点

### 2.1 Fiat–Naor (FN93)
- **来源**：Amos Fiat, Moni Naor, "Broadcast Encryption", CRYPTO 1993, LNCS 773, pp. 480–491, 1994。
- **Setup**：中心为全体用户子集族预分配密钥。基本 k-resilient 方案对每个至多 k 的子集生成独立密钥，用户持有「不含自己的所有子集」对应的密钥。
- **KeyGen**：用户 i 获得所有满足 `i ∉ T`、`|T| ≤ k` 的子集 T 的密钥。
- **Encrypt**：把明文用「仅由非授权用户组成子集」对应的密钥做 XOR 异或加密。
- **Decrypt**：授权用户因为不属于任何被使用子集，能通过异或还原明文。
- **正确性直觉**：非授权用户恰好能拿到被用到的子集密钥，无法还原；授权用户缺少这些密钥，从而 XOR 逆运算成立（信息论意义下的 k-resilient）。
- **定位**：广播加密的「概念原点」，信息论安全思想清晰，但密文/密钥随 k 膨胀，不适合大 n。

### 2.2 Complete Subtree (CS, NNL01)
- **来源**：Dalit Naor, Moni Naor, Jeffrey B. Lotspiech, "Revocation and Tracing Schemes for Stateless Receivers", CRYPTO 2001, LNCS 2139, pp. 41–62。
- **Setup**：把 n 个用户放在完全二叉树的叶子上，每个节点 v 关联一个密钥 `k_v`。
- **KeyGen**：用户（叶子）i 持有从根到叶子路径上所有节点的密钥，共 `O(log N)` 个。
- **Encrypt**：找出一组「覆盖所有授权叶子、且不覆盖任何非授权叶子」的节点集合（Steiner 树对应的子树根），用这些节点的密钥加密会话密钥。
- **Decrypt**：授权用户落在某个被覆盖子树的叶子上，用路径上的某个 `k_v` 解密；被撤销用户不在任何覆盖子树中，无法解密。
- **定位**：Subset-Cover 框架里最简单的一档，信息论安全，代码量最小，最适合作为「打通闭环」的第一版 Baseline。

### 2.3 Subset Difference (SD, NNL01)
- **来源**：同 NNL01。
- **Setup/KeyGen**：节点 v 关联标签，用户持有 `O(log² N)` 个标签，通过 PRG/单向函数派生出「子树差」`S_{v,w}`（v 的子树去掉 w 的子树）的密钥。
- **Encrypt**：把授权集拆成至多 `2r−1` 个互不相交的子树差集合，分别加密会话密钥。
- **Decrypt**：授权用户属于某个 `S_{v,w}`，用其标签派生出对应密钥解密。
- **定位**：密文长度从 CS 的 `O(r log N)` 降到 `O(r)`，是 AACS（DVD/蓝光）实际采用的方案。推导与覆盖算法比 CS 复杂，是 CS 之后的自然进阶。

### 2.4 Boneh–Gentry–Waters (BGW05)
- **来源**：Dan Boneh, Craig Gentry, Brent Waters, "Collusion Resistant Broadcast Encryption with Short Ciphertexts and Private Keys", CRYPTO 2005, LNCS 3621, pp. 258–275。
- **Setup**：生成双线性群 `(G, G_T, e)` 与公共参数，公钥大小 `O(n)`（每个用户一个群元素）。
- **KeyGen**：用户 i 获得私钥 `d_i = g^{γ_i}`（单个群元素）。
- **Encrypt**：选择随机指数 s，密文为 `(g^s, (∏_{i∈S} γ_i)^s · M)`——仅 2 个群元素，常数大小。
- **Decrypt**：授权用户 i 用私钥与配对运算 `e(g^s, g^{γ_i})` 消去 `(∏γ_i)^s`，恢复 M。
- **正确性/安全**：基于 BDHE 假设，非授权用户无法构造出消去因子。
- **定位**：公钥密码学 + 双线性配对的经典结果，常数密文/私钥非常优雅，展示「对称→公钥、线性→常数」的演进；代价是需要配对库（Python 里为 petrelic / charm-crypto）。

### 2.5 Delerablée (Del07)
- **来源**：Cécile Delerablée, "Identity-Based Broadcast Encryption with Constant Size Ciphertexts and Private Keys", ASIACRYPT 2007, LNCS 4833, pp. 200–215。
- **定位**：IBBE，密文与私钥均为常数大小，公钥 `O(m)`（m 为最大接收集大小，可小于总用户数），且无需在 Setup 阶段固定用户总数。安全性基于 GDDHE，达到 IND-sID-CCA。作为 BGW05 之后的 IBE 化改进，依赖更强的配对假设，工程依赖同 BGW05。

### 2.6 Boneh–Waters (BW06)
- **来源**：Dan Boneh, Brent Waters, "A Fully Collusion Resistant Broadcast, Trace, and Revoke System", ACM CCS 2006, pp. 211–220（ePrint 2006/298）。
- **定位**：提出「Augmented Broadcast Encryption」，可同时支撑广播、叛徒追踪、撤销，自适应安全、完全抗合谋、公开可追踪，密文/私钥 `O(√N)`。功能最强，但实现复杂度最高，不适合作为第一版 Baseline。

## 3. 推荐

### A. 最适合课程设计的方案 —— **Subset-Cover（CS 起步，SD 进阶）**
- **理由**：
  1. 对称密钥 + 二叉树 + PRG，**纯 Python（仅用 `hashlib`/`cryptography` 的 PRF）即可实现**，无需椭圆曲线配对库，工程可控。
  2. 树覆盖思想**天然适合可视化**：可以直接画出「授权叶子被哪些子树覆盖、被撤销用户落在覆盖之外」，完美契合课程设计的演示要求。
  3. 有真实工业背景（AACS DVD/蓝光 DRM），答辩时故事性强。
  4. 混合加密接入简单：BE 负责加密「随机会话密钥」，AEAD（AES-GCM）负责文件内容，边界清晰。
- **实施路径**：先以 **Complete Subtree** 打通「Setup→KeyGen→Encrypt→Decrypt→测试→审计→文件加密→可视化」完整闭环，稳定后再把覆盖算法升级为 **Subset Difference** 以体现密文 O(r) 的优化。

### B. 最容易实现的方案 —— **Fiat–Naor 的 1-resilient / 基本 k-resilient**
- **理由**：概念上就是「子集枚举 + XOR」，几十行代码即可跑通；信息论安全不需要任何困难假设，最适合先验证「同一个密文、S 内能解、S 外不能解」这个核心语义。
- **局限**：密文/密钥随 k（或 n）膨胀，不适合大 n 的真实文件场景，只适合作为理解性 Demo（需标注为 TOY/DEMO）。

### C. 最适合展示密码学思想的方案 —— **Boneh–Gentry–Waters (BGW05)**
- **理由**：常数密文（2 个群元素）+ 常数私钥 + 双线性配对消元，是公钥广播加密里最优雅的结果之一，能清晰展示「公钥/配对如何让密文与集合大小脱钩」。
- **局限**：依赖配对库（petrelic/charm-crypto），数学门槛高，且公钥 O(n)。适合作为「高级方向」的补充演示，不建议作为第一版主实现。

## 4. 结论（Baseline 选定）

**主推 Baseline：NNL01 Subset-Cover 框架，先实现 Complete Subtree（CS）打通闭环，再升级 Subset Difference（SD）。**

- CS 实现最小、信息论安全、思想直观、可视化友好，是「早期/经典广播加密算法」的合格代表。
- SD 作为同框架进阶，密文 O(r)，有 AACS 工业背书，可作为 M1 的增强目标。
- Fiat–Naor 与 BGW05 分别作为「最易理解 Demo」与「公钥/配对思想展示」的辅助材料，写入 `docs/research-notes.md` 留档。

## 5. 来源

- Fiat & Naor, *Broadcast Encryption*, CRYPTO 1993 — [zbMATH 0870.94026](https://zbmath.org/0870.94026)
- Naor, Naor & Lotspiech, *Revocation and Tracing Schemes for Stateless Receivers*, CRYPTO 2001 — [ePrint 2001/059](https://eprint.iacr.org/2001/059.pdf) · [zbMATH 1002.94522](https://zbmath.org/?q=an%3A1002.94522)
- Boneh, Gentry & Waters, *Collusion Resistant Broadcast Encryption…*, CRYPTO 2005 — [Stanford abstract](http://theory.stanford.edu/~dabo/abstracts/broadcast.html) · [Semantic Scholar](https://www.semanticscholar.org/paper/Collusion-Resistant-Broadcast-Encryption-with-Short-Boneh-Gentry/93a6a50dd24de94ad8bd5b21f64f0e98a5f298ed)
- Delerablée, *Identity-Based Broadcast Encryption…*, ASIACRYPT 2007 — [zbMATH 1153.94366](https://zbmath.org/1153.94366) · [researchr](https://researchr.org/publication/Delerablee07/bibtex)
- Boneh & Waters, *A Fully Collusion Resistant Broadcast, Trace, and Revoke System*, CCS 2006 — [ePrint 2006/298](https://eprint.iacr.org/2006/298)

## 6. 不确定项

- `[UNCERTAIN]` 各对称方案（FN93/CS/SD）是否有维护良好的 **Python** 官方开源实现：检索结果多为 C/C++（AACS 生态）或分布式广播（FlexBroadcast，配对库），经典对称方案的 Python 实现稀缺，因此本项目的 CS/SD 将**自行实现并严格测试**，不依赖第三方 BE 库。
- `[UNCERTAIN]` BGW05 / Del07 在 Python 配对库（petrelic/charm-crypto）中的现成广播加密封装是否可直接复用，需在进入公钥方向时再逐一验证。
