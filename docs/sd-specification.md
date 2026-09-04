# Subset Difference (SD) 广播加密 — 论文级算法规格化（核验修订版）

> 阶段：M4 · 对应 Prompt 07
> 论文：Dalit Naor, Moni Naor, Jeffrey B. Lotspiech, *Revocation and Tracing Schemes for Stateless Receivers*, CRYPTO 2001, LNCS 2139, pp. 41–62（ePrint 2001/059）
> 本章节对应论文 **Section 3.2（The Subset Difference Method）**、**Lemma 2**、**Theorem 4** 与 Section 6（key-indistinguishability）。
> 性质：**纯原文核查与规格化，禁止写代码、禁止修改任何现有文件。**
> 修订说明：本版使用 pymupdf 精确提取原文，修正了 Theorem 编号、存储公式、G 方向、平均数字等细节（详见 §12）。
> 编号约定：用户 1-based（u1..uN），叶子 heap 编号 v_N..v_{2N-1}（与现有 CS 实现一致）。

---

## 0. 四类信息标注约定

- **【NNL01 原文】**：直接来自 NNL01 论文的表述（已用 pymupdf 精确提取核对）。
- **【后续论文/外部分析】**：来自 NNL01 之外的研究，标注为「后续研究」。
- **【工程推断】**：为实现而做的合理推断/具体化，论文未明确规定。
- **【理解】**：我自己的解释性文字，帮助建立直觉。

---

## 1. 论文定位

【NNL01 原文】SD 定义在 **Section 3.2 "The Subset Difference Method"**，配套结论为 **Lemma 2**（cover 上界）与 **Theorem 4**（SD 复杂度）。

【NNL01 原文·动机】「The main disadvantage of the Complete Subtree method is that N\R may be partitioned into a number of subsets that is too large. … We show an improved method that partitions the non-revoked receivers into **at most 2r−1 subsets** (or 1.25r on average), thus getting rid of the log N factor … In return, the number of keys stored by each receiver **increases by a factor of log N** … any user belongs to substantially more subsets than in the first method (O(log² N) instead of O(log N)).」

【理解】SD 用「子树减去子树」的更灵活形状，换取更小的 header（O(r)），代价是用户存储从 O(log N) 升到 O(log² N)，并引入计算密钥分配（GGM PRG）来压缩存储。

---

## 2. 子集如何表示（S_{ij}）

【NNL01 原文】「a valid subset S_{ij} is represented by two nodes (v_i, v_j) such that **v_i is an ancestor of v_j**. … A leaf u is in S_{ij} iff it is in the subtree rooted at v_i but not in the subtree rooted at v_j, or in other words **u ∈ S_{ij} iff v_i is an ancestor of u but v_j is not**。」

【理解】
- **S_{ij} = (以 v_i 为根的子树) \ (以 v_j 为根的子树)**，即「一组接收者减去另一组」。
- v_i 是「外层子树根」，v_j 是「被挖掉的子树根」，且 v_j 严格在 v_i 子树内部（v_i 是 v_j 的祖先）。

【NNL01 原文·与 CS 的关系】「all subsets from the Complete Subtree Method are also subsets of the Subset Difference Method; specifically, a subtree appears here as the difference between its parent and its sibling. The only exception is the full tree itself, and we will add a special subset for that.」

【理解】CS 的每个「完整子树」S_i 可表示为 SD 的 S_{parent(i), sibling(i)}；唯一例外是整棵树 S_1（无父节点），需单独「特殊 subset」表示「无撤销」情况，其密钥即根节点 key（见 §3.4）。

---

## 3. 密钥分配（Key Assignment）

### 3.1 为什么不能信息论分配

【NNL01 原文】「If we try and repeat the information-theoretic approach … the storage requirements would expand tremendously … yielding a total of O(N) keys.」

【理解】用户属于 O(log² N) 个子集，若逐个独立随机分配密钥，每用户要存 O(N) 个，不可接受。

### 3.2 计算密钥分配：GGM PRG（G 方向已逐字确认）

【NNL01 原文】「choose for each v_i corresponding to an internal node a **random and independent value LABEL_i**. … employ the method used by Goldreich, Goldwasser and Micali [28] … Let G be a pseudo-random sequence generator that **triples the input**; let G_L(S) denote the **left third**, G_R(S) the **right third**, G_M(S) the **middle third**.」

【NNL01 原文·G 方向（原文逐字，§3.2 正文）】「Note that each label induces three parts: **G_L — the label for the left child, G_R — the label for the right child, and G_M the key at the node**.」

【NNL01 原文·标签派生】「Consider the subtree T_i (rooted at v_i). … the root is assigned a label LABEL_i. Given that a parent was labeled S, its two children are labeled G_L(S) and G_R(S) respectively. Let LABEL_{i,j} be the label of node v_j derived in the subtree T_i from LABEL_i. … the key L_{ij} assigned to set S_{ij} is **G_M(LABEL_{i,j})**.」

【理解】方向映射（已确认，非推断）：
```
LABEL_i（根种子）
  ├─ G_L(LABEL_i) → 左孩子 label
  ├─ G_R(LABEL_i) → 右孩子 label
  └─ G_M(LABEL_i) → 该节点对应的 key
```
节点 v_j 在子树 T_i 中的 label 记为 `LABEL_{i,j}`，则 S_{ij} 的密钥 `L_{ij} = G_M(LABEL_{i,j})`。

【NNL01 原文·Figure 3】图中给出具体路径示例 `LABEL_{i,j} = G_R(G_L(G_L(LABEL_i)))`（即从根经「左→左→右」到达 v_j），以及 `L_{i,j} = G_M(LABEL_{i,j})`。

### 3.3 用户存储哪些 label

【NNL01 原文】「For each subtree T_i such that u is a leaf of T_i, the receiver u should be able to compute L_{ij} iff v_j is **not** an ancestor of u. Consider the path from v_i to u and let v_{i1}...v_{ik} be the nodes just "hanging off" the path, i.e. they are adjacent to the path but not ancestors of u (see Figure 3). Each v_j in T_i that is not an ancestor of u is a descendant of one of these nodes. Therefore if u receives the labels of v_{i1}...v_{ik} …」

【理解】用户 u 只存储「挂在自己根到叶路径外侧」的那些节点的 label（每棵包含 u 的子树各一组）：
- **能派生**：任何「u 在其外层子树内、但 u 不在被挖掉子树内」的 S_{ij} 的密钥（u ∈ S_{ij} 的那些）。
- **不能派生**：u 所在「被挖掉子树」内的密钥（u ∉ S_{ij}），因为那需要「路径内侧」节点的 label，而 u 没有。

### 3.4 存储总量（Theorem 4 精确公式）

【NNL01 原文·Theorem 4】「The Subset Difference method requires … (ii) to store **½ log² N + ½ log N + 1** keys at a receiver …」

【工程推断】令 h = log₂ N，则该公式展开为：
```
½ log² N + ½ log N + 1 = h(h+1)/2 + 1 = ∑_{d=1}^{h} d + 1
```
其中 `∑_{d=1}^{h} d = h(h+1)/2` 是「挂在路径外侧」的 label 总数（每棵深度 d 的子树贡献 d 个），`+1` 是「无撤销情况」的整棵树 key（= G_M(LABEL_1)，对应 CS 的根节点密钥 L_1，见 §2）。

【NNL01 原文】「each tree T_i of depth d that contains u contributes d keys (plus one key for the case where there are no revocations)」。

---

## 4. SD Cover 算法

### 4.1 正式算法（迭代版，原文）

【NNL01 原文】「let ST(R) be the (directed) Steiner Tree induced by R and the root. We build the subsets collection iteratively, maintaining a tree T which is a subtree of ST(R) … We start by making T = ST(R) and then iteratively remove nodes from T until T consists of just a single node:

1. Find two leaves v_i and v_j in T such that the least-common-ancestor v of v_i and v_j does not contain any other leaf of T in its subtree. Let v_l and v_k be the two children of v such that v_i is a descendant of v_l and v_j is a descendant of v_k. (If there is only one leaf left, make v_i = v_j to the leaf, v_l to be the root of T and v_k = v_j.)

2. If v_l ≠ v_i then add the subset S_{l,i} to the collection; likewise, if v_k ≠ v_j then add the subset S_{k,j} to the collection.

3. Remove from T all the descendants of v and make it a leaf.」

### 4.2 可执行伪代码（工程推断，由 4.1 逐句翻译）

```
function SD_Cover(tree, R):
    # 1) ST(R)：R 中每个撤销叶子到根的路径的并集
    ST = ∅
    for leaf in revoked_leaves(R):
        ST = ST ∪ ancestors(leaf)        # 含 leaf 与根

    # 2) 初始 T = ST(R)（有向树，根为 v1）
    T = ST

    # 3) 迭代直到 T 只剩一个节点
    cover = []
    while |T| > 1:
        leaves = { 节点 x ∈ T : x 在 T 中无孩子 }

        if |leaves| == 1:                 # 原文 step 1 括号的特殊分支
            v_leaf = leaves 中唯一元素
            v_root = T 的根（v1）
            cover.append(S_{v_root, v_leaf})   # 对应 step2 的 v_l=root, v_i=leaf
            T = {v_root}                  # step3 删除所有后代
            break

        # 选两个叶子，其 LCA 的子树内不含其他 T 叶子
        v_i, v_j = 任意两个满足上述条件的叶子
        v = LCA(v_i, v_j)
        (v_l, v_k) = v 的两个孩子，其中 v_i 是 v_l 的后代、v_j 是 v_k 的后代

        if v_l != v_i: cover.append(S_{v_l, v_i})
        if v_k != v_j: cover.append(S_{v_k, v_j})

        T = T \ {v 的所有后代}            # v 本身保留，成为新叶子

    return cover
```

【理解】等价视角（原文也给出）：ST(R) 中「出度为 1」的节点连成 maximal chains，每条非平凡 chain 贡献一个 S_{链顶, 链底}。

### 4.3 Cover 大小上界

【NNL01 原文·Lemma 2】「Lemma 2 shows that a cover can contain at most **2r−1** subsets for any set of r revocations.」正式表述：「Lemma 2 Given any set of revoked leaves R, the above method partitions N\R into **at most 2r−1 disjoint subsets**.」

【NNL01 原文·证明要点】每次迭代最多增加 2 个子集（step 2）并把 Steiner 叶子数减 1（step 3），除了最后一次只加 1 个；从 r 个叶子开始，总共 ≤ 2r−1 个。

【NNL01 原文·平均】原文给出**两个**不同数字，须区分：
- **1.38r（分析上界）**：平均分析中，「the expected number of non-empty chains is bounded by ∑_{k=1}^{r} C(r,k)(1/2^k) … ≤ 2r ∑_{k=1}^{∞} (1/k)(1/2^k) ≤ **2 ln 2 · r ≈ 1.38 · r**」。这是**可证明的期望上界**。
- **1.25r（模拟实验）**：「**Simulation experiments have shown a tighter bound of 1.25r** for the random case. So the actual number of subsets … is expected to be slightly lower than the 2r−1 worst case result.」这是**经验结果，非严格证明**。

【NNL01 原文·Summary 一致性】Section 1.2 的 Summary 用「2r−1 (in the worst case, or 1.38r in the average case)」，此处「1.38r」对应上述分析上界；Section 3.2 正文用「1.25r」对应模拟实验 tighter bound。二者不是矛盾，而是「分析上界」与「经验估计」两个层次。

---

## 5. Encrypt 与 Decrypt

### 5.1 Encrypt（header 构造）

【NNL01 原文·框架 Section 2.2】与 CS 相同框架：
1. 选会话密钥 K。
2. 找 cover = {S_{i1,j1}, …, S_{im,jm}}（m ≤ 2r−1）。
3. header = ([ (i1,j1), …, (im,jm) ], E_{L_{i1,j1}}(K), …, E_{L_{im,jm}}(K))；body = F_K(M)。

【理解】与 CS 唯一区别：header 索引从「单个节点 i」变成「一对节点 (i, j)」，密钥从节点密钥 `L_i` 变成子树差密钥 `L_{ij}`。

### 5.2 Decrypt

【NNL01 原文】「a receiver u first finds the subset S_{ij} such that u ∈ S_{ij}, and computes the key corresponding to S_{ij} … this subset can be found in O(log log N). The evaluation of the subset key takes now **at most log N applications of a pseudo-random generator**. After that, a single decryption is needed.」

【理解】用户 u：
1. 在 header 索引中找 (i,j) 使 u ∈ S_{ij}（v_i 是 u 祖先、v_j 不是）。
2. 从存储的 label 出发，用 ≤ log N 次 PRG 派生 `LABEL_{i,j}`，再算 `L_{ij} = G_M(LABEL_{i,j})`。
3. `K = D_{L_{ij}}(E_{L_{ij}}(K))`，再解 body。

---

## 6. Correctness（正确性）

【NNL01 原文】「every non-revoked u is in exactly one subset, the one defined by the first chain of nodes of outdegree 1 in ST(R) that is encountered while moving from u towards the root.」

【理解】
- **授权用户 u ∉ R 能解密**：u 必落在唯一一个 cover 子集 S_{ij}；由 label 分配，u 持有「挂在路径外侧」的 label，能派生出 L_{ij}；解密成功。
- **撤销用户 u ∈ R 不能解密**：cover 恰好覆盖 N\R，u 不在任何 S_{ij} 中；且 u 无法派生任何 cover 子集的密钥（u 在被挖掉的子树内，缺路径内侧 label）。

---

## 7. Security intuition（安全直觉）

【NNL01 原文】「each key L_{ij} is (information theoretically) independent of all I_{u'} for u' ∉ S_{ij}. … the combined secret information of all u' ∉ S_{ij} is specified by at most [2] labels — those hanging on the path … which are strings generated independently by G. Hence, a hybrid argument implies that the probability of distinguishing L_{ij} from random can be at most 2r·ε, where ε is the bound on distinguishing outputs of G from random strings.」

【理解】SD 安全建立在两层：
1. **信息论层面**：撤销用户组合起来也拿不到任何 cover 子集 S_{ij} 的 label（都在「被挖掉的子树」里）。
2. **计算层面**：即便存在 PRG 推导关系，L_{ij} 与随机密钥的区分优势受 PRG 区分优势 ε 限制（hybrid argument），安全损失为 2r·ε。

【NNL01 原文】「The Subset Difference method … is secure in the sense of Definition 10.」

---

## 8. 复杂度总结

| 指标 | SD 方法 |
|---|---|
| 用户存储 | **½ log² N + ½ log N + 1**（Theorem 4） |
| header 大小 | **≤ 2r−1**（Lemma 2） |
| cover 计算 | O(r log N)（Steiner 树 + chain） |
| 解密 | O(log log N) 查找 + ≤ log N 次 PRG + 1 次解密 |
| 安全模型 | full collusion，计算安全（GGM PRG，损失 2r·ε） |

> 【NNL01 原文·Theorem 4】「The Subset Difference method requires (i) message length of at most 2r−1 keys (ii) to store ½ log² N + ½ log N + 1 keys at a receiver and (iii) O(log N) operations plus a single decryption operation to decrypt a message.」

---

## 9. N=8 完整手算

树同 CS（heap 编号，u1..u8，叶子 v8..v15，内部节点 v1..v7）。

### 9.1 SD Cover 手算

**R = {u3}（叶子 v10）**

- ST(R) = 根到 v10 路径 = {v1, v2, v5, v10}，单叶子 v10。
- 伪代码：`|leaves|==1` → 特殊分支，v_leaf=v10，v_root=v1，加 **S_{1,10}**，T={v1} 结束。
- **SD cover = { S_{1,10} }** = (全部) \ (v10 子树) = {u1,u2,u4,u5,u6,u7,u8} = N\{u3}。**1 个子集**。

**R = {u3, u5}（叶子 v10, v12）**

- ST(R) = {v1, v2, v5, v10, v3, v6, v12}，叶子 v10、v12。
- 伪代码：选 v10、v12，LCA = v1（无其他叶子）；v_l=v2（v10 侧），v_k=v3（v12 侧）。
- v_l ≠ v10 → 加 **S_{2,10}**；v_k ≠ v12 → 加 **S_{3,12}**；删 v1 后代，T={v1} 结束。
- **SD cover = { S_{2,10}, S_{3,12} }**：
  - S_{2,10} = {u1,u2,u3,u4} \ {u3} = **{u1,u2,u4}**
  - S_{3,12} = {u5,u6,u7,u8} \ {u5} = **{u6,u7,u8}**
  - 合并 = {u1,u2,u4,u6,u7,u8} = N\{u3,u5}。**2 个子集**。

### 9.2 用户 u3 的精确密钥材料（N=8）

用户 u3 = 叶子 v10，路径 v1 → v2 → v5 → v10。u3 属于 3 棵子树：T_1（根 v1）、T_2（根 v2）、T_5（根 v5）。

逐个列出「挂在路径外侧」的节点（每棵子树一组）：

| 子树 | 路径 | 挂起节点（非路径孩子） | 存储的 label |
|---|---|---|---|
| T_1（根 v1，深度3） | v1→v2→v5→v10 | v3、v4、v11 | LABEL_{1,3}, LABEL_{1,4}, LABEL_{1,11} |
| T_2（根 v2，深度2） | v2→v5→v10 | v4、v11 | LABEL_{2,4}, LABEL_{2,11} |
| T_5（根 v5，深度1） | v5→v10 | v11 | LABEL_{5,11} |

- label 数 = 3 + 2 + 1 = **6 个**（= ∑_{d=1}^{3} d）。
- 加「无撤销」整棵树 key `G_M(LABEL_1)` = **1 个**。
- **总计 = 7 个**，精确等于 Theorem 4 的 ½·3² + ½·3 + 1 = 4.5 + 1.5 + 1 = **7**。

### 9.3 密钥派生示例（用户 u1 解密 R={u3} 的 cover {S_{1,10}}）

u1 ∈ S_{1,10}，需派生 L_{1,10} = G_M(LABEL_{1,10})。u1 持有 LABEL_{1,5}（v5 在 T_1 的 label），而 v10 是 v5 的右孩子，故 `LABEL_{1,10} = G_R(LABEL_{1,5})`，再 `L_{1,10} = G_M(LABEL_{1,10})`，共 **2 次 PRG**（≤ log 8 = 3）。

---

## 10. CS vs SD 对比

| 维度 | Complete Subtree (CS) | Subset Difference (SD) |
|---|---|---|
| 子集形状 | 完整子树 S_i | 子树减子树 S_{ij} |
| 用户密钥数量 | log N + 1（N=8 时 4） | **½ log² N + ½ log N + 1**（N=8 时 7） |
| 密钥分配 | 信息论（独立随机） | 计算（GGM PRG 派生） |
| header 大小 | ≤ r·log(N/r) | **≤ 2r−1** |
| R={u3} cover 数 | 3 | **1** |
| R={u3,u5} cover 数 | 4 | **2** |
| Cover 计算 | ST(R) 悬挂子树 | Steiner + outdegree-1 chain |
| 解密 | 1 次解密 | ≤ log N 次 PRG + 1 次解密 |
| 安全 | 信息论 key-indist. | 计算 key-indist.（依赖 PRG） |
| 适用场景 | 实现简单、直观 | header 更短、适合大 r |

### 10.1 为什么 SD 能减少 header

【理解】CS 的覆盖单元是「完整子树」，形状受限——覆盖稀疏撤销时产生很多小完整子树（r·log(N/r) 项）。SD 的覆盖单元是「子树减子树」，可直接表达「一大块减去被撤销的小块」，单个撤销时 1 个 S_{root,leaf} 就够，header 从 O(r log N) 降到 O(r)。

---

## 11. 与现有 CS 实现的接口对照（仅理解，不修改）

| 现有 CS 接口 | SD 对应概念 |
|---|---|
| `CompleteSubtreeTree`（节点/祖先/路径/子树） | 复用（SD 也基于同一棵树，需新增「子树差」查询） |
| `cover(tree, revoked) → [node...]` | SD cover 输出 `[(i,j)...]` 而非 `[node...]` |
| `setup` / `keygen`（节点独立密钥） | SD 改为「内部节点 label + GGM PRG 派生」 |
| `encrypt_session_key(node_keys, cover, K)` | SD 的 header 索引变成 (i,j) 对 |
| `decrypt_session_key(user_key, header)` | SD 需先「命中 (i,j)」再「派生 L_{ij}」 |

【工程推断】SD 实现需新增：label 结构、PRG G（`G_L/G_M/G_R`）、SD cover 算法（§4.2 伪代码）、用户 label 派生。**本轮不实现**，仅为后续 M4/M5 建立接口预期。

---

## 12. 核验结论与剩余不确定项

### 12.1 已从原文确认（pymupdf 精确提取）

| 结论 | 出处 |
|---|---|
| 2r−1 最坏 header 上界 | **Lemma 2**（原文「at most 2r−1 disjoint subsets」） |
| 1.38r 平均分析上界 | §3.2 average-case（= 2 ln 2 · r，可证明期望上界） |
| 1.25r 模拟实验 tighter bound | §3.2（「Simulation experiments…」） |
| 存储 = ½ log² N + ½ log N + 1 | **Theorem 4**（原文逐字） |
| G_L = 左孩子、G_R = 右孩子、G_M = 节点 key | §3.2 正文（「G_L — the label for the left child, …」） |
| SD 复杂度定理编号 = **Theorem 4** | 原文（pymupdf 与 pdftotext 双工具一致） |

### 12.2 剩余 [UNCERTAIN]

1. **论文 Theorem 编号跳跃**：提取到 Theorem 1（CS）、Theorem 4（SD）、Theorem 11（security），未见 Theorem 2、3。编号跳跃原因不明（可能是 Section 3.3/4/5 中的定理未用「Theorem」字样，或 OCR 边界），**但不影响「SD 复杂度定理 = Theorem 4」这一结论**。
2. **1.38r 求和式的完整中项**：结论「≤ 2 ln 2 · r ≈ 1.38r」已确认，但期望 non-empty chains 的求和式中间若干符号（`C(r,k)(1/2^k)` 及上界放大步骤）在提取中有缺，精确展开以论文排版为准。

> 上述两项均不影响 SD 的算法规格（cover 算法、密钥分配、存储、header 复杂度均已确认）。

---

## 13. 参考文献

- Naor, Naor & Lotspiech, *Revocation and Tracing Schemes for Stateless Receivers*, CRYPTO 2001, LNCS 2139, pp. 41–62 — ePrint 2001/059（本项目 `papers/NNL01-revocation-tracing.pdf`）
- 本文档对应其 Section 3.2（Subset Difference Method）、Lemma 2、Theorem 4、Figure 3 与 Section 6（key-indistinguishability）。
