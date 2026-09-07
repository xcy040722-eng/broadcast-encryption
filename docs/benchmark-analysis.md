# CS vs SD Benchmark 分析（v1.2 正式结果）

> 实验基线：commit `482c6ef`（SD Cover chain 优化 + Benchmark harness v1.2）
> 环境：Windows 10 / Python 3.11.9 / cryptography 48.0.0 / 16 CPU / 15.2 GB RAM
> 数据：`benchmarks/results/raw.csv`（5120 行）、`summary.csv`（400 行）、`figures/`（6 张）

---

## 0. 四类信息标注

- **【论文理论】**：NNL01 论文给出的复杂度/性质。
- **【实现结果】**：本项目的 PAPER-FAITHFUL 算法语义（CS 完整子树、SD 子树差 S_ij）。
- **【工程优化】**：为可运行性做的工程适配（SD Cover chain 方法、AES-GCM、SHA-256 PRG）。
- **【实测结果】**：Benchmark 跑出的实际数据。

---

## 1. 核心结论（TL;DR）

**SD 通过更大的用户端 key material（约 5×）和显著更高的 KeyGen 计算成本（约 267×），换取低/中撤销率下更小的广播 Cover/Header（ρ=0.10 时 header 省约 44%）；该通信收益随撤销率提高而下降，在 ρ=0.50 时由于 SD entry 的双索引开销，Header 反而略大于 CS（约 +7%）。**

---

## 2. Cover Compression（cover 数量）

【论文理论】CS cover ≤ r·log(N/r)，SD cover ≤ 2r−1（Lemma 2）。

【实测结果】median cover count（case=random）：

| N | ρ | CS | SD | SD/CS |
|---|---|---|---|---|
| 256 | 0.01 | 18 | 4 | 22% |
| 1024 | 0.01 | 59 | 12 | 20% |
| 256 | 0.10 | 67 | 28 | 42% |
| 1024 | 0.10 | 271 | 113 | 42% |
| 256 | 0.25 | 98 | 58 | 59% |
| 1024 | 0.25 | 382 | 230 | 60% |
| 256 | 0.50 | 92 | 74 | 80% |
| 1024 | 0.50 | 366 | 294 | 80% |

【分析】SD 的 cover 压缩随 ρ 增大单调衰减：ρ=0.01 时 SD 仅 CS 的 ~20%，ρ=0.50 时升到 ~80%。这与理论一致——SD 的 2r−1 上界在 ρ 大时趋近 CS 的 r·log(N/r)。

---

## 3. Header Compression（序列化字节数）

【工程优化】header 用 JSON+base64 序列化；SD 每个 entry 用 `(i,j)` 双索引，CS 用单索引 `i`，故 SD 每 entry 的字节开销更大。

【实测结果】median header_bytes（case=random）：

| N | ρ | CS | SD | SD/CS |
|---|---|---|---|---|
| 256 | 0.10 | 5974 B | 3334 B | 0.56（省 44%） |
| 1024 | 0.10 | 24146 B | 13475 B | 0.56（省 44%） |
| 256 | 0.50 | 8214 B | 8818 B | 1.07（大 7%） |
| 1024 | 0.50 | 32866 B | 35217 B | 1.07（大 7%） |

【分析】Header 压缩是 Cover 压缩的**净效果**：ρ=0.10 时 SD 的 cover 更少 → header 更小（省 44%）；ρ=0.50 时 cover 数接近，但 SD 每 entry 多一个索引字段 → header 反而大 7%。**这是本 Benchmark 最重要的 trade-off 发现：SD 的 header 压缩收益只在中低撤销率成立。**

---

## 4. Key Material Overhead（用户端存储）

【论文理论】CS 存 log N + 1 个密钥；SD 存 ½log²N + ½logN + 1 个 label。

【实测结果】mean key/label 数量：

| N | CS | SD | SD/CS |
|---|---|---|---|
| 8 | 4 | 7 | 1.75× |
| 256 | 9 | 37 | 4.1× |
| 1024 | 11 | 56 | 5.1× |

【分析】SD 的用户端存储随 N 增长到 CS 的 ~5 倍，与理论（½log²N vs log N）一致。这是 SD 压缩 header 的**直接代价**——用「用户多存 label」换「广播 header 更短」。

> 口径：`key_material_mean`/`key_material_max` 为**用户持有的 key/label 数量（整数）**，非字节数。

---

## 5. KeyGen Overhead（密钥生成计算成本）

【工程优化】SD 的 KeyGen 用 GGM PRG（SHA-256）派生每用户 ~220 次（N=1024）；CS 的 KeyGen 直接存路径节点密钥（无派生）。

【实测结果】median 耗时（N=1024, ρ=0.25）：

| 阶段 | CS | SD | SD/CS |
|---|---|---|---|
| Setup | 0.87 ms | 0.41 ms | 0.47× |
| **KeyGen** | 3.25 ms | **869.05 ms** | **267×** |
| Cover | 1.78 ms | 2.08 ms | 1.17× |
| Header | 1.76 ms | 2.62 ms | 1.49× |
| AuthRecover | 0.02 ms | 0.14 ms | 7× |
| RevReject | 0.02 ms | 0.58 ms | 29× |

【分析】
- **KeyGen 是 SD 最大的计算代价（267×）**，源于 GGM PRG 的 SHA-256 派生。
- SD 的 Setup 反而更快（生成 N−1 个 label vs CS 生成 2N−1 个节点密钥）。
- Cover/Header/解密 SD 略慢，但绝对值均 <3ms，可忽略。
- 解密阶段 SD 慢（AuthRecover 7×、RevReject 29×），因为需要派生子树差密钥，但绝对值 <1ms。

---

## 6. 不同撤销比例 ρ 的影响

【实测结果】以 N=1024、case=random 为例：

| ρ | CS cover | SD cover | SD/CS | SD header 收益 |
|---|---|---|---|---|
| 0.01 | 59 | 12 | 20% | 显著压缩 |
| 0.10 | 271 | 113 | 42% | 压缩 44% |
| 0.25 | 382 | 230 | 60% | 压缩减弱 |
| 0.50 | 366 | 294 | 80% | **负收益（+7%）** |

【分析】SD 的优势集中在**低撤销率**场景（稀疏撤销，覆盖一棵大子树减去少量撤销点）。随着 ρ 升高，撤销点分散，SD 的「子树减子树」形状优势消失，header 压缩被双索引开销抵消。

---

## 7. 四类 R 的结构差异

【实测结果】median cover count（N=1024, ρ=0.25）：

| case | CS | SD | 说明 |
|---|---|---|---|
| random | 382 | 230 | 随机撤销（平均情况） |
| **contiguous** | 2 | 1 | 连续撤销（共享最长前缀） |
| **uniform** | 512 | 256 | 均匀分布（最分散） |
| **clustered** | 2 | 1 | 聚集撤销（同一子树） |

【分析】
- **连续/聚集撤销**（共享子树）→ cover 极小（1–2）：SD 和 CS 都能用一个 `S_root,child` 覆盖。
- **均匀分布**（最分散）→ cover 最大：SD=256=2r−1（达上界），CS=512≈2r。
- **random** 介于两者之间（平均情况）。
- 这印证了「树结构对 cover 影响极大」——撤销集的空间分布比撤销数量更能决定 header 大小。

---

## 8. SD 的实际 trade-off（综合）

| 维度 | SD 相对 CS | 方向 |
|---|---|---|
| Cover count | 少（低 ρ 时 20%，高 ρ 时 80%） | ✅ 收益 |
| Header bytes | 低 ρ 省 44%，ρ=0.5 大 7% | ⚠️ 有限收益 |
| Key material | 大 5×（用户端存储） | ❌ 代价 |
| KeyGen 计算 | 慢 267× | ❌ 代价 |
| Setup | 快 2× | ✅ 小收益 |
| Cover 计算 | 慢 1.17×（可忽略） | ≈ 中性 |
| 解密计算 | 慢 7–29×（绝对值 <1ms） | ≈ 中性 |

**净结论**：SD 适合「**低撤销率 + 广播 header 是主要通信成本 + 用户端能接受较多存储和计算**」的场景（如大规模订阅广播、数字版权分发）。在「高撤销率」或「用户端存储/计算受限」的场景下，SD 的收益消失甚至为负，CS 反而更优。

---

## 9. 数据一致性核验结论

- raw.csv **5120 行**、summary.csv **400 行**、figures **6 张** ✓
- `correct=True` **5120/5120 全通过** ✓
- `measurement` 与 v1.2 配置一致（N≤128→100、256→30、512→10、1024→3）✓
- CS/SD 相同 R：random case 1120 个 `(N,ratio,trial)` 组 seed 全部一致 ✓
- summary 与 raw 聚合一致性：400 组 `cover_count_median` 用 `statistics.median` 核验 **0 mismatch** ✓
- Key material 口径：key/label 数量（整数 [4,56]），非字节数 ✓

---

## 10. 与论文理论的对账

| 项 | 论文理论 | 实测结果 | 是否一致 |
|---|---|---|---|
| SD cover ≤ 2r−1 | Lemma 2 | 均匀分布时 SD=256=2r−1（达上界），random 时 ≤ 上界 | ✅ |
| CS cover ~ r·log(N/r) | §3.1 | CS=382（N=1024,ρ=0.25）≈ 2r·log(4) 量级 | ✅ |
| SD 存储 ½log²N | Theorem 4 | N=1024 时 SD=56≈½·100 | ✅ |
| CS 存储 log N | Theorem 1 | N=1024 时 CS=11=log N+1 | ✅ |
| SD KeyGen 更贵 | GGM PRG 计算分配 | KeyGen 267× | ✅ |

理论与实测一致，未发现偏离。

---

## 11. 参考

- 论文：NNL01（`papers/NNL01-revocation-tracing.pdf`）§3.1 / §3.2 / Lemma 2 / Theorem 1 / Theorem 4
- 规格：`docs/cs-specification.md`、`docs/sd-specification.md`
- 实现：`src/cs/`、`src/sd/`、`src/file_crypto/`
- Benchmark：`benchmarks/`（v1.2），结果 `benchmarks/results/`
