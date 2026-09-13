# Matrix Commitment DBE — 规格说明 v1.1

> 阶段：M5 · 对应 Prompt 08/09（Matrix Commitment → DBE）
> 性质：**规格化（Specification），不含代码实现。**
> **v1.1 最高依据**：Wee & Wu, *Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE*, CRYPTO 2025（ePrint **2025/1039**）—— **§3 Matrix Commitments（Lemma 3.8 / Remark 3.9 / Lemma 3.10）、§4 Construction 4.2、Appendix A**。
> 讲义 `papers/论文PPT.pdf` **仅用于解释与可视化**，其直观化公式**不得覆盖**正式构造。

---

## 0. 三层标注约定

- **【WW25 正式算法】**：直接来自 WW25 论文的正式定义/公式（最高优先级）。
- **【讲义直观化】**：来自讲义 PPT 的简化/直观表述，**不构成算法定义**。
- **【课程 TOY 参数】**：课程版为可运行而做的具体化，WW25 未规定。

> **本规格的铁律**：凡与 WW25 冲突处，一律以 WW25 为准；讲义内容只能出现在第 9 节「讲义直观化」中。

---

## 1. v1.0 勘误（为什么必须重写）

v1.0 把**讲义的直观化公式**当成了正式算法，与 WW25 Construction 4.2 存在**结构性冲突**：

| 项 | v1.0（错误，源自讲义直观化） | WW25 正式算法（v1.1） |
|---|---|---|
| base matrix | 只有 `A`，`A` 既当 base 又当 DBE 随机矩阵 | **`B` 是 base matrix**；`A` 是 Setup 中**另外采样**的随机矩阵 |
| `pp_com` | `(A, {v_i}, p)` | **`(B, W, T)`** |
| 用户秘密钥 | `y_i`（low-norm） | **`r_i ∈ {0,1}^m`**（二进制，非 low-norm 高斯） |
| 用户公钥 | `t_i = A·y_i` | **`t_i = B r_i + p − A v_i`** |
| 承诺对象 | 「位置 j 承诺 `p + t_j` 或 `0`」 | **对每个 `i∈S` 承诺稀疏矩阵 `u_i^T ⊗ t_i`** |
| 打开关系 | `C_S v_i = p + t_i − A z_i` | **`C_i v_{i*} = t_{i*} − B z_{i*,i*}`（i=i*）；`−B z_{i,i*}`（i≠i*）** |
| 解密 | 单个 `z_i` | **对全部 `i∈S` 的 local opening `z_{i,i*}` 求和** |
| 比特编码 | `s^T p + b⌊q/2⌋`（直觉正确但缺项） | **`s^T p + e^T d_2 + ⌊q/2⌋·μ`** |

**结论**：v1.0 的 `t_i = A y_i`、单一 `z_i` 解密、「位置直接承诺 `p+t_i`/`0`」**均非**正式算法，v1.1 已从正式章节删除，仅保留在第 9 节作为讲义直观解释。

---

## 2. 关键区分：矩阵 `B` 与矩阵 `A`

**【WW25 正式算法】**

| 矩阵 | 角色 | 维度 | 来源 |
|---|---|---|---|
| **`B`** | **Matrix Commitment 的 base matrix**（承诺关系 `C·V_L = M − B·Z` 中的 `B`） | `Z_q^{n×m}` | `TrapGen` 输出 |
| **`A`** | **DBE 中另外采样的随机矩阵**（用于构造 `t_i = B r_i + p − A v_i`） | `Z_q^{n×m}` | Setup 中 `A ← Z_q^{n×m}` |
| `W` | 承诺参数的一部分 | `Z_q^{2m²n×m}` | Setup 采样 |
| `T` | succinct LWE 实例（维度 `2m²`）的 **trapdoor** | `Z_q^{(2m²+1)m×2m³}` | `SamplePre` 输出 |
| `p` | 公开随机向量 | `Z_q^n` | Setup 采样 `p ← Z_q^n` |

> `B` 与 `A` **是两个独立矩阵**。v1.0 把二者混为一个 `A`，是根本性错误。
> 承诺关系用 `B`；用户公钥构造同时用 `B`（作用于 `r_i`）与 `A`（作用于 `v_i`）。

---

## 3. 六个核心接口【WW25 正式算法】

### 3.1 基础三接口（Lemma 3.8 + Remark 3.9）

**Lemma 3.8** 给出原始三算法 `(Commx, Vermx, Openmx)`，满足
```
C · V_L = M · G_L − B · Z
```
**Remark 3.9** 指出与 Eq.(3.3)（`C·V_L = M − B·Z`）差一个 `G_L^{-1}(I_L)` 因子，于是定义**规范化三接口**：

| 接口 | 输入 | 输出 | 维度 |
|---|---|---|---|
| **`Commat(pp, M)`** | `pp=(B,W,T)`，`M ∈ Z_q^{n×L}` | 承诺 `C` | `Z_q^{n×m}` |
| **`Vermat(pp, 1^L)`** | `pp`，长度参数 `L` | 验证矩阵 `V_L` | `Z_q^{m×L}` |
| **`Openmat(pp, M)`** | `pp`，`M` | 打开矩阵 `Z` | `Z_q^{m×L}` |

满足（对所有 `pp`、`L`、`M`）：
```
Commat(pp, M) · Vermat(pp, 1^L) = M − B · Openmat(pp, M)      （Eq. 3.3）
```
范数界：`‖V_L‖ ≤ O(‖T‖·m⁴ log q)`，`‖Z‖ ≤ O(‖T‖·m⁷ log q log L)`。

**基础算法（Appendix A，`L ≤ 2m` 时）**：
```
Split(pp, L) → (W_L, T_L)   使  [I_{Lm} ⊗ B | W_L]·T_L = I_{Lm} ⊗ G
bits(M) := vec(G^{-1}(M)) ∈ Z_q^{Lm}
J_L ∈ {0,1}^{Lm² × L⌈log q⌉}  固定矩阵，满足 (bits(M) ⊗ G)·J_L = M·G_L

Commx(pp, M)  = (bits(M)^T ⊗ I_n) · W_L                    ∈ Z_q^{n×m}
Vermx(pp, 1^L)= T_L · J_L                                  ∈ Z_q^{m×L⌈log q⌉}
Openmx(pp, M) = (bits(M)^T ⊗ I_m) · T_L · J_L              ∈ Z_q^{m×L⌈log q⌉}
```

### 3.2 稀疏承诺 + 本地打开三接口（Lemma 3.10）

当 `M ∈ Z_q^{n×L}` 稀疏（`L` 可**指数大**，如 `L=2^λ`，但仅 `K = poly` 个非零列）时：

| 接口 | 输入 | 输出 | 复杂度 |
|---|---|---|---|
| **`ComSparsemat(pp, M)`** | `pp`，稀疏 `M ∈ Z_q^{n×L}` | `C = Commat(pp, M)` | `poly(K, m, log q, log L)` |
| **`VerLocalmat(pp, L, i)`** | `pp`，`L`（二进制），列索引 `i∈[L]` | `v_{L,i} ∈ Z_q^m`（`V_L` 第 `i` 列） | `poly(m, log q, log L)` |
| **`OpenLocalmat(pp, M, i)`** | `pp`，稀疏 `M`，索引 `i∈[L]` | `z_i ∈ Z_q^m`（`Z` 第 `i` 列） | `poly(K, m, log q, log L)` |

**核心性质（Appendix A.1）**：
- `ComSparsemat` 用**完全二叉递归树**：`L = 2^k·ℓ`（`ℓ∈[2m]`）时，`C = Commx(pp, [C_0|C_1])`，其中 `C_β = ComSparsemat(pp, M_β)`；`M = 0` 时返回 `0^{n×m}`。
- `VerLocalmat` 递归：`v_{L,i} = V_{2m,lt}·G_m^{-1}(v_{L/2,i})`（`i` 在左半）或 `V_{2m,rt}·G_m^{-1}(v_{L/2,i−…})`（右半）。
- 因此 `V_L`、`Z` 本身指数宽，但**任何单列可在 poly 时间内算出**——这是「无界用户」的关键。

---

## 4. 公开参数【WW25 正式算法】

```
pp_com = (B, W, T)                      （承诺公开参数）
pp     = (N, pp_com, A, p)              （DBE 完整公开参数）
```
其中 `[I_{2m²} ⊗ B | W] · T = I_{2m²} ⊗ G`，`T` 是维度 `2m²` 的 succinct LWE 实例 trapdoor。

> 【讲义直观化】讲义 p31 只画 `pp_com = [p]`「includes `A`, `v_i`」，并**把 base matrix 画成了 `A`**——这是讲义为了幻灯片简洁做的简化，**与正式构造不符**，不得作为算法依据。

---

## 5. Setup / KeyGen / Encrypt / Decrypt【WW25 Construction 4.2】

### 5.1 Setup(1^λ, N) → pp

```
(B, T_B) ← TrapGen(1^n, 1^m, q)
W        ← Z_q^{2m²n × m}
T        ← SamplePre([I_{2m²} ⊗ B | W], [I_{2m²} ⊗ T_B ; 0], I_{2m²} ⊗ G, σ)
A        ← Z_q^{n × m}
p        ← Z_q^n
若 ‖T‖ > √m·σ，则置 T = [I_{2m²} ⊗ T_B ; 0]
pp_com = (B, W, T)
输出 pp = (N, pp_com, A, p)
```
> 这解决了 v1.0 的 `[UNCERTAIN]`：**`p` 的来源 = Setup 中 `p ← Z_q^n` 随机采样**。

### 5.2 KeyGen(pp, i) → (pk_i, sk_i)

```
r_i  ← {0,1}^m                              （二进制秘密钥）
v_i  = VerLocalmat(pp_com, N, i)            （本地导出的验证列，∈ Z_q^m）
t_i  = B·r_i + p − A·v_i   ∈ Z_q^n
pk_i = t_i ,   sk_i = r_i
```
> 这解决了 v1.0 的 `[UNCERTAIN]`：**`v_i` 由 `VerLocalmat` 本地导出**，无需存储整张 `V_N`。

### 5.3 Encrypt(pp, {(i, pk_i)}_{i∈S}, μ) → ct

```
s    ← Z_q^n
e    ← D_{Z,χ}^m                 （离散高斯噪声）
D_1  ← {0,1}^{m×m}
d_2  ← {0,1}^m
若 ‖e‖ > √m·χ，则置 e = 0^m

对每个 i ∈ S:
    C_i = ComSparsemat(pp_com, u_i^T ⊗ t_i)      u_i ∈ {0,1}^N 为第 i 个单位向量
                                                  （u_i^T ⊗ t_i ∈ Z_q^{n×N}，仅第 i 列非零 = t_i）

输出 ct = ( c_1, c_2, c_3 )

  c_1 = s^T B + e^T                              ∈ Z_q^m
  c_2 = s^T ( A + Σ_{i∈S} C_i ) + e^T D_1        ∈ Z_q^m
  c_3 = s^T p + e^T d_2 + ⌊q/2⌋ · μ              ∈ Z_q
```
> **`S` 如何进入承诺**：集合 `S` 通过「对哪些 `i` 构造 `C_i`」进入——`Σ_{i∈S} C_i` 只累加 `S` 中用户的承诺。**不是**「把 `p+t_j` 写进位置 `j`」（那是 v1.0 的讲义直观化表述）。

### 5.4 Decrypt(pp, {(i, pk_i)}_{i∈S}, ct, (i*, sk_{i*})) → μ

```
v_{i*} = VerLocalmat(pp_com, N, i*)
对全部 i ∈ S:  z_{i,i*} = OpenLocalmat(pp_com, u_i^T ⊗ t_i, i*)

μ̃ = c_3 + c_1^T·r_{i*} − c_2^T·v_{i*} − Σ_{i∈S} c_1^T·z_{i,i*}

输出 0  若 −q/4 < μ̃ < q/4
     1  否则
```
> **注意**：解密需要 **`|S|` 个 local opening `z_{i,i*}`**（对每个 `i∈S` 各一个），而非 v1.0 的单个 `z_i`。阈值解码为 **`q/4`**。

---

## 6. 正确性完整推导【WW25 Theorem 4.3】

### 6.1 关键打开关系

由 Remark 3.9 / Lemma 3.10，`C_i = ComSparsemat(pp_com, u_i^T ⊗ t_i)`，而 `u_i^T ⊗ t_i` 仅第 `i` 列非零（值为 `t_i`）。取 `V_N` 的第 `i*` 列 `v_{i*}`：

```
C_i · v_{i*} = t_{i*} − B·z_{i*,i*}     ,  当 i = i*     （该列非零 = t_{i*}）
C_i · v_{i*} = 0 − B·z_{i,i*} = −B·z_{i,i*}  ,  当 i ≠ i*  （该列为零）
```

### 6.2 推导

```
c_2^T·v_{i*} + Σ_{i∈S} c_1^T·z_{i,i*}
  = s^T A v_{i*} + Σ_{i∈S} s^T C_i v_{i*} + Σ_{i∈S} s^T B z_{i,i*} + e^T D_1 v_{i*} + Σ_{i∈S} e^T z_{i,i*}
  = s^T ( A v_{i*} + t_{i*} ) + ẽ_1
  = s^T ( p + B r_{i*} ) + ẽ_1
```
其中 `ẽ_1 = e^T D_1 v_{i*} + Σ_{i∈S} e^T z_{i,i*}`；第三步用了 `A v_{i*} + t_{i*} = A v_{i*} + (B r_{i*} + p − A v_{i*}) = p + B r_{i*}`。

代入 `μ̃`：
```
μ̃ = c_3 + c_1^T r_{i*} − c_2^T v_{i*} − Σ_{i∈S} c_1^T z_{i,i*}
   = (s^T p + e^T d_2 + ⌊q/2⌋μ) + (s^T B + e^T) r_{i*} − [ s^T(p + B r_{i*}) + ẽ_1 ]
   = ⌊q/2⌋·μ + e^T d_2 + e^T r_{i*} − ẽ_1
```

### 6.3 结论

```
μ̃ = ⌊q/2⌋·μ + ẽ ,   其中 ẽ = e^T d_2 + e^T r_{i*} − ẽ_1
当 |ẽ| < q/4 时正确。
```
- `μ = 0` → `μ̃ ≈ ẽ ≈ 0`；`μ = 1` → `μ̃ ≈ ⌊q/2⌋`。阈值 `q/4` 分离二者。✓

### 6.4 噪声界与参数条件

```
|ẽ_1| ≤ N · O(m⁹ χ σ log q log N)
|ẽ|   ≤ N · O(m⁹ χ σ log q log N)

正确性要求:   q > N · O(m⁹ χ σ log q log N)      （Theorem 4.3）
安全性假设:   n ≥ λ,  m ≥ 3n log q,  σ ≥ O(m³ log m)，
              依赖 (2m², σ)-succinct LWE              （Theorem 4.4）
```

---

## 7. 参数与噪声：必须保留 vs 课程 TOY

### 7.1 必须保留（否则广播语义崩溃）

| 要素 | 原因 |
|---|---|
| `B`（base）与 `A`（随机）**分离** | `A v_i + t_i = p + B r_i` 的关键消去 |
| 承诺关系 `C_i v_{i*} = t_{i*}(i=i*) / 0(i≠i*) − B z` | 稀疏承诺的结构性来源 |
| `r_i ∈ {0,1}^m` | 与 `e^T r_i` 一并进入噪声 |
| `p`、`v_i`、`z_{i,i*}` 的**一致性**（同一 `pp_com` 导出） | 否则消去失败 |
| `⌊q/2⌋·μ` + `q/4` 阈值 | 比特编码与纠错 |
| **对全部 `i∈S` 的 local opening** | `Σ c_1^T z_{i,i*}` 缺一项即错 |

### 7.2 课程 TOY 参数（可简化）

| 要素 | 课程处理 | 后果 |
|---|---|---|
| `n, m, q, N` | 极小（如 `n=4, m=8, q=97`，`N=8`） | 规模小，**可被实际攻破** |
| `TrapGen / SamplePre` | 简化为玩具实现 | 必须**仍是真 trapdoor**，否则承诺非真 |
| `D_{Z,χ}` 高斯噪声 | 取小 `χ` 或象征性噪声 | 正确性可成立，**安全证明失效** |
| succinct LWE 假设 | **直接假设**，不做归约 | 未验证假设 |
| `G, G^{-1}, J_L, Split` | 可硬编码小 gadget | 机制保持 |
| `L = 2^λ`（指数） | 取小 `L = N` | 失去「无界」卖点，但保留稀疏承诺机制 |

### 7.3 声明

> **课程版 = TOY / 教学简化**：用于演示 Matrix Commitment DBE 的**代数机制与广播语义**；**不提供**真实安全性，不声称工业级，不声称忠实实现 WW25 参数。

---

## 8. 【讲义直观化】章节（仅解释，非算法）

> 以下内容来自讲义 p26–38，**只用于建立直觉**，与正式算法冲突处以第 5 节为准。

- 【讲义 p27–29】「每个用户采样 dual-Regev 密钥对并公开公钥」——正式版中公钥是 `t_i = B r_i + p − A v_i`，秘密钥是二进制 `r_i`（**不是** dual-Regev 的 low-norm `y_i`）。
- 【讲义 p34】「commit to `p + t_j` at position `j` when `j ∈ S` and `0` otherwise」——正式版是**对每个 `i∈S` 承诺稀疏矩阵 `u_i^T ⊗ t_i`**；讲义的 `p + t_j` 是消去后的**净效果**的直观说法。
- 【讲义 p36】「`C_S v_i = p + t_i − A z_i`」——正式版是 `C_i v_{i*} = t_{i*} − B z_{i*,i*}`（`i=i*`）。讲义把 `B` 写成 `A`、并省略了 `Σ` 与 `i≠i*` 分支。
- 【讲义 p38】「only user `i` can compute `s^T t_i ≈ s^T A y_i`」——正式版是 `s^T(p + B r_i)`，用二进制 `r_i` 而非 `y_i`。

**v1.0 的错误正是把上述四条的直观表述当成了算法定义。**

---

## 9. 课程 TOY 参数化方案【课程 TOY 参数】

```
n = 4, m = 8, q = 97, N = 8, L = N = 8, χ = 1, σ = 小值
TrapGen / SamplePre / G / G^{-1} / J_L / Split → 玩具实现（保持数学关系）
```
关键：即使规模极小，**六个接口的输入输出与维度关系、以及第 6 节推导链条必须保持形式一致**，否则就不是 Matrix Commitment DBE。

---

## 10. Python 模块结构（建议）

```
src/mc_dbe/
├── __init__.py
├── params.py        # (n,m,q,N,L,χ,σ,⌊q/2⌋)；标注 TOY
├── lattice.py       # Z_q 运算、G、G^{-1}、bits()、Split()
├── trapdoor.py      # TrapGen / SamplePre（玩具）
├── commit.py        # Commat / Vermat / Openmat
├── sparse.py        # ComSparsemat / VerLocalmat / OpenLocalmat（递归树）
├── setup.py         # Setup(1^λ,N) → pp=(N, pp_com, A, p)
├── keygen.py        # KeyGen(pp,i) → (t_i, r_i)
├── encrypt.py       # Encrypt(pp, {(i,t_i)}_{i∈S}, μ) → (c_1,c_2,c_3)
├── decrypt.py       # Decrypt(pp, ..., (i*,r_{i*})) → μ
└── serialization.py
```
> 与 `src/cs/`、`src/sd/` **完全独立**（DBE 无树）；不修改任何现有模块。

---

## 11. 测试清单【课程 TOY 参数】

| # | 测试 | 验证内容 |
|---|---|---|
| 1 | `Commat/Vermat/Openmat` 代数正确性 | `C·V_L = M − B·Z` 成立 |
| 2 | `Split` 正确性 | `[I_{Lm}⊗B \| W_L]·T_L = I_{Lm}⊗G` |
| 3 | `bits/G^{-1}` 正确性 | `(bits(M)⊗G)·J_L = M·G_L` |
| 4 | **`ComSparsemat` 稀疏承诺** | 与稠密 `Commat` 在小 `L` 上一致；零矩阵 → `0^{n×m}` |
| 5 | **`VerLocalmat` 本地列** | 与 `Vermat` 的第 `i` 列逐项一致 |
| 6 | **`OpenLocalmat` 本地列** | 与 `Openmat` 的第 `i` 列逐项一致 |
| 7 | Setup 一致性 | `[I_{2m²}⊗B\|W]·T = I_{2m²}⊗G`；`‖T‖ ≤ √m σ` |
| 8 | KeyGen 结构 | `t_i = B r_i + p − A v_i`；`r_i ∈ {0,1}^m` |
| 9 | Encrypt 形状 | `c_1∈Z_q^m, c_2∈Z_q^m, c_3∈Z_q` |
| 10 | **授权用户正确性** | 对所有 `μ∈{0,1}`、`i*∈S`：`Decrypt = μ` |
| 11 | **非接收者解密失败** | `i* ∉ S` 时 `μ̃` 落在错误区间 / 无法恢复 |
| 12 | 多集合 | `S=∅`、`S=全用户`、随机 `S` |
| 13 | **tamper / shape** | 篡改 `c_1/c_2/c_3` 任一分量 → 解码错误；形状校验 |
| 14 | 序列化 | `ct` round-trip |

> **注**：v1.0 的「单元测试验证 commitment binding 安全性」已删除——安全性依赖 succinct LWE 假设，**不能**由单元测试证明。只测**代数正确性**。

---

## 12. N=4 手算示例 → 改为「待真实执行导出」

**v1.0 的标量手算例子已删除**（它混淆了正式构造，且标量下「一致 opening」未必存在）。

**v1.1 方案**：N=4 的 trace **待 `src/mc_dbe/` 实现后，由真实 toy matrix execution 导出**，包括：
```
- pp_com = (B, W, T) 的实际值
- 各用户的 (r_i, v_i, t_i)
- 加密时的 (s, e, D_1, d_2) 与 (c_1, c_2, c_3)
- 解密时的 v_{i*}、{z_{i,i*}}_{i∈S}、μ̃ 及阈值判定
```
> 在实现完成前，**不提供任何手工数值示例**，以免再次引入与正式构造不符的直观化数字。

---

## 13. 禁止的伪实现

1. ❌ 用 `A` 同时充当 base matrix 与 DBE 随机矩阵（v1.0 的错误）。
2. ❌ 用哈希（SHA-256/Merkle）替代 `Commat/ComSparsemat`。
3. ❌ 用 AES 包装 / 逐用户单独加密 `μ`。
4. ❌ 省略 `Σ_{i∈S} C_i`，或只用单个 `z_i` 解密。
5. ❌ 去掉 `B` 或 `A v_i` 项。
6. ❌ 让 `i* ∉ S` 也能正确恢复。

---

## 14. 剩余 `[UNCERTAIN]`

1. **`t_i` 的维度在论文内部不一致**：KeyGen 写 `t_i ∈ Z_q^n`，而 Encrypt 与 Theorem 4.4 证明中写作 `t_i ∈ Z_q^{n×m}`。由代数 `B r_i + p − A v_i`（`B` 为 `n×m`、`r_i` 为 `m` 维）推断应为 `Z_q^n`，`n×m` 疑为论文笔误。**待作者/正式版本确认**。
2. **`OpenLocalmat` 的完整递归式**：Appendix A.1 给出了 `ComSparsemat` 与 `VerLocalmx` 的完整递归，`OpenLocalmat` 的本地递归式在文本抽取中未完整取得（仅确认其存在与复杂度 `poly(K,m,log q,log L)`）。实现前需补读 Appendix A.1 后半。
3. **`D_{Z,χ}` 的精确分布与 `χ` 取值**：WW25 未在正文给出具体采样器实现细节。
4. **`TrapGen` / `SamplePre` 的确切算法**：论文引用 [MP12] 等，未在本文展开；课程 TOY 需自行选择玩具 trapdoor。
5. **`G`、`G^{-1}`、`J_L` 的具体构造**：`J_L` 引用 `[Wee25, Lemma 4]`；`G^{-1}` 的确定性采样需 [MP12] gadget 细节。
6. **`μ̃` 的阈值边界**：论文写 `−q/4 < μ̃ < q/4` 输出 0（边界取闭/开未明确），实现时需与 `⌊q/2⌋` 的舍入配合确认。

---

## 15. 来源

- 【WW25 正式算法】Wee & Wu, *Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE*, CRYPTO 2025 — ePrint **2025/1039**：§3.2（Lemma 3.8 / Remark 3.9 / Lemma 3.10）、§4（Definition 4.1 / **Construction 4.2** / Theorem 4.3 / Theorem 4.4）、**Appendix A**（`Split`、`Commx/Vermx/Openmx`、`ComSparsemat`、`VerLocalmx`）。
- 【讲义直观化】`papers/论文PPT.pdf` p23–38（**仅解释**，不作为算法依据）。
- 【承诺原语】Wee, *Succinct vector, polynomial, and functional commitments from lattices*, EUROCRYPT 2023（`[Wee25]`）。
