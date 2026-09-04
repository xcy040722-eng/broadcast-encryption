# Subset Difference (SD) 实现说明

> 阶段：M4 · 对应 Prompt 07 实现阶段
> 依据：`docs/sd-specification.md`（已核对的 NNL01 §3.2 / Figure 3 / Lemma 2 / Theorem 4）
> 性质：仅实现 NNL01 §3.2 的 SD 会话密钥广播加密，**不含文件 body 加密、不含 GUI**。

---

## 1. 文件与 NNL01 §3.2 对应关系

| 文件 | 对应论文内容 | 类别 |
|---|---|---|
| `src/sd/tree.py` | 满二叉树（receivers as leaves in a complete binary tree） | 论文原文 + heap 编号属工程选择 |
| `src/sd/prg.py` | §3.2「G triples the input；G_L=左1/3、G_R=右1/3、G_M=中1/3」 | 派生关系是论文原文，SHA-256 是工程实例化 |
| `src/sd/keys.py` | §3.2「LABEL_i」「hanging off the path」label 分配 | 论文原文 |
| `src/sd/cover.py` | §3.2 cover 算法（Step 1-3 迭代法） | 论文原文 |
| `src/sd/encrypt.py` | §2.2 框架（header = E_L(K)）+ §3.2 解密派生 | header 结构是论文原文，AES-GCM 是工程实例化 |
| `src/sd/serialization.py` | header 的工程序列化 | 工程选择 |

## 2. 论文原文 vs ENGINEERING ADAPTATION

### 论文原文（PAPER-FAITHFUL）

- **子集表示**：`S_{ij} = (v_i 子树) \ (v_j 子树)`，v_i 是 v_j 的祖先。
- **G 方向**：`G_L` = 左孩子 label、`G_R` = 右孩子 label、`G_M` = 节点 key（§3.2 原文逐字）。
- **label 分配**：每个内部节点 v_i 独立随机 `LABEL_i`；用户存储「挂在根到叶路径外侧」节点的 label + 全树 key。
- **密钥派生**：`L_{ij} = G_M(LABEL_{i,j})`，`LABEL_{i,j}` 沿 v_i→v_j 路径用 G_L/G_R 派生。
- **cover 算法**：ST(R) + 迭代 Step 1-3（找叶子对 → LCA → 加 S_{l,i}/S_{k,j} → 删后代）。
- **存储公式**：`½ log² N + ½ log N + 1`（Theorem 4）。

### ENGINEERING ADAPTATION

- **PRG 具体化**：论文 G 是抽象 PRG（triples the input）；本实现用 **SHA-256 做 domain separation**（`SHA256(domain ‖ seed)`，domain ∈ {left/right/middle}）。**不声称论文规定 SHA-256**。
- **E_L 具体化**：header 加密会话密钥用 **AES-256-GCM**（独立于 src/cs/）。**不声称论文规定 AES-GCM**。
- **节点编号**：heap 编号（根=1，左=2i，右=2i+1）是工程选择；论文只规定「complete binary tree」。
- **label 长度**：32 字节（256-bit）是工程选择，与 AES-256 密钥长度一致。
- **N=1 退化**：N=1 无内部节点，但仍为根节点生成 label 以提供整棵树 key（`G_M(LABEL_1)`）。

## 3. [UNCERTAIN]

- 与 `sd-specification.md` §12 一致：论文 Theorem 编号跳跃（1/4/11，缺 2/3）与 1.38r 求和式中项，均不影响 SD 实现。
- 本实现未发现新的 UNCERTAIN 项。

## 4. 实现中发现的问题

- **`sd-specification.md` §9.2 的挂起节点表已修正**：该表曾将 u3 的挂起节点写为 `{v3, v4, v9}`，正确为 **`{v3, v4, v11}`**（v5 的孩子是 v10、v11，不是 v9、v10）。正确的 u3 label 集合为 `{(1,3), (1,4), (1,11), (2,4), (2,11), (5,11)}`（共 6 个），实现与测试均已按正确值核对。

## 5. 测试覆盖

`tests/test_sd.py` 20 项，覆盖：
- 树结构 / LCA / ID 区分
- G_L/G_R/G_M 派生
- Setup / KeyGen（含 N=8 u3 的 7 个 material 精确断言）
- cover 六类场景（R={u3}、R={u3,u5}、R=∅、R=全部、随机、穷举 N≤8）
- cover 不重叠 / 不包含撤销 / union == N\R / ≤2r−1
- 加解密恢复（随机 N∈{1,2,4,8,16}）
- header 不泄露明文 K / 篡改 / 非法格式 / 序列化 round-trip

## 6. 定位声明

本项目实现了 **NNL01 §3.2 Subset Difference Method 的课程设计级工程化版本**（会话密钥广播加密层）。不宣称工业级安全，不宣称论文规定具体 Python/SHA-256/AES-GCM API。

## 7. 审计结论

SD 实现已通过代码级审计（依据 NNL01 §3.2 / Figure 3 / Lemma 2 / Theorem 4）：**PASS**。

- 无 CRITICAL / HIGH / MEDIUM 问题。
- 核心算法（cover Step 1-3、label 派生、KeyGen、存储量、加解密）忠实实现论文。
- 仅 4 项 LOW 级工程细节（私有函数导入、密文长度校验、宽异常捕获、O(r³) 效率），不影响正确性与安全性。
- 88 tests passed（CS 回归 39 + file crypto 29 + SD 20）。
