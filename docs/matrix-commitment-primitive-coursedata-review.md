# Matrix Commitment 原语 — 课程资料依据核查与 TOY 方案设计

> 阶段：M5 · Matrix Commitment 原语研究（**不写代码**）
> **依据范围与优先级**（本轮严格执行）：
> 1. **【PPT】** `papers/论文PPT.pdf`（**最高优先级**，决定算法结构/符号/演示逻辑）
> 2. **【ABE】** `papers/Registered ABE and Adaptively-secure Broadcast Encryption fr.pdf`（CHW25，补充正式理论）
> 3. **【docs】** `docs/matrix-commitment-dbe-theory.md`、`docs/matrix-commitment-dbe-spec.md`（最低，冲突时让位）
>
> **本轮不采用 WW25 独立论文作为主实现依据。**
> **遇到课程资料未给出的必要细节 → 标记 `[UNRESOLVED]`，说明"课程资料没有给出"，再提出 TOY 候选。**

---

## 0. 结论速览

| 问题 | 结论 |
|---|---|
| PPT 有没有定义 `Com(pp, m_1..m_L) → (C, z_1..z_L)` 与 `Cv_i+Az_i=m_i`？ | **有**（p23–25），但只有**接口 + 关系 + 安全性陈述**，**无具体构造** |
| CHW25 有没有定义 Matrix Commitment 原语？ | **没有**。全文 `0` 处 "matrix commitment"/"Commat"/"opening"/"V_L"/"z_i" |
| 那 CHW25 提供什么正式依据？ | **周边理论**：ℓ-succinct LWE 假设、`SuccinctTrapGen`/`DimRed`/`Transform`、格同态求值、"属性压缩"技术 |
| `C, v_i, z_i` 的**具体构造**在哪？ | **课程资料均未给出** → **`[UNRESOLVED]`** |
| 课程 TOY 最小方案 | 见第 6 节候选 A（显式列构造，`L ≤ m`），**待审核** |

---

## 1. 【PPT】给出的内容（精确，带页码）

### 1.1 接口定义（PPT **p23**）

```
Com(pp, m_1 ... m_L) → C ,   openings z_1 ... z_L
```
- 讲义原话：**"vector commitment to vectors"**（对一组向量做承诺）；
- 讲义原话：**"can be deterministic or randomized"**；
- `C` 标注为 **commitment**，`z_1...z_L` 标注为 **openings**。

### 1.2 核心打开关系（PPT **p24**）

```
对任意 i ∈ [L]:    C · v_i = m_i − A · z_i
```
PPT 在等式下方用箭头标注：**`v_i` 与 `z_i` 均为 low-norm**。

等价移项（本文写作）：
```
C · v_i + A · z_i = m_i
```

### 1.3 公开参数描述（PPT **p24** 右侧文本框，原话）

> **"pp describes `A` and `v_i` for `i ∈ [L]`"**

即：`pp` 中描述了 `A` 与**全部** `v_i`（`i = 1..L`）。

### 1.4 安全性陈述（PPT **p25**）

```
Security:   s^T A + e^T  ≈  z^T      given pp
```
- 这是 **ℓ-succinct LWE** 假设的表述（PPT 标题 p21–22 为 "Succinct LWE Family of Assumptions"）；
- 含义：即便给定 `pp`（含 `A` 的"新鲜 trapdoor"），LWE 样本仍与均匀分布不可区分。

### 1.5 PPT 归属标注（p23 右上角）

> **`[Wee25, adapted]`**

**即 PPT 明确说这一节内容取自 `[Wee25]` 并做了适配。** 本轮按你的要求**不展开 WW25**，仅记录这一"指路牌"。

### 1.6 PPT 给出的公式汇总

| 公式 | 出处 | 性质 |
|---|---|---|
| `Com(pp, m_1..m_L) → (C, z_1..z_L)` | p23 | **接口** |
| `C v_i = m_i − A z_i`（即 `Cv_i+Az_i=m_i`） | p24 | **关系** |
| `pp describes A and v_i (i∈[L])` | p24 | **参数内容** |
| `v_i, z_i` 是 low-norm | p24 | **性质** |
| `s^T A + e^T ≈ z^T given pp` | p25 | **安全性** |

---

## 2. 【ABE / CHW25】给出的内容 —— 以及**不**给出什么

### 2.1 **不给**：Matrix Commitment 原语（关键发现）

对 CHW25 全文（84 页）关键词检索结果：

| 关键词 | 出现次数 |
|---|---|
| `matrix commitment` / `Matrix Commitment` | **0** |
| `Commat` / `Vermat` / `Openmat` | **0** |
| `vector commitment` | **0** |
| `opening` / `short opening` | **0** |
| `V_L` | **0** |
| `Open(` | **0** |
| `z_i` | **0** |
| `commitment` | 6（**全部**在参考文献或旁述：functional commitments、cuckoo commitments 等） |

**结论**：**CHW25 没有定义 `Com(pp, m_1..m_L) → (C, z_1..z_L)` 这一原语，也没有 `Cv_i+Az_i=m_i` 关系。** 因此 `C, v_i, z_i` 的构造**无法**从 CHW25 找到依据。

### 2.2 **给**：周边正式理论

CHW25 提供的是**不同的**密码学基础设施：

| 组件 | CHW25 内容 | 与 Matrix Commitment 的关系 |
|---|---|---|
| **ℓ-succinct LWE 假设** | 定义为 PPT p25 安全性陈述的正式来源；可证伪、实例无关 | **背景假设**（PPT p25 的正式版） |
| `SuccinctTrapGen(1^n,1^ℓ,q,m,σ)` → `(A,U,T)` | 满足 `[I_ℓ⊗A \| U]·T = G_{nℓ}`，`‖T‖ ≤ √m σ` | **不同的** trapdoor 基础设施 |
| `DimRed(A,U,T,S)` → `(U_S, T_S)` | 维度约简，`[I_k⊗A \| U_S]·T_S = G_{nk}` | 用于子集 `S` 的 trapdoor |
| `Transform(A,U,T,N)` → `(V,Z,R,T_V,T_Ẑ)` | 把 ℓ-succinct trapdoor 转成结构矩阵的 trapdoor | 名字含 `Z`，但**不是** opening |
| **属性压缩**（源自 `[Wee24]`） | `[A \| A_0 + Σ x_i U_i]` 是 `B − x^T⊗G` 的压缩表示 | **概念相近但不同**：是"编码压缩"，非"承诺+打开" |
| 格同态求值 | `B − x^T⨂G`、`H_{B,f,x}`（PPT p40–42 亦有） | ABE 策略求值 |

> **重要澄清**：CHW25 §2 的"attribute compression"与 PT 的 Matrix Commitment **都使用 succinct LWE trapdoor**，但**解决的问题不同**：
> - CHW25 压缩的是"属性编码"（让密文不随 `|x|` 增长）；
> - PPT 的 Matrix Commitment 是"对一组向量承诺 + 单点打开"。
> **不能**把 CHW25 的压缩技术直接当作 Matrix Commitment 的实现。

### 2.3 CHW25 的 `Transform` 输出含 `Z`——是否就是 opening？

**不是。** `Transform` 输出 `(V, Z, R, T_V, T_Ẑ)`，其用途是"得到结构矩阵（Eq. 4.1）的 trapdoor"；`Z` 在此是 trapdoor 变换的中间矩阵，**CHW25 未赋予其 `Cv_i+Az_i=m_i` 的打开语义**，也**未给出** `C`（承诺矩阵）与 `v_i`（验证向量）。**不可**将其等同于 PPT 的 `z_i`。

---

## 3. 逐符号对照：`pp, A, v_i, C, z_i, m_i`

| 符号 | 【PPT】怎么定义 | 【CHW25】怎么定义 | 状态 |
|---|---|---|---|
| `pp` | "describes `A` and `v_i` for `i∈[L]`"（p24） | 无 Matrix Commitment 意义下的 `pp`（其 `pp` 用于 ABE） | PPT 给**内容**，未给**生成算法** |
| `A` | 公开矩阵（未给维度/生成方式） | CHW25 的 `A ∈ Z_q^{n×m}` 由 `TrapGen` 生成（但**语境不同**） | **`[UNRESOLVED]`**（维度/生成） |
| `v_i` | 验证向量，**public、low-norm**（p24） | **无定义** | **`[UNRESOLVED]`**（如何构造） |
| `C` | 承诺矩阵，"短"（p23） | **无定义** | **`[UNRESOLVED]`**（如何构造） |
| `z_i` | opening，**low-norm**（p24） | **无定义**（`Transform` 的 `Z` 语义不同） | **`[UNRESOLVED]`**（如何构造） |
| `m_i` | 位置 `i` 的被承诺消息（p24） | **无定义** | 语义清楚，构造由 `S` 决定（DBE 层） |
| `L` | 位置总数 | 无 | 语义清楚 |

---

## 4. `C, v_i, z_i` 实际怎样构造？——课程资料的答案

### 4.1 直接回答
**课程资料（PPT + CHW25）没有给出 `C, v_i, z_i` 的构造。**

- **PPT** 只给了**接口**（`Com(...) → (C, z_1..z_L)`）、**关系**（`Cv_i+Az_i=m_i`）、**性质**（`v_i,z_i` low-norm）、**安全性**（succinct LWE），并注明源自 `[Wee25, adapted]`。
- **CHW25** 完全没有这个原语。

### 4.2 按你的要求，这属于 `[UNRESOLVED]`

> **`[UNRESOLVED]`**：`C`（承诺矩阵）、`v_i`（验证向量）、`z_i`（打开）的**具体构造算法**。
> **课程资料没有给出这一细节**：PPT 仅给出接口与关系并注明 `[Wee25, adapted]`；CHW25 无此原语。
> 因此**不得**从其他论文（含 WW25）补齐后当作老师要求。

---

## 5. `[UNRESOLVED]` 清单（课程资料缺失项）

| # | 缺失细节 | PPT 给了吗 | CHW25 给了吗 | 处置 |
|---|---|---|---|---|
| U1 | `A` 的维度与生成方式 | ✗（只说"公开矩阵"） | ✗（其 `A` 语境不同） | `[UNRESOLVED]` |
| U2 | `C` 的构造算法 | ✗ | ✗ | `[UNRESOLVED]` |
| U3 | `v_i` 的构造/生成 | ✗（只说 public、low-norm） | ✗ | `[UNRESOLVED]` |
| U4 | `z_i` 的构造/生成 | ✗（只说 low-norm） | ✗ | `[UNRESOLVED]` |
| U5 | `z_i` 的采样分布 | ✗ | ✗ | `[UNRESOLVED]` |
| U6 | 参数 `n, m, q, L` 关系 | ✗ | ✗（CHW25 的参数是 ABE 的） | `[UNRESOLVED]` |
| U7 | binding 的正式证明依据 | 仅隐含（low-norm + 格困难） | ✗ | `[UNRESOLVED]`（PPT 未证） |
| U8 | "确定性 / 随机化承诺"的具体形式 | ✗（只说两者皆可） | ✗ | `[UNRESOLVED]` |
| U9 | 无界 `L`（指数宽）如何只算单列 | ✗ | ✗（CHW25 的 local 是 `DimRed`，语义不同） | `[UNRESOLVED]` |

> **注意**：`docs/matrix-commitment-dbe-spec.md` **v1.1** 中关于 `pp_com=(B,W,T)`、`Commat/Vermat/Openmat`、`ComSparsemat` 等内容**来自 WW25**。按本轮优先级（PPT → CHW25 → docs），这些属于**最低优先级 docs**，**不能**作为本轮实现依据。**该冲突需你裁决**（见第 8 节）。

---

## 6. 课程 TOY 最小可实现方案（候选，**待审核**）

**共同约束**（来自 PPT，必须满足）：
1. 实现 `Com(pp, m_1..m_L) → (C, z_1..z_L)` 接口；
2. 满足关系 `C v_i + A z_i = m_i`；
3. `v_i`、`z_i` 为 **low-norm**；
4. **不得**用哈希 / AES / 逐用户加密冒充；
5. 明确标注 TOY。

---

### 候选 A（**推荐**）：显式列构造 —— 最小、透明

**【设计】**
```
参数： n, m, q（小），L ≤ m
pp  = (n, m, q, L, A)          A ← Z_q^{n×m}（随机公开矩阵）
v_i = e_i ∈ {0,1}^m            （第 i 个单位向量；low-norm）

Com(pp, m_1 ... m_L):
    对每个 i：采样短随机 z_i ∈ Z_q^m        （low-norm）
    置 C 的第 i 列 = m_i − A·z_i
    （C ∈ Z_q^{n×m}，其余列为 0；需 L ≤ m）
    输出 (C, z_1 ... z_L)

验证： C·v_i = C·e_i = C 的第 i 列 = m_i − A z_i
    ⟹ C·v_i + A·z_i = m_i      ✓ 关系精确成立
```

**【满足】**
- ✅ 接口一致；关系精确成立；`z_i` low-norm；
- ✅ 真格结构（`A`、`z_i`），**非** hash/AES/逐用户加密；
- ✅ binding（找短 `δ` 使 `Aδ = m_i' − m_i` ⇒ SIS 困难）。

**【牺牲 / 限制】**
- ⚠️ `L ≤ m`：**没有 succinct、没有 unbounded**（与 PPT 的"unbounded"卖点不符，但对课程小 `N` 足够）；
- ⚠️ `v_i = e_i` 使 `C` 的构造退化为"直接列赋值"——**透明但非论文构造**；
- ⚠️ 安全性为 TOY 级（小参数可攻破）。

**【诚实性声明】** 候选 A **真实满足 PPT 的接口与关系**，但**不是** PPT 所引 `[Wee25]` 的构造；必须在文档/代码中标注为 **课程 TOY 实例**。

---

### 候选 B：随机验证向量版（仍透明，稍进一层）

**【设计】** 与 A 相同，但 `v_i ← {0,1}^m` 短随机（而非单位向量），并令
```
V = [v_1 | ... | v_L] ∈ Z_q^{m×L}（需 L ≤ m 且 V 可逆）
C = [m_1 − A z_1 | ... | m_L − A z_L] · V^{-1}
```
验证：`C v_i = (m_i − A z_i) · V^{-1} v_i = m_i − A z_i` ✓

**【取舍】** 比 A 更"像"通用验证向量，但 `C` 变稠密、可读性下降，且仍需 `L ≤ m`。**收益有限，一般不必要。**

---

### 候选 C：trapdoor 方案（最接近正式，但工程重）

**【设计】** 用格 trapdoor 生成真正的 succinct 结构（`TrapGen` / `SamplePre` / gadget `G` / `G^{-1}`），使 `C` 与 `v_i` 具备论文所述结构。

**【取舍】**
- ✅ 最接近 `[Wee25]` 的形态；
- ❌ 需要离散高斯采样、`G`-trapdoor、`G^{-1}` 确定性采样——**纯 Python 实现成本高、正确性难保证**；
- ❌ 大参数下不可行；小参数下安全性更弱。
- **判断**：可作为"进阶目标"，**不建议**作为课程第一版。

---

### 6.4 候选对比

| 维度 | 候选 A | 候选 B | 候选 C |
|---|---|---|---|
| 满足 PPT 关系 | ✅ | ✅ | ✅ |
| 实现成本 | **低** | 中 | **高** |
| 透明度（可教学） | **高** | 中 | 低 |
| `L` 是否无界 | ❌（`L≤m`） | ❌ | ✅（理论） |
| 是否论文构造 | ❌（TOY） | ❌（TOY） | 接近 |
| 风险 | 可能被认为"太简单" | 同 A | 做不完 |

---

## 7. 禁止的"伪实现"（重申）

1. ❌ 用哈希（SHA-256 / Merkle）替代 `Com`；
2. ❌ 用 AES 包装或**逐用户单独加密**；
3. ❌ 去掉 `A`/`z_i` 的格结构，只留一个"承诺值"；
4. ❌ 把 `m_i` 明文放进 `C` 或密文；
5. ❌ 声称候选 A/B 就是 `[Wee25]` 的构造。

---

## 8. 待你审核/裁决的问题

1. **是否采用候选 A** 作为课程 TOY 的 Matrix Commitment 实现？（推荐）
2. **`L ≤ m` 的限制**是否可接受？（若要 `L` 更大，需转向候选 C）
3. **`docs/matrix-commitment-dbe-spec.md` v1.1 的定位冲突**：
   - v1.1 以 **WW25** 为依据（`pp_com=(B,W,T)` 等）；
   - 本轮优先级为 **PPT → CHW25 → docs**，v1.1 降为最低；
   - **请裁决**：是否废弃/降级 v1.1 的 WW25 内容？还是保留为"参考资料"？
4. **U1–U9 的 `[UNRESOLVED]`** 是否确认按"课程资料未给出"处理，选用上述 TOY 候选填补？
5. 是否需要我**只依据 PPT** 再产出一份"纯 PPT 版"的 Matrix Commitment 说明（不含任何论文外内容）？

---

## 9. 来源

- **【PPT】** `papers/论文PPT.pdf`：**p23–25（Matrix Commitments，标注 `[Wee25, adapted]`）**、p21–22（Succinct LWE）、p26–30（Basic Approach）、p31–38（DBE For Unbounded Users）。
- **【ABE / CHW25】** `papers/Registered ABE and Adaptively-secure Broadcast Encryption fr.pdf`：§1（ℓ-succinct LWE 介绍）、§2（attribute compression，源自 `[Wee24]`）、§4（`SuccinctTrapGen` / `DimRed` / `Transform`）。
- **【docs】** `docs/matrix-commitment-dbe-theory.md`（v2.0）、`docs/matrix-commitment-dbe-spec.md`（v1.1，WW25 依据）。
