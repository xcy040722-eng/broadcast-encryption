# Complete Subtree (CS) Baseline — 密码学与算法一致性审计

> 阶段：M1 · 对应 Prompt 05
> 性质：**纯审计，未修改任何代码、未新增任何功能。**
> 审计对象：`src/cs/`（tree / crypto / keys / cover / encrypt / serialization）与 `tests/`
> 审计依据：NNL01 原文（`papers/NNL01-revocation-tracing.pdf`）Section 2.2（框架）、2.3（安全）、3.1（CS 方法）、Theorem 1。

---

## 0. 最终判定

# **PASS**

核心算法**忠实对应 NNL01 Section 3.1**，39 项测试全部通过。审计发现的 **M1、M2、L1、L5 已修复**（见 §7.1 修复记录），无遗留 CRITICAL / HIGH / MEDIUM 问题。剩余 L2、L3、L4 为 LOW 级可选改进，不影响正确性与安全性。

---

## 1. 三类实现标注（PAPER-FAITHFUL / ENGINEERING / PROJECT-SPECIFIC）

| 文件 | 内容 | 标注 |
|---|---|---|
| `tree.py` | 满二叉树 2N−1 节点、路径/祖先/子树 | **PAPER-FAITHFUL** + 编号方案属 PROJECT-SPECIFIC |
| `keys.py` `setup` | 每节点独立随机密钥 `L_i` | **PAPER-FAITHFUL** |
| `keys.py` `keygen` | 根到叶路径 log₂N+1 把密钥 | **PAPER-FAITHFUL** |
| `cover.py` `steiner_tree`/`cover` | ST(R) 与悬挂子树覆盖 | **PAPER-FAITHFUL** |
| `encrypt.py` | header 结构 `([i], E_{L_i}(K))`、解密命中逻辑 | **PAPER-FAITHFUL** |
| `crypto.py` | E_L 用 AES-256-GCM；secrets 随机 | **ENGINEERING ADAPTATION** |
| `serialization.py` | JSON+base64 header 序列化 | **ENGINEERING ADAPTATION** |
| heap 编号、R=∅ 边界、cover/encrypt 分层 | 课程设计自加 | **PROJECT-SPECIFIC** |

---

## 2. 逐项一致性核查

### 2.1 Setup

- **原文**：满二叉树 N 叶子（N=2 的幂），共 2N−1 节点；「assign an independent and random key L_i to every node v_i」。
- **代码**：`setup(n)` → `CompleteSubtreeTree(n)`（校验 N 为 2 的幂，`node_count = 2N−1`）+ `{i: random_key() for i in 1..2N−1}`。
- **结论**：**一致**。`random_key()` 用 `secrets.token_bytes(32)`，满足「independent and random」。

### 2.2 KeyGen

- **原文**：「Provide every receiver u with the log N + 1 keys associated with the nodes along the path from the root to leaf u」。
- **代码**：`keygen` → `{i: node_keys[i] for i in tree.ancestors(leaf_of_user(user_id))}`；`ancestors` 返回 `[leaf, …, root]`，长度 `h+1 = log₂N+1`。
- **结论**：**一致**。

### 2.3 Cover / ST(R)

- **原文**：ST(R) 为 R 的叶子与根的 Steiner 树；覆盖 = 「all subtrees that hang off ST(R)，即根与 ST(R) 中出度 1 节点相邻、但不在 ST(R) 中的子树」。
- **代码**：`steiner_tree` 求每个撤销叶子到根路径的并集；`cover` 遍历 ST 节点，取 `in_st_children == 1`（出度 1）节点的「非 ST 孩子」为悬挂根。
- **结论**：**一致**。N=8 手算 `R={u3}→[3,4,10]`、`R={u3,u5}→[4,7,10,12]` 与 `docs/cs-specification.md` §10 完全吻合。

### 2.4 Encrypt

- **原文**：`header = ([i_1..i_m], E_{L_i1}(K), …, E_{L_im}(K))`，`body = F_K(M)`。
- **代码**：`encrypt_session_key` 产出 `{"indices": cover_roots, "encrypted": [AES-GCM(L_i, K) …]}`。**body（F_K）未实现**（属 Prompt 06 混合加密范围，本阶段合理缺省）。
- **结论**：header 部分**一致**；body 缺省为**阶段内合理**，非缺陷。

### 2.5 Decrypt

- **原文**：「Find i_j such that u ∈ S_{i_j}（无则 null）；Extract L_{i_j}；Compute K；Compute M」。
- **代码**：`decrypt_session_key` 遍历 header，`if i in user_key`（即 v_i 是用户祖先 ⟺ u∈S_i），命中则 `decrypt_key` 恢复 K；无命中返回 None。M 恢复同 body 缺省。
- **结论**：K 恢复部分**一致**；「至多一个祖先」由覆盖互不重叠保证（见 §3.3）。

---

## 3. 重点核查项结论

### 3.1 Cover 是否覆盖全部非撤销用户、不覆盖任何撤销用户

**通过。** `tests/test_cover.py::test_cover_exactly_partitions` 对 N∈{1,2,4,8,16} **穷举所有撤销子集**，断言 `covered == N\R`。这同时证明了「不遗漏」与「不含撤销用户」。

### 3.2 各覆盖子树是否互不重叠

**算法上保证，但测试未显式验证（MEDIUM-1）。** 原文保证覆盖是「disjoint subsets」；代码忠实实现悬挂子树算法，因此两两不重叠（证明见 §3.3）。但现有测试用 `set` 并集断言 `== N\R`，无法区分「有重叠但并集仍正确」的情况，存在测试盲区。

### 3.3 「至多一个祖先」的正确性

**成立。** 覆盖根是「ST(R) 中出度 1 节点的非 ST 孩子」。任取两个覆盖根 a、b，若 a 是 b 的祖先，则 a 在 b 到根的路径上；但 b 的父节点 q 在 ST，而 q 的所有祖先（含 a，若 a 是 q 的祖先）都在 ST，与「a 不在 ST」矛盾。故任意两个覆盖根互不为祖先，子树互不重叠，用户至多命中一个。此性质使 `decrypt_session_key` 中「命中即返回」的早退逻辑正确。

### 3.4 header 密钥是否确为用户路径密钥

**是。** `user_key` 由 `keygen` 生成为路径密钥 dict；`decrypt_session_key` 用 `i in user_key` 精确判定「v_i 是否在用户路径上」，等价于原文「find whether any of its ancestors is among i_1..i_m」。

### 3.5 授权/撤销用户解密逻辑

**符合。** 授权用户命中唯一覆盖子集 → 用路径密钥 L_i 解密 K；撤销用户路径上无任何覆盖根 → 返回 None。测试 `test_encrypt_decrypt.py` 六类场景 + 随机化验证全部通过。

### 3.6 「测试通过但算法与论文不同」

**未发现。** 核心四算法逐项对照 §2，均忠实原文，无隐性语义偏移。

---

## 4. 问题分级清单

### MEDIUM

#### M1 — 覆盖互不重叠未显式测试 — **[已修复]**
- **文件/函数**：`tests/test_cover.py::test_cover_exactly_partitions`
- **问题**：仅断言 `set(covered) == N\R`，未断言子树叶子数之和等于 `N−|R|`。
- **为什么有问题**：`set` 并集天然去重，即使存在重叠子树也能通过 `== N\R`，无法暴露「覆盖不互斥」的潜在 bug。
- **建议**：增加断言 `sum(len(tree.users_in_subtree(r)) for r in roots) == N - len(R)`（子树大小之和 = 非撤销用户数 ⟺ 两两不重叠）。

#### M2 — 解密异常处理过宽 — **[已修复]**
- **文件/函数**：`src/cs/encrypt.py::decrypt_session_key`
- **问题**：`except Exception` 捕获一切异常，并把「撤销（无命中）」与「命中但认证失败」统一折叠为 `None`。
- **为什么有问题**：(1) 过宽的异常捕获会掩盖真实编程错误（如 TypeError、KeyError）；(2) 两种失败语义不同，合并后调用方无法区分「合法拒绝」与「密文被篡改」。
- **建议**：改为 `from cryptography.exceptions import InvalidTag` 后 `except InvalidTag: return None`；在 docstring 明确「None 表示无法恢复（撤销或认证失败）」。

### LOW

#### L1 — 用户编号 0-based vs 1-based — **[已修复]**
- **文件/函数**：`tree.py::leaf_of_user/user_of_leaf` 等全部对外接口
- **问题**：代码内部与测试用 0-based（`u0..uN−1`），而 Prompt 04 的测试描述用 1-based（`u1..uN`）。
- **为什么有问题**：课程设计答辩/演示面向「用户列表 Alice/Bob/…」的自然编号是 1-based；0-based 易造成理解偏差。
- **建议**：**代码内部保留 0-based**（叶子 = N + user_id 的映射最简洁），在对外 API / GUI / 文档层统一暴露 1-based，转换集中在一处。

#### L2 — Encrypt 接口是 cover_roots 而非 revoked_set
- **文件/函数**：`src/cs/encrypt.py::encrypt_session_key(node_keys, cover_roots, session_key)`
- **问题**：Prompt 04 描述接口为 `Encrypt(revoked_set, session_key)`，当前 `encrypt_session_key` 要求调用方先 `cover()` 得到 `cover_roots`。
- **为什么有问题**：接口与描述不一致，调用方需多一步，且易误传错误的覆盖。
- **建议**：保留底层 `encrypt_session_key`，另提供便捷函数 `encrypt(node_keys, tree, revoked_set, session_key)` 内部完成 `cover` 后再加密。

#### L3 — R=∅ 边界处理未在代码标注
- **文件/函数**：`src/cs/cover.py::cover`（`if len(revoked) == 0: return [tree.root]`）
- **问题**：R=∅ 时 ST(∅) 未定义，「悬挂子树」概念不适用，代码做了语义补全（覆盖 = 整个树 S₁）。
- **为什么有问题**：这是原文未明确给出的边界，属于 PROJECT-SPECIFIC 补全，未标注易被误读为「论文算法的一部分」。
- **建议**：加一行注释标注「PROJECT-SPECIFIC：R=∅ 时覆盖 = 根子树（符合框架 N\R = N 的划分语义）」。

#### L4 — 节点密钥独立性测试弱
- **文件/函数**：`tests/test_setup_keygen.py::test_node_keys_independent`
- **问题**：断言「2N−1 个密钥两两不同」。
- **为什么有问题**：「不同」是独立随机的弱证据（32 字节碰撞概率可忽略），无法验证「随机性」本身。
- **建议**：保留该 sanity check，但明确其定位；随机性由 `secrets.token_bytes` 保证（代码层面已正确），无需也无法用黑盒测试证明独立性。

#### L5 — header 结构健壮性（zip 隐式截断） — **[已修复]**
- **文件/函数**：`src/cs/encrypt.py::decrypt_session_key`（`zip(header["indices"], header["encrypted"])`）
- **问题**：若 header 被外部破坏导致 `indices` 与 `encrypted` 长度不一致，`zip` 会静默截断到较短一方，而非报错。
- **为什么有问题**：篡改的 header 可能被静默处理，掩盖损坏。
- **建议**：进入循环前显式校验 `len(indices) == len(encrypted)`，不匹配则返回 None 或抛异常。

---

## 5. AES-GCM 工程实例化评估（ENGINEERING ADAPTATION）

- **原文 E_L**：块密码（block cipher），且 Section 2.3 要求 E 达到 **chosen-ciphertext（CCA）语义安全**（pre-processing mode）。
- **原文 F_K**：流密码 XOR，要求 chosen-plaintext 一次性语义安全（尚未实现，Prompt 06）。
- **当前 E_L = AES-256-GCM**：
  - GCM 是认证加密（AEAD），提供 **IND-CCA** 安全（nonce 不重用时），**满足且超出**原文对 E 的 CCA 要求。
  - **优于**「纯 block cipher（如 AES-ECB/CBC）」——后者仅 CPA，不满足原文的 CCA 要求。
  - 结论：**该工程实例化是正确且更安全的选择**，标注 ENGINEERING ADAPTATION 恰当。

### 密钥 / nonce / 随机 / 序列化 / 认证失败安全性核查

| 项 | 结论 |
|---|---|
| 密钥生成 | `secrets.token_bytes(32)`（CSPRNG），**非 `random`** ✓ |
| nonce | `encrypt_key` 每次生成独立随机 12 字节 nonce，**不复用** ✓ |
| 明文会话密钥 | header 中仅存 AES-GCM 密文，`test_ciphertext_does_not_reveal_session_key` 已断言 ✓ |
| 序列化 | indices 明文（本就公开）+ encrypted base64（密文），无泄露 ✓ |
| 认证失败 | GCM 认证失败抛 `InvalidTag`，`decrypt_session_key` 返回 None（不静默产出坏结果），`test_tampered_header_fails` 已验证 ✓ |
| 密钥长度 | L_i 与 K 均为 32 字节，恰为 AES-256 密钥长度 ✓ |

---

## 6. 原文 vs 代码差异明细（逐条）

| 原文 | 当前代码 | 差异 | 影响正确性？ |
|---|---|---|---|
| N 为 2 的幂的满二叉树 | 同，非 2 幂抛 ValueError | 无 | 否 |
| 每节点独立随机 L_i | 同 | 无 | 否 |
| 用户存根到叶 log N+1 把 | 同 | 无 | 否 |
| ST(R) 悬挂子树覆盖 | 同 | 无 | 否 |
| header = [indices, E_L(K)] | 同（E_L=AES-GCM） | E_L 具体化为 AEAD | 否（更安全） |
| body = F_K(M) | **未实现** | 缺省，属 Prompt 06 | 否（阶段内） |
| 解密找祖先、至多一个 | 同 | 无 | 否 |
| R=∅ 未明确 | 补全为覆盖根 | PROJECT-SPECIFIC 边界 | 否 |

---

## 7. 修改建议汇总（按优先级）

1. **[MEDIUM] 补测试**：覆盖子树大小之和 == N−|R|（证明互不重叠）。
2. **[MEDIUM] 收窄异常**：`except InvalidTag` 替代 `except Exception`。
3. **[LOW] 编号**：对外 API/GUI 统一 1-based，内部保留 0-based。
4. **[LOW] 接口**：提供 `encrypt(tree, node_keys, revoked_set, K)` 便捷函数。
5. **[LOW] 标注**：R=∅ 补全、L5 header 长度校验。

> 以上均不涉及算法核心变更，属「加固 + 补测试 + 工程约定」，不影响 PAPER-FAITHFUL 定位。

### 7.1 修复记录（2026-09-04）

| 编号 | 修复内容 | 涉及文件 |
|---|---|---|
| M1 | 新增 `test_cover_subtrees_disjoint`：断言 `sum(len(users_in_subtree(r))) == N−len(R)`，穷举 N∈{1,2,4,8,16} 所有撤销子集 | `tests/test_cover.py` |
| M2 | `decrypt_session_key` 改为 `except InvalidTag`，其他异常不吞；docstring 区分「无命中=无权」「InvalidTag=篡改」「其他=抛出」 | `src/cs/encrypt.py` |
| L5 | `decrypt_session_key` 开头显式校验 `len(indices) == len(encrypted)`，不一致抛 `ValueError`；新增 `test_header_length_mismatch_raises` | `src/cs/encrypt.py`、`tests/test_boundary.py` |
| L1 | 用户编号统一 1-based（u1..uN）：`leaf_of_user`/`user_of_leaf`/`users_in_subtree` 改 1-based，内部叶子映射保留 `N+user_id−1`；同步更新全部测试与 `cs-specification.md` §10 | `src/cs/tree.py`、全部测试、`docs/cs-specification.md` |

**验证**：完整测试套件 **39 passed**（原 37 + M1/L5 各新增 1 项）。

**未落实（LOW 级可选）**：L2（便捷 `encrypt(revoked_set)` 接口）、L3（R=∅ 边界注释标注）、L4（独立性测试定位说明）——均为非阻塞改进，可在后续阶段顺带处理。

---

## 8. 参考文献

- Naor, Naor & Lotspiech, *Revocation and Tracing Schemes for Stateless Receivers*, CRYPTO 2001, LNCS 2139 — ePrint 2001/059。
- 对应 Section 2.2 / 2.3 / 3.1 / Theorem 1。
