# CHW25 Distributed Broadcast Encryption — 课程实现规格（Construction 6.4）

> 阶段：M5 · CHW25 DBE 实现规格
> 依据：`papers/Registered ABE and Adaptively-secure Broadcast Encryption fr.pdf`
> **Section 6.1（Construction 6.4 / Theorem 6.5 / Theorem 6.6）**；依赖 **Section 3（Lemma 3.8、Eq. (3.1)）** 与 **Section 4（Lemma 4.5、Lemma 4.7）**
> 模块：`src/chw25_dbe/`
> 性质：**relation-preserving educational implementation**（保持代数正确性结构，不声称完整密码学安全性）

---

> ## 声明（必读）
>
> **This implementation preserves the algebraic correctness structure of CHW25 Construction 6.4 but does not claim the full cryptographic security of the paper's lattice trapdoor and Gaussian-sampling instantiation.**

---

## 1. 论文接口（忠实保留）

```
Π_DBE = (Setup, KeyGen, IsValid, Encrypt, Decrypt)
```

| 算法 | 论文输入/输出 |
|---|---|
| **Setup(1^λ, 1^N)** | → `pp = (A, p, V, Z, {r_i, t_i}_{i∈[N]}, T_V, T_Ẑ)` |
| **KeyGen(pp, i)** | → `pk_i = (W_i, {y_{i,j}}_{j≠i})`, `sk_i = y_{i,i}` |
| **IsValid(pp, i, pk_i)** | → `1` iff `∀j≠i: A y_{i,j} = W_i r_j` 且 `‖y_{i,j}‖ ≤ β_key` |
| **Encrypt(pp, {(j,pk_j)}_{j∈S}, μ)** | → `ct = (ξ, c_1^T, c_2^T, c_3)` |
| **Decrypt(pp, {(j,pk_j)}_{j∈S}, ct, (i, sk_i))** | → `μ ∈ {0,1}` |

---

## 2. 论文核心代数结构（必须在代码中显式保存并可测试）

### 2.1 密钥关系（Theorem 6.5 的 Eq. (6.6)/(6.7)）

```
(6.6)   A·y_{i,i} = W_i·r_i + p            ← 用户 i 自己的分量
(6.7)   A·y_{i,j} = W_i·r_j ,  j ≠ i       ← 用户 i 为其他用户存的分量
```

### 2.2 加密时重随机化关系（Theorem 6.6 的 Eq. (6.8)）

```
(6.8)   A·y_{0,i} = W_0·r_i ,  i ∈ S
```

### 2.3 密文（Construction 6.4）

```
ct = (ξ, c_1^T, c_2^T, c_3)

c_1^T = s^T A + e^T
c_2^T = s^T (W_0 + W_S) + e^T K_W        W_S = Σ_{j∈S} W_j
c_3   = s^T p + e^T k_p + μ·⌊q/2⌋
```

### 2.4 解密（Construction 6.4）

```
z = c_3 + c_2^T·r_i − c_1^T·( y_{i,i} + y_{0,i} + Σ_{j∈S\{i}} y_{j,i} )

⌊z⌉ = 0  若 −q/4 ≤ z < q/4
     1  否则
若 i ∉ S，输出 0
```

### 2.5 为什么正确（Theorem 6.6 的推导，代码 trace 需复现）

```
c_1^T(y_{i,i} + y_{0,i} + Σ_{j∈S\{i}} y_{j,i})
  = s^T(W_i r_i + p + W_0 r_i) + Σ_{j∈S\{i}} s^T W_j r_i + ẽ_1
  = s^T(W_S r_i + p + W_0 r_i) + ẽ_1            （用 W_S = Σ_{i∈S}W_i、i∈S）

c_3 + c_2^T r_i = μ⌊q/2⌋ + s^T p + s^T(W_0 + W_S) r_i + ẽ_2
                 где ẽ_2 = e^T k_p + e^T K_W r_i

⟹ z = c_3 + c_2^T r_i − c_1^T(...) = μ·⌊q/2⌋ − ẽ_1 + ẽ_2
```

**s^T 项完全精确抵消**（无噪声残留），剩下的 `(ẽ_2 − ẽ_1)` 全部来自 `e`、`k_p`、`K_W` 与各 `y`。`|ẽ_1 − ẽ_2| < q/4` 时正确。

---

## 3. Pedagogical Substitutions（教学替代，逐条对照）

> 以下替代**保持代数正确性结构**（Eq. (6.6)/(6.7)/(6.8) 精确成立），但**不是**论文正式实现。

| # | 论文正式做法 | 课程替代 | 影响 |
|---|---|---|---|
| **S1** | `SuccinctTrapGen` + `Transform` 生成 `(V, Z, R, T_V, T_Ẑ)`，`V = [I_N⊗A \| M_{Z,R}]` | **不实现**。取 `r_i = e_i`（标准基向量），`m ≥ N`；直接按代数式构造 `W_i` | 失去 succinct/trapdoor 结构 |
| **S2** | `V · T_V = G_{nN}` 的 gadget trapdoor；Kronecker 恒等式 `Z(I_k⊗r_j)d_i = Z(d_i⊗I_m)r_j`（Eq. (3.1)） | **绕过**：直接令 `W_i[:,i] = A y_{i,i} − p`、`W_i[:,j] = A y_{i,j}`（j≠i） | `Z`、`d` 不再出现 |
| **S3** | `KeyGen` 用 `SamplePre(V, T_V, η_i⊗p, σ_key)` 采样离散高斯 preimage | 直接从低范数分布采样 `y_{i,j}`（小整数），再**反向构造** `W_i` 使其满足 Eq. (6.6)/(6.7) | 分布非高斯、无 trapdoor 保证 |
| **S4** | `DimRed(A, M_{Z,R}, T_V, S)` 做维度约简 | **不实现**，直接用 `S` 构造 | 失去 succinct 收益 |
| **S5** | `DGS.SamplePre(...; H_ρ(ξ))` 采样 `y_{0,j}`，`W_0 = Z(d_0⊗I_m)`（Eq. (6.5)） | `derive_rerandomization(pp, S, ξ)`：以 `ξ‖S` 为**确定性**随机源生成低范数 `y_{0,i}`，令 `W_0[:,i] = A y_{0,i}`（i∈S） | **不是** explainable DGS；安全性论证不成立 |
| **S6** | `e ← D^m_{Z,σ_LWE}` 离散高斯噪声 | 小整数噪声（如 `{−1,0,1}` 或小高斯） | 无高斯宽度保证 |
| **S7** | `q` 满足 `q ≥ 4m^{3/2}σ_LWE(Nβ_key+β_agg) + 8ℓ_0m^5σ_LWEσ_pp` | 取较大 toy prime（如 `q=104729`），噪声远小于 `q/4` | 无安全性（参数太小） |

### 3.1 `r_i = e_i` 为什么能让替代成立

论文用 Kronecker 恒等式把 `Z(d⊗I_m) r` 化为 `Z(I_k⊗r)d`，从而用 trapdoor 生成满足关系的 `(y, d)`。
令 `r_i = e_i` 后，`W r_i = W[:, i]`（取第 `i` 列），于是关系退化为**逐列的向量等式**：

```
W_i[:, i] = A y_{i,i} − p
W_i[:, j] = A y_{i,j}          (j ≠ i)
W_0[:, i] = A y_{0,i}          (i ∈ S)
```

可直接构造 `W`（无需 trapdoor、无需 `Z`/`d`），且 Eq. (6.6)/(6.7)/(6.8) **精确成立**（非"约等于"）。

---

## 4. 忠实 vs 替代（汇总）

### 4.1 忠实来自论文（代码中保留且可测）

- `Π_DBE = (Setup, KeyGen, IsValid, Encrypt, Decrypt)` 五算法接口；
- 密钥结构 `pk_i = (W_i, {y_{i,j}}_{j≠i})`、`sk_i = y_{i,i}`；
- Eq. (6.6)/(6.7)/(6.8) 三条核心关系；
- 密文结构 `(ξ, c_1^T, c_2^T, c_3)` 与三个分量公式；
- 解密公式 `z = c_3 + c_2^T r_i − c_1^T(y_{i,i}+y_{0,i}+Σ_{j∈S\{i}}y_{j,i})`；
- 阈值判定 `[−q/4, q/4)`；`i ∉ S → 输出 0`；
- `W_S = Σ_{j∈S} W_j` 的聚合结构；
- Theorem 6.6 的**抵消结构**（s^T 项精确抵消，噪声仅来自 e 与 y）。

### 4.2 Pedagogical substitution（S1–S7，代码中明确标注）

- `SuccinctTrapGen` / `Transform` / `DimRed` / `Z` / `d` / `T_V` / `T_Ẑ`：**不实现**；
- `SamplePre`（离散高斯 preimage）：**不实现**，改为反向构造；
- `DGS.SamplePre` + explainable 性质（Eq. (6.5)）：**不实现**，改为确定性重随机化；
- 高斯噪声 `D_{Z,σ}`：**不实现**，改为小整数噪声；
- 正式参数（`σ_pp, σ_key, σ_agg, σ_LWE, β_key, β_agg, ℓ_0, k, m'`）：**不实现**，改为 toy 参数。

### 4.3 因此**不声称**的性质

- 不声称 succinct（公钥/密文大小不随 `N` 亚线性）；
- 不声称 semi-static / adaptive 安全性；
- 不声称对恶意公钥的防护（`IsValid` 只做关系检查）；
- 不声称 explainable DGS 或任何随机预言机论证。

---

## 5. 模块结构

```
src/chw25_dbe/
├── __init__.py
├── types.py        # Params / PublicParams / PublicKey / SecretKey / Ciphertext
├── algebra.py      # Z_q 运算、centered representative、范数、矩阵辅助
├── construction.py # Setup / KeyGen / IsValid / Encrypt / Decrypt + derive_rerandomization
└── trace.py        # decrypt_with_trace：输出每次解密的中间值（供可视化）
```

> 与 `src/cs/`、`src/sd/`、`src/file_crypto/` **完全独立**；不改任何现有模块与 UI。

---

## 6. 参数（集中配置）

```python
@dataclass(frozen=True)
class Params:
    n: int = 4          # 格维度
    m: int = 8          # ≥ N（供 N 个位置使用）
    q: int = 104729     # toy prime，⌊q/2⌋ = 52364
    N: int = 4          # 用户数
    noise_bound: int = 1   # e 的采样范围 {−1,0,1}
    y_bound: int = 1       # y_{i,j} 的采样范围 {−1,0,1}
```
> `q=104729` 为素数；`q/4 = 26182.25`，远超 toy 噪声量级，保证解码余量。
> **所有参数集中在 `Params`，代码中不散落 magic number。**

---

## 7. Trace 输出项（`trace.py`）

供后续动态可视化，逐项输出：

| 项 | 含义 |
|---|---|
| `c3` | 密文第三分量 |
| `c2_dot_r_i` | `c_2^T r_i` |
| `c1_dot_y_ii` | `c_1^T y_{i,i}` |
| `c1_dot_y_0i` | `c_1^T y_{0,i}` |
| `c1_dot_y_ji` | 各 `c_1^T y_{j,i}`（`j ∈ S\{i}`） |
| `c1_term_total` | `c_1^T(y_{i,i}+y_{0,i}+Σ y_{j,i})` |
| `z_before_center` | 抵消后的 `z`（未取中心代表） |
| `z_centered` | 中心代表 `z' ∈ [−q/2, q/2)` |
| `noise_residual` | `z − μ̂·⌊q/2⌋`（即 `ẽ_2 − ẽ_1`） |
| `decoded_mu` | 解码结果 `μ̂` |
| `threshold` | `q/4` |

---

## 8. 测试清单

| # | 测试 | 验证 |
|---|---|---|
| 1 | Eq. (6.6) | Setup+KeyGen 后 `A y_{i,i} = W_i r_i + p` |
| 2 | Eq. (6.7) | `A y_{i,j} = W_i r_j`（∀j≠i） |
| 3 | Eq. (6.8) | `A y_{0,i} = W_0 r_i`（∀i∈S） |
| 4 | `IsValid` 接受诚实公钥 | 全部 `IsValid=1` |
| 5 | `IsValid` 拒绝篡改公钥 | 改动 `y` 或 `W` → `0` |
| 6 | 授权解密（随机 S、∀i∈S） | 恢复 `μ` |
| 7 | `μ ∈ {0,1}` 两者 | 都能恢复 |
| 8 | `i ∉ S` 被拒绝 | `Decrypt` 返回 0 |
| 9 | **N=4, S={2,4}** | u2/u4 成功；u1/u3 不属于广播集合 |
| 10 | trace 抵消 | `z_centered ≈ μ⌊q/2⌋`，`noise_residual` 小 |
| 11 | 模运算 | 全在 `Z_q`；解码前用 centered representative |
| 12 | Rerandomization 确定性 | 同 `(ξ,S)` → 同 `(W_0, {y_{0,i}})` |

---

## 9. 下一阶段：接入 AES-256-GCM

```
① 随机会话密钥 K（32B）
② AES-256-GCM(K) 加密文件 → body
③ CHW25 DBE 广播保护 K（把 K 的比特逐个/编码后送入 μ）
④ 授权用户 i∈S 恢复 K → 解密 body
⑤ i∉S 无法恢复 K（Decrypt 输出 0，无法还原 K）
```
> 复用 `src/file_crypto/` 的 AES-GCM 层（不改其实现）；DBE 只负责保护 K。**本阶段只做 DBE 核心，不接 UI。**

---

## 10. 来源

- **【论文】** CHW25：`papers/Registered ABE and Adaptively-secure Broadcast Encryption fr.pdf`
  - §6.1 **Construction 6.4**、**Theorem 6.5（Completeness）**、**Theorem 6.6（Correctness）**、Theorem 6.7（Semi-Static Security）
  - §3 **Lemma 3.8（Gadget Trapdoor）**、**Eq. (3.1)（Kronecker 恒等式）**
  - §4 **Lemma 4.5（ℓ-Succinct Trapdoor Sampler）**、**Lemma 4.7（Transform）**、explainable DGS
