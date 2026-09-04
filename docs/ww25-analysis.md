# WW25 / CHW25 技术分析（Matrix Commitment 与广播加密）

> 阶段：M1.5 · 对应 Prompt 08
> 性质：**技术理解与可行性分析，禁止直接写完整代码。**
> 核查日期：2026-09-04

## 1. 两篇论文的关系

### 1.1 是同一研究路线吗？

**是。** 两篇论文共享同一套技术主干，属于同一作者圈（David J. Wu 均为作者）在同一时期的工作：

```
ℓ-succinct LWE 假设
      │
      ▼
Matrix Commitment（矩阵承诺，[Wee25]）
      │
      ├──► WW25：DBE（无界用户）+ registered ABE（无界用户）
      │         · 选择性安全（selective）
      │         · 透明 setup（从 decomposed LWE）
      │
      └──► CHW25：DBE（自适应安全）+ registered ABE（有界用户，电路策略）
                · 自适应安全（adaptive，ROM）
                · 更弱的可证伪假设（ℓ-succinct LWE）
```

### 1.2 哪篇是 WW25、哪篇是 CHW25？

| 简称 | 论文 | 作者 | ePrint | 关键词 |
|---|---|---|---|---|
| **WW25** | *Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE* | Hoeteck Wee, David J. Wu | 2025/1039 | **无界用户**、选择性安全、透明 setup |
| **CHW25** | *Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE* | Jeffrey Champion, Yao-Ching Hsieh, David J. Wu | 2025/044 | **自适应安全**、有界用户、ROM |

> 命名规则：WW25 = **W**ee–**W**u；CHW25 = **C**hampion–**H**sieh–**W**u。

### 1.3 两者分别解决什么问题？

- **WW25**：解决「用户数量**无界**」问题——在不需要预先固定用户总数的情况下，用固定大小的公开参数和 `poly(λ, log N)` 的参数实现分布式广播加密与注册式 ABE。这是**首个无 iO/Witness-Encryption、无界用户或透明 setup 的构造**。
- **CHW25**：解决「**自适应安全**」问题——在 ROM 里，让敌手无需在安全游戏开始时预先承诺挑战集合，即可保证安全性；同时给出**首个基于可证伪格假设的自适应安全 DBE**，以及首个支持**任意有界深度电路策略**的注册式 ABE（且密文独立于属性长度）。

### 1.4 各技术要素出现在哪里？

| 要素 | 位置 |
|---|---|
| **Matrix Commitment** | 两篇的**核心原语**（都是用它把多个公钥「压成」一个短主公钥） |
| **Succinct LWE** | 两篇的**安全假设基础**（WW25 另用 decomposed LWE 实现透明 setup） |
| **Broadcast Encryption（DBE）** | 两篇都构造（WW25 = 无界/选择性；CHW25 = 自适应） |
| **Registered ABE** | 两篇都构造（WW25 = 无界/选择性；CHW25 = 电路策略/属性选择性） |

---

## 2. Matrix Commitment 详解

来源：讲义 `论文PPT.pdf` 中的「Matrix Commitments [Wee25, adapted]」一节，以及 WW25 论文（NSF PAR 公开摘录）中作为正式原语的描述。

### 2.1 是什么

「**向量到向量的承诺**（vector commitment to vectors）」：不是承诺一个标量，而是承诺一个**矩阵**（或一组向量），并能为**单个列/位置**单独打开。

### 2.2 核心公式与各符号含义

讲义给出的打开关系（对第 `i` 个位置）：

```
C · v_i = m_i − A · z_i      （z_i 为 low-norm）
```

| 符号 | 含义 |
|---|---|
| `C` | **承诺矩阵**（公开的、短的聚合结果，即「commitment」）。可看作把多个向量压缩后的指纹 |
| `v_i` | 第 `i` 个位置的 **opening 向量**（用于证明位置 `i` 承诺的内容） |
| `m_i` | 被承诺的消息（矩阵）的**第 `i` 列**，即位置 `i` 上真正要承诺的内容 |
| `A` | 公开参数里的**公开矩阵**（与 trapdoor 相关，论文里也写作 `B`） |
| `z_i` | **low-norm 的 opening 随机性**（一个范数很小的向量） |

论文（WW25 正文 / NSF 摘录）里的等价形式为：

```
C · V_L = M − B · Z        （或  C · V_L = M · G_L − B · Z）
```

对应关系：`C` = 承诺矩阵，`B` = 公开矩阵（即讲义里的 `A`），`M` = 被承诺矩阵（第 `i` 列即 `m_i`），`V_L` = 验证矩阵（第 `i` 列即 `v_i`），`Z` = low-norm opening 矩阵（第 `i` 列即 `z_i`）。

### 2.3 关键概念

- **low-norm（低范数）**：`z_i` 的范数很小。在格密码里，低范数向量是「稀有且难伪造」的——给定 `A`，找到满足某关系的低范数 `z_i` 等价于解 SIS/格上的困难问题，这是安全的根基。
- **commitment（承诺）**：`C` 是绑定（binding）且（可选）隐藏（hiding）的；给定 `C` 无法轻易改成承诺别的内容。
- **opening（打开）**：持有正确 `(v_i, z_i)` 的人能证明位置 `i` 承诺的是 `m_i`；没有的人无法为任意 `m_i'` 伪造 opening。
- **确定性 / 随机化**：矩阵承诺可以是确定性的，也可以是随机化的（CHW25 的自适应安全技巧就用到「随机化承诺」）。

### 2.4 公开参数结构（论文版）

```
pp = (B, W, T)
B ∈ Z_q^{n×m}
W ∈ Z_q^{2m²n×m}
T ∈ Z_q^{(2m²+1)m×2m³}      满足  [ I_{2m²} ⊗ B | W ] · T = I_{2m²} ⊗ G
```

`T` 是一个针对「succinct LWE 实例（维度 `2m²`）」的 **trapdoor**，`G` 是 gadget 矩阵。这套结构支持**稀疏承诺**：即使承诺矩阵有指数多的列 `L`，只要只有 `poly` 个非零位置，也能高效地承诺并局部打开/验证——这正是「无界用户」的关键。

> `[UNCERTAIN]` 上述 `pp = (B, W, T)` 的确切维度来自 NSF 公开摘录，完整严谨的参数关系需以 WW25 论文正文为准，此处仅作理解性转述。

---

## 3. 为什么 Matrix Commitment 能作为广播加密的基础

核心思想（讲义「DBE: The Basic Approach」）：

1. **每个用户采样一个 dual-Regev 密钥对**并公开公钥 `pk_i`（低范数秘密钥 `sk_i`）。
2. **加密者**对广播集合 `S` 内的公钥做「**Merkle 式的矩阵承诺压缩**」：把 `S` 内用户的公钥通过矩阵承诺聚合成一个短承诺（即主公钥 / 承诺 `C`）。
3. **加密**：加密者向承诺 `C` 对应的「虚拟主公钥」用 dual-Regev 加密消息 `μ`。
4. **解密**：用户 `i` 用**本地 opening `v_i`** 打开位置 `i`，把「对主公钥的密文」转化成「对 `pk_i` 的 dual-Regev 密文」，再用自己的 `sk_i` 解密。

一句话：**矩阵承诺把「N 个用户各自的公钥」无损压成一个短承诺，加密者只需针对这一个短承诺加密；而每个用户能靠自己的 opening 把密文「翻译」成针对自己公钥的密文。** 这就是它作为广播加密基础的原因——它是「聚合公钥」的代数化实现。

对照讲义的 DBE 无界用户构造（WW25）：

- **公开参数**：`pp` 含承诺参数 `com`（含矩阵 `A`）。
- **用户公钥**：`pk_i = A·t_i`（`t_i` 为 low-norm 秘密钥）。
- **加密 μ∈{0,1} 到集合 S**（噪声省略）：

  ```
  对每个位置 i：承诺「若 i∈S 则 μ + pk_i，否则 0」
  → 承诺值 T（短的主密文 / 承诺）
  ```

- **打开关系**（对每个 i）：

  ```
  v_i = μ + pk_i − A·z_i          （z_i 公开且 low-norm）
  ```

- **解密**：只有用户 `i` 能算出

  ```
  t_i^T v_i = t_i^T μ + t_i^T pk_i − t_i^T A z_i
           ≈ t_i^T μ + (低范数噪声项)
  ```

  利用 `pk_i = A t_i` 的 dual-Regev 结构，消去后得到关于 `μ` 的 dual-Regev 密文，进而恢复 `μ`。非授权用户没有对应位置的 `t_i`，无法打开，也就无法恢复 `μ`。

> `[UNCERTAIN]` 上述解密推导中的精确代数关系（`t_i^T A z_i` 如何与 `pk_i` 项消去）在 PDF 文本抽取中符号有缺失，最终公式以 WW25 论文第 5 章（Remark 5.38 之前的 DBE 构造）为准；此处描述的是机制层面，而非可实现的逐项公式。

---

## 4. 方案四算法概览（WW25 DBE / CHW25 DBE）

> 仅为理解性归纳，**不是可实现的完整规格**；逐项公式请以论文为准。

| 算法 | 内容 |
|---|---|
| **Setup(1^λ)** | 生成公开参数 `pp`：含矩阵承诺参数（`B, W, T`）与 dual-Regev 公共矩阵 `A`。WW25 为透明 setup；CHW25 有结构化 CRS（大小 `n² + |x|²`） |
| **KeyGen / Register(pp, i)** | 用户采样 low-norm 秘密钥 `t_i`，公开 `pk_i`（WW25 无界用户逐个注册；CHW25 有界用户数 n） |
| **Encrypt(pp, {pk_i}, S, μ)** | 用矩阵承诺把 `S` 内公钥「压缩」成承诺；向承诺加密 `μ`（在位置 `i∈S` 处 commit `μ + pk_i`，否则 0） |
| **Decrypt(pp, {pk_i}, sk_i, ct)** | 用户 `i` 用 opening `v_i` 把密文翻译成针对 `pk_i` 的 dual-Regev 密文，用 `t_i` 解密 |

### 4.1 正确性

- 授权用户 `i∈S`：拥有 `t_i`，能由 opening `v_i` 恢复 `μ`（见第 3 节）。
- 非授权用户 `j∉S`：承诺中位置 `j` 承诺的是 `0` 而非 `μ+pk_j`，且没有对应 opening，无法把密文翻译成对 `pk_j` 的密文。

### 4.2 安全性依赖

- **WW25**：选择性安全，基于 **succinct LWE**（或 decomposed LWE，用于透明 setup）。
- **CHW25**：自适应安全（ROM），基于 **succinct LWE**。其关键技巧是：在加密时加入一个**随机化承诺**（随机量 `r_0` 由 random oracle 派生），去除敌手对聚合公钥的对抗性控制，从而在 ROM 中可编程地模拟挑战密文。

---

## 5. Succinct LWE 的角色

- **Succinct LWE**（[Wee24]，CRYPTO 2024 *Circuit ABE* 引入）是 LWE 的一族「简洁」推广：在给定一个相关矩阵的「新鲜 trapdoor」时，LWE 仍是困难的。
- 它是**可证伪（falsifiable）、实例无关**的假设，比之前的 **private-coin evasive LWE** 更弱、更可信（后者近年被 [VWW22, BŚW24, BDJ+24] 给出反例攻击）。
- 在本项目里，succinct LWE 同时支撑：矩阵承诺的绑定/隐藏、DBE 与 registered ABE 的安全性。它是「从格假设做紧凑密文」的核心工具。

---

## 6. GREEN / YELLOW / RED 与 blocker

| 级别 | 对象 | 判定 |
|---|---|---|
| **GREEN** | 忠实实现（PAPER-FAITHFUL） | **无** |
| **YELLOW** | 教学简化版矩阵承诺广播加密（TOY） | 可做：以小参数、玩具模数复现 `C·v_i = m_i − A·z_i` 的承诺/打开机制，展示「授权用户能打开、非授权用户不能」；**明确标注教学简化、不声称安全** |
| **RED** | 忠实实现 WW25 / CHW25 | 不建议（见下） |

### blocker（忠实实现不可行的具体原因）

1. **无官方源码 / 无参考实现**，参数选择无工程先例。
2. **ℓ-succinct LWE 参数规模**（sub-exponential modulus-to-noise）超出 Python 可承受范围。
3. **Matrix Commitment 的 trapdoor 关系** `[I⊗B | W]·T = I⊗G` 需要 G-trapdoor 采样（MP12），实现门槛高。
4. **离散高斯采样**在纯 Python 中正确性与性能均难保证（通常需 Sage）。
5. **格同态求值**（GSW13/BGG+14）用于 ABE 策略，是另一套重型组件。
6. **CHW25 还需 NIZK PoK**（防恶意注册），进一步抬高成本。
7. 两篇均为 2025 年新论文，工程化尚无人踩坑。

---

## 7. 结论与建议

1. **忠实实现两篇论文 = RED**，不纳入本项目主实现。
2. **「基于矩阵承诺的广播加密」应落地为教学简化 TOY 版本**（YELLOW）：在完成经典 Baseline（CS/SD）闭环之后，用**小参数 + 明确标注**实现矩阵承诺的核心机制，作为「高级方向」的演示，展示 `C·v_i = m_i − A·z_i` 与「聚合公钥 → 广播加密」的思想链条。
3. 本项目的**主实现与答辩核心仍是经典 Baseline（NNL01 CS → SD）**，WW25/CHW25 作为「前沿方向 + 教学简化」的补充说明，符合 CLAUDE.md「高级方案过难可回退」的要求。

## 8. 来源

- WW25：https://eprint.iacr.org/2025/1039
- CHW25：https://eprint.iacr.org/2025/044
- 讲义：`papers/论文PPT.pdf`（Matrix Commitments / DBE / Succinct LWE 各节）
- Wee, *Circuit ABE with poly(depth,λ)-Sized Ciphertexts and Keys from Lattices*, CRYPTO 2024（ℓ-succinct LWE 假设出处）
- Wee & Wu, *Succinct vector, polynomial, and functional commitments from lattices*, EUROCRYPT 2023（向量/函数承诺基础）
