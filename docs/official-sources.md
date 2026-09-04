# 官方论文与源码核查（WW25 / CHW25）

> 阶段：M1.5 · 对应 Prompt 02
> 性质：**仅资料定位与源码可行性分析**，不涉及任何代码实现。
> 核查日期：2026-09-04

## 0. 结论摘要

| 核查项 | 结论 |
|---|---|
| 两篇是否同一研究路线 | **是**（同一批作者圈、同一套技术：ℓ-succinct LWE + Matrix Commitment → DBE / registered ABE） |
| WW25 对应论文 | Wee & Wu, *Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE* |
| CHW25 对应论文 | Champion, Hsieh & Wu, *Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE* |
| 官方源码 | **两篇均【未发现】任何官方 / 作者提供的源码** |
| 可运行 demo | **两篇均【未发现】** |
| 源码是否对应论文 | 不存在源码，故无「是否对应」的核对问题 |
| 语言 / 构建 / 依赖 | 忠实实现需重型格密码工具（离散高斯采样、G-trapdoor、格同态计算、大模数运算、NIZK） |
| 是否适合 Python 项目 | 忠实实现**不适合**（需 Sage / C++）；教学简化 toy **可尝试** |
| 是否适合课程设计 | 忠实实现 **RED**；教学简化 **YELLOW** |

---

## 1. 论文 A：CHW25（老师点名的那篇）

- **标题**：*Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE*
- **作者**：
  - Jeffrey Champion（UT Austin）
  - Yao-Ching Hsieh（University of Washington）
  - David J. Wu（UT Austin）
- **年份**：2025
- **ePrint**：[2025/044](https://eprint.iacr.org/2025/044)（PDF：[2025/044.pdf](https://eprint.iacr.org/2025/044.pdf)）
- **正式发表**：CRYPTO 2025，Part III，pp. 3–34，DOI `10.1007/978-3-032-01881-6_1`，Springer LNCS
- **分类**：Public-key cryptography
- **作者主页**：
  - Jeff Champion：https://www.cs.utexas.edu/~jchamps/ （页面提供 ePrint 与 Slides 链接，**无代码链接**）
  - David J. Wu：https://www.cs.utexas.edu/~dwu4/
  - Yao-Ching Hsieh：`[UNCERTAIN]` 未检索到独立主页
- **Slides**：https://iacr.org/submit/files/slides/2025/crypto/crypto2025/123/123_slides.pdf
- **官方源码**：**未发现**（作者主页、ePrint、Google/GitHub 检索均无实现链接）

## 2. 论文 B：WW25

- **标题**：*Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE*
- **作者**：
  - Hoeteck Wee（NTT Research, CIS Lab）
  - David J. Wu（UT Austin）
- **年份**：2025
- **ePrint**：[2025/1039](https://eprint.iacr.org/2025/1039)（PDF：[2025/1039.pdf](https://eprint.iacr.org/2025/1039.pdf)）
- **正式发表**：CRYPTO 2025，Part III，DOI `10.1007/978-3-032-01881-6_7`，Springer LNCS（ePrint 标注为 CRYPTO 2025 的 major revision）
- **分类**：Public-key cryptography
- **作者主页**：
  - Hoeteck Wee：https://cis.ntt-research.com/cis-people/wee-profile/ （NTT CIS 主页，无 GitHub）
  - David J. Wu：https://www.cs.utexas.edu/~dwu4/
- **官方源码**：**未发现**

## 3. 源码核查明细

- **David J. Wu 的 GitHub（`dwu4`）**：通过 GitHub API 拉取其公开仓库，仅见 `fhe-si`（Brakerski 全同态加密）、`lattice-snarg`（格 SNARG）、`genome-privacy` 等，**没有** broadcast encryption / registered ABE / succinct LWE / matrix commitment 相关实现。
- **Hoeteck Wee**：未发现公开 GitHub 账号；以 NTT CIS 主页发布论文，未见代码。
- **Jeff Champion**：主页仅挂论文与 Slides，无代码。
- **社区实现**：检索「broadcast encryption + python / succinct LWE + implementation」等关键词，未发现针对这两篇论文的第三方实现。检索到的 Python 广播加密项目（如 FlexBroadcast、Proxy-Reencryption）对应的是**别的论文**（配对/证书类广播），与本论文无关。
- **结论**：两篇均为「只有论文、无参考实现」的前沿成果。

## 4. 技术栈与依赖评估（用于判断实现可行性）

忠实实现这两篇论文，至少需要以下重型格密码工具：

| 依赖项 | 用途 | Python 可行性 |
|---|---|---|
| 大模数 `Z_q` 矩阵运算（q 为 sub-exponential 级） | 全方案基础 | 需 numpy + 高精度，性能瓶颈 |
| 离散高斯采样 | KeyGen / 噪声 | 纯 Python 难；需 Sage 或专用采样器 |
| G-trapdoor（Micciancio–Peikert 12）采样 | Setup / 矩阵承诺 trapdoor | 需 Sage/格库 |
| 格同态计算（GSW13 / BGG+14） | ABE 策略求值 | 需 Sage/格库 |
| Matrix Commitment（[Wee25]） | 核心原语 | 无现成实现 |
| NIZK PoK（CHW25 的 registered ABE 需要） | 防恶意注册 | 需额外 NIZK 实现 |
| Random Oracle（ROM） | CHW25 自适应安全 | 可用标准哈希替代 |

**结论**：忠实实现是「前沿 CRYPTO 2025 工程化」级别的工作，通常以 C++ / Sage 完成，**超出课程设计 Python 项目的合理范围**。

---

## 5. 「老师那句话」对应哪篇论文、哪个构造

- 老师点名论文名 *Registered ABE and Adaptively-secure Broadcast Encryption from Succinct LWE* → **CHW25**（ePrint 2025/044）。
- 老师要求「实现讲义上**基于矩阵承诺的广播加密算法**」→ 讲义（即本项目的 `论文PPT.pdf`）里专门有一节 **「DBE: The Basic Approach」** 和 **「DBE For Unbounded Users [WW25]」**，用 **Matrix Commitment** 构造 **分布式广播加密（DBE）**。因此「基于矩阵承诺的广播加密算法」最直接对应的是 **WW25 的 DBE 构造**（CHW25 的 DBE 是其自适应安全增强版，同属一条技术线）。

一句话：**「矩阵承诺的广播加密」= 两篇论文共用的 Matrix-Commitment-based DBE；老师引用的论文名是 CHW25；讲义详细推导的是 WW25 的无界用户 DBE。**

---

## 6. GREEN / YELLOW / RED 判定

| 级别 | 对象 | 判定 |
|---|---|---|
| **GREEN** | 可作为本项目高级实现（faithful） | **无** |
| **YELLOW** | 可研究/移植，但成本高 | **教学简化版矩阵承诺广播加密（TOY）**：以小参数、玩具模数复现 `C·v_i = m_i − A·z_i`（low-norm opening）机制，展示「授权用户能打开、非授权用户不能」的思想，**明确标注为教学简化、不声称安全** |
| **RED** | 不建议作为本项目实现 | **两篇论文的忠实实现（PAPER-FAITHFUL）**：无源码、依赖重型格工具、参数规模非 Python 可承受 |

### RED 的具体 blocker

1. **无官方源码**，需从公式零开始实现，任何符号/参数理解偏差都会导致结果不可信。
2. **ℓ-succinct LWE 假设**本身是 2024–2025 年的前沿假设，其参数选择（sub-exponential modulus-to-noise ratio）没有成熟的工程参数指引。
3. **Matrix Commitment / 稀疏承诺**的「指数位置高效承诺」依赖精巧的格构造（`pp = (B, W, T)` 及 `[I⊗B | W]·T = I⊗G` 的 trapdoor 关系），实现门槛高。
4. **离散高斯采样 / G-trapdoor / 格同态求值**在纯 Python 中性能与正确性都难以保证。
5. **NIZK PoK**（CHW25 registered ABE 所需）是另一套独立的重型组件。
6. 这是 2025 年刚发表的 CRYPTO 论文，尚无可借鉴的工程实现或参数报告。

---

## 7. 来源

- CHW25 ePrint：https://eprint.iacr.org/2025/044
- WW25 ePrint：https://eprint.iacr.org/2025/1039
- CRYPTO 2025 Part III（Springer LNCS）：DOI `10.1007/978-3-032-01881-6`（CHW25 为 `_1`，WW25 为 `_7`）
- David J. Wu 主页：https://www.cs.utexas.edu/~dwu4/ ；GitHub：https://github.com/dwu4
- Hoeteck Wee 主页：https://cis.ntt-research.com/cis-people/wee-profile/
- Jeff Champion 主页：https://www.cs.utexas.edu/~jchamps/
