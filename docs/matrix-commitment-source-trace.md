# Matrix Commitment `[Wee25]` 来源追踪报告

> 阶段：M5 · 引用来源追踪（**不写代码**）
> 任务：在 `papers/论文PPT.pdf` 中确定 `[Wee25, adapted]` 的完整 bibliographic entry，并回答 Matrix Commitment 原语的构造问题。
> **执行结果：追踪在第一步即中止 —— PPT 未提供 `[Wee25]` 的完整引用。按指令"停下来汇报，不自行猜来源"。**
> 状态：**`[UNRESOLVED]` / 已停止，等待审核**

---

## 0. 结论（一句话）

> **`papers/论文PPT.pdf` 没有参考文献/引用页，因此无法在 PPT 范围内确定 `[Wee25]` 的完整 bibliographic entry。**
> 按你的指令（"如果 PPT 没有给 `[Wee25]` 的完整引用，再停下来汇报，不自行猜来源"），**本报告在此停止**，不进入构造研究。

---

## 1. 追踪方法与穷尽性检查

为确认 PPT 是否给出 `[Wee25]` 引用，执行了以下**穷尽检索**（全文 65 页）：

| 检查项 | 方法 | 结果 |
|---|---|---|
| 是否存在参考文献页 | 全文检索 `References` / `Bibliograph` / `[Rr]eference` | **0 命中** |
| `[Wee25]` 出现位置 | 全文检索 `Wee25` | 命中 **5 页**（p23, p24, p25, p31, p45），**均为正文引用标记，无条目** |
| 末页内容 | 读取 p64–p65 全文 | p64 = "Open Problems"；p65 = "Thanks for listening!" + 两个 URL |
| 是否有隐藏引用（PDF annotation / 备注） | 遍历全部 65 页的 annotation | 仅 p30 有 **1 个无内容高亮**（用户标注，非引用） |
| 是否有 speaker notes | 检查 PDF 内嵌 notes | 无 |

**结论：PPT 的引用体系是“只有标记、没有文献表”。** 全文不存在任何 `.bib` / 参考文献列表 / 引用条目。

---

## 2. PPT 中的全部引用标记（实录）

PPT 使用的是**内联引用标记**，但没有对应的文献表。实录如下：

| 标记 | 出现页 | 上下文 |
|---|---|---|
| `[WQZD10, BZ14]` | p3–p8 | Distributed Broadcast Encryption 起源 |
| `[GHMR18, HLWW23]` | p13 | Registered ABE |
| `[Wee24]` | p22 | "Succinct LWE `[Wee24]`: `A` is uniform, `U_i` is uniform" |
| `[AMR25]` | p22 | "Decomposed LWE `[AMR25]`: `A` is structured, `U_i` is uniform, trapdoor is public" |
| **`[Wee25, adapted]`** | **p23, p24, p25** | **Matrix Commitments 标题右上方** |
| **`[Wee25]`** | **p31, p45** | "`[Wee25]` has fixed-size public parameters!" / "can be compressed via `[Wee25]`" |
| `[WW25]` | p31–p49 标题 | "DBE For Unbounded Users `[WW25]`" / "Registered ABE For Unbounded Users `[WW25]`" |
| `[CHW25]` | p54–p63 标题 | "Proving Security `[CHW25]`" |
| `[GSW13, BGGHNSVV14]` | p40–p42 | Lattice-based Homomorphic Computation |
| `[AWY20, LW22]` | p61–p63 | 安全性证明备注 |
| `[FN93]` | （讲义 DBE 讲解） | Broadcast Encryption 起源 |

**没有任何一处给出 `[Wee25]` 的标题、作者、会议或 ePrint 编号。**

---

## 3. PPT 提供的**唯一** URL 信息（p65）

p65 全文（实录）：

```
Thanks for listening!
https://eprint.iacr.org/2025/1039
https://eprint.iacr.org/2025/044
```

| URL | 事实（已核对项目内/已下载的论文标题） |
|---|---|
| `https://eprint.iacr.org/2025/1039` | *Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE*（Wee & Wu）—— 即 PPT 中的 `[WW25]` |
| `https://eprint.iacr.org/2025/044` | *Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE*（Champion, Hsieh & Wu）—— 即 PPT 中的 `[CHW25]`（项目 `papers/` 已有该论文） |

> ⚠️ **这两个 URL 都不是 `[Wee25]` 的 entry。** `[Wee25]`（单作者命名风格）与 `[WW25]`（Wee & Wu）、`[CHW25]`（Champion-Hsieh-Wu）在 PPT 中是**并列且不同**的标记，PPT 未指出 `[Wee25]` 指向上述任一 URL。

---

## 4. 观察（非来源判定，不作为结论）

以下仅为**对 PPT 内部引用命名风格的客观观察**，**不是**对 `[Wee25]` 来源的判定：

- PPT 中 `[Wee24]`、`[Wee25]` 采用「**单姓氏 + 年份**」风格；
- `[WW25]`、`[CHW25]`、`[AMR25]` 采用「**多作者首字母 + 年份**」风格；
- 该风格差异**暗示** `[Wee25]` 可能是一篇**单作者（Wee）2025** 的工作，与 `[WW25]`（Wee & Wu）不是同一篇。

> **但这只是命名风格的推断，PT 未给出任何条目。按你的指令，本报告不据此断定来源、不自行查阅外部论文补齐。**
> 结论：**`[Wee25]` 在 PPT 范围内为 `[UNRESOLVED]`。**

---

## 5. 因此，以下问题**全部无法回答**（`[UNRESOLVED]`）

因为构造来源 `[Wee25]` 未能确定，你列出的问题在**课程资料范围内**均无依据：

| # | 问题 | 状态 | 说明 |
|---|---|---|---|
| Q1 | `pp` 的真实 Setup 是什么？ | **`[UNRESOLVED]`** | PPT 只说 "pp describes `A` and `v_i` for `i∈[L]`"（p24），**无 Setup 算法** |
| Q2 | `A` 如何生成、维度是什么？ | **`[UNRESOLVED]`** | PPT 未给维度或生成方式 |
| Q3 | `v_i` 如何生成？ | **`[UNRESOLVED]`** | PPT 只说 public、low-norm（p24） |
| Q4 | `C` 如何从 `m_1..m_L` 生成？ | **`[UNRESOLVED]`** | PPT 只给接口 `Com(pp, m_1..m_L)→(C, z_1..z_L)`，**无构造** |
| Q5 | `z_i` 如何生成？ | **`[UNRESOLVED]`** | PPT 只说 low-norm（p24） |
| Q6 | 为什么同一个 `C` 能对所有位置满足 `Cv_i+Az_i=m_i`？ | **`[UNRESOLVED]`** | 需构造才能解释；PPT 未给 |
| Q7 | 为什么 `v_i, z_i` 是 low-norm？ | **部分**：PPT 断言其为 low-norm（p24），但**未说明为何必须如此**（设计动机）→ **`[UNRESOLVED]`** |
| Q8 | commitment 的 binding/security 来自什么困难问题？ | **`[UNRESOLVED]`** | PPT 只给安全性式 `s^TA+e^T≈z^T given pp`（p25，标注为 succinct LWE 假设），**未给出 binding 的归约或困难问题陈述** |
| Q9 | `[adapted]` 相比原始构造改了哪些？ | **`[UNRESOLVED]`** | 需要原始 `[Wee25]` 才能对比；PPT 未提供原文 |
| Q10 | 该 primitive 能否与后面的 `t_i=Ay_i`、`m_i=p+t_i/0` DBE 教学构造直接组合？ | **`[UNRESOLVED]`** | 需先确定 primitive 的构造；且组合正确性依赖 `C, v_i, z_i` 的实际性质 |

### 关于 Q10 的一点**范围外提示**（不作为结论）

`docs/matrix-commitment-primitive-coursedata-review.md` 已记录：候选 A/B **不批准**作为最终实现（缺真正 binding）。在 `[Wee25]` 构造未知的前提下，**无法**判断 PPT 的 primitive 能否与 `t_i=Ay_i`、`m_i=p+t_i/0` 直接组合。**需先解决来源问题。**

---

## 6. 需要你裁决的事项

**追 踪 在 此 停 止。** 是否继续，取决于你的决定：

| 选项 | 说明 |
|---|---|
| **A. 由你提供 `[Wee25]` 的准确出处** | 你直接给出标题/ePrint/DOI，我据此研究（最稳妥，符合"不猜来源"） |
| **B. 授权我扩大检索范围** | 例如允许查阅 PPT 提及的 `[Wee24]`（Wee 2024）与外部引文索引去定位 `[Wee25]`；需你**明确授权**，我才会做 |
| **C. 保持 `[UNRESOLVED]`，改用其他方案** | 例如以 `docs/matrix-commitment-dbe-spec.md` v1.1（WW25 Formal Reference）作为构造来源——**但这与本轮"不以 WW25 为主依据"的约束冲突**，需你解禁 |
| **D. 维持现状** | 保留 `[UNRESOLVED]` 状态，不推进 Matrix Commitment 实现 |

---

## 7. 附：本报告的检索可复现性

| 项 | 值 |
|---|---|
| 被检索文件 | `papers/论文PPT.pdf`（65 页） |
| 检索工具 | PyMuPDF（`fitz`）全文提取 + annotation 遍历 |
| 关键词 | `Wee25`, `Wee`, `References`, `Bibliograph`, `eprint`, annotation 遍历 |
| 结果 | 无参考文献表；`[Wee25]` 仅 5 处内联标记；唯一 URL 在 p65（2025/1039, 2025/044） |

---

## 8. 来源

- **【PPT】** `papers/论文PPT.pdf`：p23–25（Matrix Commitments，标注 `[Wee25, adapted]`）、p22（`[Wee24]`/`[AMR25]`）、p31/p45（`[Wee25]`/`[WW25]`）、p64–65（Open Problems / Thanks + 两个 URL）。
- **【项目内论文】** `papers/Registered ABE and Adaptively-secure Broadcast Encryption fr.pdf`（CHW25，对应 p65 的 2025/044）。
- **【前序文档】** `docs/matrix-commitment-primitive-coursedata-review.md`（课程资料缺失构造的结论）。
