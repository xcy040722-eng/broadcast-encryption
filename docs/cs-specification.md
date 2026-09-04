# Complete Subtree (CS) 广播加密 — 论文级算法规格化

> 阶段：M1 · 对应 Prompt 03
> 论文：Dalit Naor, Moni Naor, Jeffrey B. Lotspiech, *Revocation and Tracing Schemes for Stateless Receivers*, CRYPTO 2001, LNCS 2139, pp. 41–62（ePrint 2001/059）
> 本章节对应论文 **Section 2（Subset-Cover 框架）** 与 **Section 3.1（The Complete Subtree Method）**。
> 性质：算法规格化，**不涉及代码实现**。所有关键算法细节均已核对 NNL01 原文（`papers/NNL01-revocation-tracing.pdf`）。

---

## 0. 结论速览

- CS 是 NNL01 提出的 **Subset-Cover 框架**下的第一个实例，属于**信息论安全**（密钥独立随机分配）的对称广播加密。
- 树：满二叉树，N = 2^h 个叶子（用户），共 2N−1 个节点。
- 每个节点 `v_i` 配一把**独立随机密钥** `L_i`；用户 u 持有**根到叶子路径上的 log₂N + 1 把密钥**。
- 覆盖：撤销集合 R 的 Steiner 树 ST(R) 之外「悬挂」的所有子树，恰覆盖 N\R，最多 `r·log(N/r)` 个子集。
- 加密：会话密钥 K 用每个覆盖子集密钥 `E_{L_i}(K)` 加密 → 组成 **header**；消息用 K 加密 → 组成 **body**。

---

## 1. 符号与参数

| 符号 | 含义 |
|---|---|
| `N` | 用户总数（叶子数），取 N = 2^h（h = log₂N 为树高） |
| `h` | 树高 = log₂N |
| `U = {u_0, …, u_{N−1}}` | 全体用户集合 |
| `v_i` | 树中第 i 个节点（1 ≤ i ≤ 2N−1），`v_1` 为根 |
| `S_i` | 以 `v_i` 为根的子树所含叶子（用户）的集合 |
| `L_i` | 节点 `v_i` 的长寿命密钥（独立随机） |
| `R ⊆ U` | 被撤销（应被禁止解密）的用户集合 |
| `ST(R)` | 由 R 中叶子与根诱导出的 **Steiner 树**（连接它们的最小子树，唯一） |
| `K` | 会话密钥（每次广播新鲜随机的短比特串） |
| `E_L` | 长寿命密钥加密原语（header 中加密 K，原文建议块密码） |
| `F_K` | 会话密钥加密原语（body 中加密消息 M，原文建议流密码 XOR） |
| `M` | 待广播的明文消息 |

---

## 2. 数据结构

### 2.1 树与编号（heap 编号，便于工程实现）

满二叉树，N 个叶子。采用数组式堆编号：

- 根 `v_1`。
- 节点 `v_i` 的左孩子 = `v_{2i}`，右孩子 = `v_{2i+1}`。
- 叶子对应第 `h` 层，编号区间 `[N, 2N−1]`，即 `v_N … v_{2N−1}`。
- 用户 `u_j`（0 ≤ j < N）对应叶子 `v_{N+j}`。

### 2.2 关键定义（原文）

- **完整子树（complete subtree）**：以任意节点 `v_i` 为根的整棵子树。集合 `S_i = { u_j : v_i 是 u_j 的祖先 }`。
- **祖先关系**：`u_j ∈ S_i` 当且仅当 `v_i` 在从根到叶子 `v_{N+j}` 的路径上。

---

## 3. Setup(1^λ, N)

| 项 | 内容 |
|---|---|
| **输入** | 安全参数 λ；用户总数 N（2 的幂） |
| **输出** | 树结构；所有节点密钥 `{L_i}`；公开树编号 |
| **参数** | h = log₂N；节点数 2N−1 |
| **随机变量** | 每把密钥 `L_i`（2N−1 把） |
| **密钥** | `L_i ←$ {0,1}^κ`，κ ≥ λ（对称密钥长度，如 256 位） |
| **中间变量** | 无 |
| **公式** | `L_i =$ random`，对所有 `1 ≤ i ≤ 2N−1`，且**两两独立** |
| **数据依赖** | 无（各密钥独立） |
| **正确性条件** | 每个节点有且仅有一把密钥 |
| **安全性依赖** | 密钥来自**安全随机源**（CSPRNG）；信息论意义下要求真正独立均匀随机 |
| **论文对应** | Section 3.1：「assign an independent and random key `L_i` to every node `v_i`」 |

---

## 4. KeyGen / 密钥分配（原文称 Scheme Initiation）

| 项 | 内容 |
|---|---|
| **输入** | 用户身份 `u_j`（叶子 `v_{N+j}`） |
| **输出** | 用户私钥 `K_u_j`（一个密钥集合） |
| **参数** | 路径长度 h+1 |
| **随机变量** | 无（纯分发，密钥已在 Setup 生成） |
| **密钥** | 路径上所有节点的 `L_i` |
| **中间变量** | `path(u_j) = { v_1, v_2, …, v_{N+j} }`（从根到叶的祖先链） |
| **公式** | `K_u_j = { L_i : v_i ∈ path(u_j) }`，共 `log₂N + 1` 把 |
| **数据依赖** | 依赖 Setup 生成的 `{L_i}` |
| **正确性条件** | `u_j` 能推导出所有满足 `u_j ∈ S_i` 的子集密钥 `L_i` |
| **安全性依赖** | 用户只能获得自己路径上的密钥，无法获得其他节点密钥 |
| **论文对应** | Section 3.1：「Provide every receiver u with the log N + 1 keys associated with the nodes along the path from the root to leaf u」 |

---

## 5. Encrypt（原文称 Broadcast）

| 项 | 内容 |
|---|---|
| **输入** | 明文消息 M；撤销集合 R |
| **输出** | 广播密文 `(header, body)` |
| **参数** | h、N、r = |R| |
| **随机变量** | 会话密钥 K；E 的随机化（若 E 为概率加密） |
| **密钥** | 覆盖子集对应的 `{L_{i_1}, …, L_{i_m}}`；会话密钥 K |
| **中间变量** | Steiner 树 `ST(R)`；覆盖 `{S_{i_1}, …, S_{i_m}}` |
| **公式** | 见下方步骤 |

**步骤（原文）**：

1. 选择会话加密密钥 `K ←$ {0,1}^κ`（随机比特串）。
2. 对撤销集 R，计算 `ST(R)`（R 的叶子 + 根的 Steiner 树）。
3. 找覆盖 `N\R` 的互不相交子集 `{S_{i_1}, …, S_{i_m}}`：
   > 覆盖 = 所有「挂在 ST(R) 上」的子树——其根 `v` 与 ST(R) 中**出度为 1** 的节点相邻、但 `v` 本身不在 ST(R) 中。
   > 原文：「all subtrees of the original tree that "hang" off ST(R), i.e. all subtrees whose roots are adjacent to nodes of outdegree 1 in ST(R), but they are not in ST(R).」
4. 取对应密钥 `L_{i_1}, …, L_{i_m}`。
5. 用每个密钥加密会话密钥 K，构成 header；消息用 K 加密构成 body：

```
header = ( [i_1, …, i_m],  E_{L_{i_1}}(K), …, E_{L_{i_m}}(K) )
body   = F_K(M)
密文   = ( header, body )
```

| 数据依赖 | K → body；{L_{i_j}} → header |
| 正确性条件 | 覆盖 `{S_{i_j}}` 恰好划分 `N\R`（不遗漏、不重复、不包含 R） |
| 安全性依赖 | E 为语义安全（header 部分）；F 为一次性语义安全（body 部分）；覆盖不含任何撤销用户 |
| 论文对应 | Section 2.2（Broadcast 算法）+ Section 3.1（覆盖方法） |

---

## 6. Decrypt（原文称 Decryption Step）

| 项 | 内容 |
|---|---|
| **输入** | 广播密文 `(header, body)`；用户私钥 `K_u_j` |
| **输出** | 明文 M（或解密失败 ⊥） |
| **参数** | h |
| **随机变量** | 无 |
| **密钥** | 用户路径上的某把 `L_i` |
| **中间变量** | 命中覆盖子集 `S_i` 的判定 |

**步骤（原文）**：

1. 在 header 索引 `[i_1, …, i_m]` 中查找 `u_j` 的某个祖先：找 `i*` 使 `u_j ∈ S_{i*}`。
   - 若不存在（`u_j` 被撤销）→ 输出 ⊥（结果为空）。
   - 注意：这样的祖先**至多一个**（路径上唯一）。
2. 从私钥 `K_u_j` 中取出 `L_{i*}`。
3. 计算 `K = D_{L_{i*}}( E_{L_{i*}}(K) )`（解密 header 对应项得会话密钥）。
4. 计算并输出 `M = F_K^{-1}( body )`。

| 数据依赖 | `L_{i*}` → K → M |
| 正确性条件 | `E`/`F` 解密正确；`u_j ∈ S_{i*}` 时必能恢复 K |
| 安全性依赖 | 撤销用户不在任何 `S_{i*}` 中，因此无 `L_{i*}`，无法恢复 K |
| 论文对应 | Section 3.1：「The Decryption Step」 |

---

## 7. 正确性论证

1. **授权用户 `u_j ∉ R` 能解密**：覆盖 `{S_{i_j}}` 恰好划分 `N\R`，故 `u_j` 属于唯一一个 `S_{i*}`；由密钥分配，`u_j` 持有 `L_{i*}`；`K = D_{L_{i*}}(E_{L_{i*}}(K))` 成立；`M = F_K^{-1}(F_K(M))` 成立。
2. **撤销用户 `u_j ∈ R` 不能解密**：覆盖由「ST(R) 悬挂子树」构成，任何 `S_i` 都不含 R 中叶子（原文：「this collection covers all nodes in N\R and only them」）；故 `u_j` 不在任何 `S_{i*}` 中，其路径上无 `L_{i*}`，无法从 header 恢复 K。

---

## 8. 安全性（信息论 key-indistinguishability）

- CS 的密钥分配是**信息论安全**：各 `L_i` 独立随机。
- 满足 Subset-Cover 框架的 **key-indistinguishability** 性质：对任意覆盖子集 `S_i`，其密钥 `L_i` 对「所有不在 `S_i` 中的用户所持有的全部信息」而言，与随机密钥不可区分（此处是**信息论意义下**的不可区分，因为被撤销用户完全不持有 `L_i`）。
- 结合 `E`（header，需 chosen-ciphertext / preprocessing 语义安全）与 `F`（body，需 chosen-plaintext 一次性语义安全）的安全性，由 NNL01 **Theorem 11** 得到 CS 的安全性；并由 **Theorem 1** 给出复杂度。

---

## 9. 复杂度（论文 Theorem 1）

| 指标 | CS 方法 |
|---|---|
| 消息长度（header） | 至多 `r·log(N/r)` 个密钥（最坏情况） |
| 接收者存储 | `log₂N + 1` 把密钥（= O(log N)） |
| 接收者处理时间 | O(log log N) 次查找 + **1 次**解密 |
| 加密端 | 找覆盖 O(r log N)；加密 ∝ 覆盖子集数 |

---

## 10. N=8 完整手算示例

> 用户编号采用 1-based（u1…u8），与 `src/cs/tree.py` 的对外 API 一致。

### 10.1 树结构与编号（N=8, h=3, 节点 1…15）

```
                 (1)
             /         \
          (2)           (3)
         /   \         /   \
      (4)     (5)    (6)     (7)
      / \     / \    / \     / \
    (8) (9)(10)(11)(12)(13)(14)(15)
    u1  u2  u3  u4   u5  u6  u7  u8
```

### 10.2 密钥分配（每用户路径密钥）

| 用户 | 叶子 | 路径节点 | 持有密钥（4 把） |
|---|---|---|---|
| u1 | v8 | 1,2,4,8 | L1, L2, L4, L8 |
| u2 | v9 | 1,2,4,9 | L1, L2, L4, L9 |
| u3 | v10 | 1,2,5,10 | L1, L2, L5, L10 |
| u4 | v11 | 1,2,5,11 | L1, L2, L5, L11 |
| u5 | v12 | 1,3,6,12 | L1, L3, L6, L12 |
| u6 | v13 | 1,3,6,13 | L1, L3, L6, L13 |
| u7 | v14 | 1,3,7,14 | L1, L3, L7, L14 |
| u8 | v15 | 1,3,7,15 | L1, L3, L7, L15 |

### 10.3 手算：撤销 R = {u3}（叶子 v10）

**ST(R)** = 根到 v10 的路径 = {v1, v2, v5, v10}。

- v1：子节点 v2 ∈ ST、v3 ∉ ST → 出度 1，悬挂子树 **S3**（挂 v3）
- v2：子节点 v4 ∉ ST、v5 ∈ ST → 出度 1，悬挂子树 **S4**（挂 v4）
- v5：子节点 v10 ∈ ST、v11 ∉ ST → 出度 1，悬挂子树 **S11**（挂 v11）
- v10：叶子，出度 0，不产生

**覆盖** = { S3, S4, S11 } = { {u5,u6,u7,u8}, {u1,u2}, {u4} }，覆盖 N\R = {u1,u2,u4,u5,u6,u7,u8}，**3 个子集**。

**加密**（会话密钥 K）：

```
header = ( [3, 4, 11],  E_{L3}(K), E_{L4}(K), E_{L11}(K) )
body   = F_K(M)
```

**解密**：

| 用户 | 路径 | 命中祖先 | 结果 |
|---|---|---|---|
| u1 | 1,2,4,8 | v4 ∈ {3,4,11} → 用 L4 | ✓ 恢复 K → M |
| u2 | 1,2,4,9 | v4 → L4 | ✓ |
| **u3（撤销）** | 1,2,5,10 | 无（1,2,5,10 均不在 {3,4,11}） | ✗ 无法解密 |
| u4 | 1,2,5,11 | v11 → L11 | ✓ |
| u5 | 1,3,6,12 | v3 → L3 | ✓ |
| u6 | 1,3,6,13 | v3 → L3 | ✓ |
| u7 | 1,3,7,14 | v3 → L3 | ✓ |
| u8 | 1,3,7,15 | v3 → L3 | ✓ |

### 10.4 手算：撤销 R = {u3, u5}（叶子 v10、v12）

**ST(R)** = {v1, v2, v5, v10, v3, v6, v12}。

- v1：v2、v3 都在 ST → 出度 2，不产生
- v2：v4 ∉、v5 ∈ → 出度 1，挂 **S4** = {u1,u2}
- v5：v10 ∈、v11 ∉ → 出度 1，挂 **S11** = {u4}
- v3：v6 ∈、v7 ∉ → 出度 1，挂 **S7** = {u7,u8}
- v6：v12 ∈、v13 ∉ → 出度 1，挂 **S13** = {u6}

**覆盖** = { S4, S11, S7, S13 } = { {u1,u2}, {u4}, {u7,u8}, {u6} }，覆盖 N\{u3,u5}，**4 个子集**（≤ r·log(N/r) = 2·log₄(4)=4，达到上界）。

**header** = ( [4, 7, 11, 13], E_{L4}(K), E_{L7}(K), E_{L11}(K), E_{L13}(K) )

---

## 11. 混合加密设计（AES-GCM 实现图片/视频广播加密）

> 本设计是 **ENGINEERING ADAPTATION**（工程适配）：NNL01 原文的 `E_L`（header 块密码）与 `F_K`（body 流密码）是抽象原语，此处用 AES-256-GCM 具体化，并遵循 CLAUDE.md §3.3 的「AEAD 加密文件 + BE 保护会话密钥」原则。

### 11.1 架构（对应 CLAUDE.md §3.3）

```
原始文件 M（JPG/PNG/MP4）
      │
      ├─① 随机生成会话密钥 K（256 位）
      │
      ├─② AEAD 加密文件内容：body = AES-256-GCM(K, nonce_body, M)
      │        → (ciphertext, tag_body)   【大文件内容加密】
      │
      └─③ Broadcast Encryption 加密会话密钥 K：
               header = ( [i_1..i_m], E_{L_{i_1}}(K), …, E_{L_{i_m}}(K) )
               【广播加密只负责"谁拿得到 K"】
```

- **广播加密（CS）负责**：会话密钥 K 的受控分发（谁在广播集合 S = N\R 中）。
- **AES-GCM 负责**：大文件内容的机密性 + 完整性认证。
- **关键原则**：大文件**绝不**直接送入 CS 的 header；CS 只加密 256 位的 K。

### 11.2 原语映射

| NNL01 原语 | 原文建议 | 本项目工程适配 |
|---|---|---|
| `E_L`（header 加密 K） | block cipher | AES-256-GCM（对 K 做认证加密）或 AES-256-CTR |
| `F_K`（body 加密 M） | stream cipher XOR | AES-256-GCM（AEAD，附 16 字节 tag） |

### 11.3 加密包结构（版本化）

```
enc_packet = {
  version     : 1,
  header      : [ i_1,…,i_m,  E_{L_{i_1}}(K), …, E_{L_{i_m}}(K) ],  // CS 广播加密保护 K
  body        : ( nonce_body, ciphertext, tag_body ),              // AES-GCM 加密文件
  meta        : { filename, mime_type, size }                      // 非敏感元数据
}
```

### 11.4 加密流程

1. 读文件 M，保留 `filename`、`mime_type`、`size` 到 meta。
2. `K ← CSPRNG(32)`（256 位会话密钥）。
3. `nonce_body ← CSPRNG(12)`（96 位，一次性）。
4. `(ciphertext, tag_body) = AES-256-GCM.Encrypt(K, nonce_body, M)`。
5. 计算覆盖 `{S_{i_j}}`，对每个 `E_{L_{i_j}}(K)` 使用独立 nonce。
6. 组装 `enc_packet` 输出。

### 11.5 解密流程

1. 从 header 找命中祖先 `i*`，取 `L_{i*}`。
2. `K = D_{L_{i*}}(E_{L_{i*}}(K))`。**若认证失败 → ⊥**（header 被篡改）。
3. `M = AES-256-GCM.Decrypt(K, nonce_body, ciphertext, tag_body)`。
4. **验证 tag_body**：失败 → ⊥（文件被篡改）；成功 → 还原 M。

### 11.6 nonce / 完整性要点

- `nonce_body` 每次加密**新鲜随机**，禁止复用（同一 K 复用 nonce 会破坏 GCM 安全）。
- header 中每个 `E_{L_{i_j}}(K)` 的 nonce 也须唯一。
- 完整性：GCM tag 覆盖密文，任何篡改导致解密失败（不静默产出坏文件）。
- 授权用户能恢复 M；非授权用户拿不到 K，无法解密 body，也无法伪造。

---

## 12. 实现标注（CLAUDE.md §3.2）

| 部分 | 标注 |
|---|---|
| CS 树结构 / 密钥分配 / ST(R) 覆盖 / header+body | **PAPER-FAITHFUL**（忠实 Section 3.1） |
| `E_L`、`F_K` 用 AES-256-GCM 具体化 | **ENGINEERING ADAPTATION** |
| N=8 手算示例 | **TOY / DEMO**（教学演示，非正式安全参数） |
| 安全声明 | 仅 educational prototype；不声称密码学安全 |

---

## 13. 参考文献

- Naor, Naor & Lotspiech, *Revocation and Tracing Schemes for Stateless Receivers*, CRYPTO 2001, LNCS 2139, pp. 41–62 — ePrint 2001/059（本项目 `papers/NNL01-revocation-tracing.pdf`）
- 本文档对应其 Section 2（Subset-Cover 框架）、Section 3.1（Complete Subtree Method）、Section 6（安全性）与 Theorem 1 / Theorem 11。
