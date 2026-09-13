# 基于 Matrix Commitment 的广播加密：课程理论说明（v2.0）

> 文档定位：课程设计**原理教学**文档（配套 `docs/matrix-commitment-dbe-spec.md` v1.1）
> 目标：让项目成员**真正理解** Matrix Commitment DBE 的机制与信息流
> 依据优先级：**老师讲义 `论文PPT.pdf` 的教学逻辑优先**；WW25 正式论文（ePrint 2025/1039）补充出处与 formal construction
> 性质：原理讲解，**不含代码**

---

## 0. 三层标注约定（全文贯穿）

本文每一处内容都归属以下三层之一，避免符号混用：

| 标注 | 含义 | 用途 |
|---|---|---|
| **【老师讲义】** | `papers/论文PPT.pdf` 的教学化记号与直观构造 | **理解思想**（本文主线） |
| **【WW25 正式构造】** | Wee & Wu, *Unbounded DBE and Registered ABE from Succinct LWE*, CRYPTO 2025, **Construction 4.2** | **精确依据**（正式定义） |
| **【我们的课程实现选择】** | 课程版为可运行所做的具体化/简化 | **落地方案** |

> ⚠️ **关键提醒**：讲义为教学做了简化，其公式与 WW25 正式构造**有结构性差异**（第 14 节逐项对照）。先读讲义建直觉，再看 WW25 学正式版。

---

## 1. 课程目标与广播语义

本课程第二阶段目标：实现**基于 Matrix Commitment 的广播加密**。

核心语义（所有用户收到**同一份密文**，而非逐用户分别生成）：

\[
i\in S \Rightarrow \text{用户 }i\text{ 可解密}
\qquad
i\notin S \Rightarrow \text{用户 }i\text{ 不能解密}
\]

其中 \(S\) 是本次广播的授权用户集合。**"同一份密文"是本方案的灵魂**——不是给每人各发一份。

---

## 2. 密码学基础：对称 / 非对称 / 属性

### 2.1 对称加密【老师讲义 / 通用背景】

加密与解密用同一密钥 \(K\)：
\[
C=\mathrm{AES\text{-}GCM.Enc}(K,M),\qquad M=\mathrm{AES\text{-}GCM.Dec}(K,C)
\]
- **优点**：快，适合图片/视频等大文件。
- **缺点**：双方必须事先安全共享 \(K\) → **密钥分发问题**。

### 2.2 非对称密码（公钥密码）【老师讲义 p32】

每个用户有一对密钥：
\[
(sk_i,\;pk_i)
\]
- \(sk_i\)（私钥）：**只自己保存**；
- \(pk_i\)（公钥）：**公开发布**。

**【老师讲义】教学化 DBE 表示**：
\[
\boxed{\;sk_i=y_i,\qquad pk_i=t_i=A\,y_i\;}
\]
其中 \(A\) 是公开矩阵，\(y_i\) 是 **low-norm** 短向量。

### 2.3 私钥本地生成、公钥公开发布【老师讲义 p3–8】

DBE 的关键特性是**没有中央权威**（trustless）：
\[
\text{本地随机生成 }y_i \;\rightarrow\; t_i=A y_i \;\rightarrow\; \text{公开 }t_i
\]
- 私钥**永不传输**，中心也不知道；
- 公钥贴到**公开目录**，加密者取用。

> 【我们的课程实现选择】课程版"公开目录"就是内存字典 `{i: t_i}`。

### 2.4 为什么私钥要 low-norm【老师讲义 p24/p32】

**范数**衡量向量大小，如 \(\|(3,4)\|_2=5\)。low-norm = 坐标小、整体短。

两个作用：
1. **安全性**：知道 \(A\) 与 \(t_i\) 后，很难找到**足够短**的 \(y\) 使 \(Ay=t_i\pmod q\)（格困难问题 / SIS）；
2. **正确性**：噪声乘以短向量后仍小，不破坏解密。

> 关键区分：不是"找不到**任何**解"，而是"很难找到**足够短、能用于正确解密**的解"。

---

## 3. 一次性随机向量 \(s\) 与 LWE 噪声

### 3.1 \(s\) 是什么【老师讲义 p33】

\(s\) 是**发送者每次加密时新鲜生成的一次性随机向量**：
\[
s\leftarrow \mathbb Z_q^n
\]
- 它不是任何用户的长期私钥；
- 用完即弃；\(s^T\) 只是转置，用于维度匹配。

### 3.2 为什么公开 \(s^TA+e^T\) 而不公开 \(s\)【老师讲义 p25/p35】

后续会出现掩码项 \(s^Tp\)。而 \(p\) **是公开参数**，所以：
\[
\text{若公开 }s \;\Rightarrow\; \text{任何人可算 }s^Tp \;\Rightarrow\; \text{掩码被剥离，消息暴露}\;\;✗
\]

因此系统只公开 **LWE 型量**（含小噪声 \(e\)）：
\[
\boxed{\;c_A=s^TA+e^T\;}
\]
由 **LWE 假设**，给定公开的 \(A\)，\(c_A\) 与**均匀随机**不可区分，故**不泄露 \(s\)**。

> 一句话：**公开"带噪声的线性组合"，既能让人完成消去，又不足以反推 \(s\)**。

### 3.3 用户怎样用私钥得到 \(s^Tt_i\)【老师讲义 p38】

\[
c_A y_i=(s^TA+e^T)y_i=s^TAy_i+e^Ty_i=s^Tt_i+e^Ty_i
\]
因 \(e\) 与 \(y_i\) 都短：
\[
\boxed{\;c_A y_i\approx s^Tt_i\;}
\]
用户得到的**不是 \(s^T\) 本身**，而是自己需要的线性量 \(s^Tt_i\)——这样才能把它从等式里消掉。

---

## 4. Matrix Commitment 原语【老师讲义 p23–25】

### 4.1 接口

\[
\operatorname{Com}(pp,\;m_1,\ldots,m_L)\;\rightarrow\;(C,\;z_1,\ldots,z_L)
\]

- 讲义称 **"vector commitment to vectors"**：**对一组向量做承诺**；
- \(C\) 称 **commitment（承诺）**；\(z_1..z_L\) 称 **openings（打开）**；
- 讲义注明 "can be deterministic or randomized"。

### 4.2 核心 opening relation

\[
\boxed{\;C\,v_i=m_i-A\,z_i\;}
\qquad\Longleftrightarrow\qquad
\boxed{\;C\,v_i+A\,z_i=m_i\;}
\]

### 4.3 各符号含义【老师讲义 p24】

| 符号 | 含义 | 性质 |
|---|---|---|
| \(i\) | **位置**（第 \(i\) 个槽位 ↔ 第 \(i\) 个用户） | \(i\in[L]\) |
| \(m_i\) | 位置 \(i\) 上**被承诺的消息向量** | 由广播集合 \(S\) 决定 |
| \(v_i\) | 位置 \(i\) 的**验证向量** | **public**；low-norm |
| \(z_i\) | 位置 \(i\) 的**打开 opening** | **low-norm** |
| \(C\) | **承诺矩阵**（短） | public |

> 讲义 p24 原话：「**pp describes `A` and `v_i` for `i ∈ [L]`**」——\(A\) 与全部 \(v_i\) 都在公开参数里。

### 4.4 opening 语义与安全性直觉

- **左边** \(Cv_i+Az_i\)：\(C,v_i,A\) 都公开，\(z_i\) 是打开 → **任何人可验算**；
- **右边** \(m_i\)：位置 \(i\) 真正承诺的内容；
- 想**伪造** \(z_i'\) 让位置 \(i\) 打开成别的值，需找 \(A z_i'=Cv_i-m_i'\) 的 **low-norm 解** → **格困难问题（SIS）**。

**这就是 "Matrix Commitment" 的由来**：承诺对象是**矩阵/向量**，安全性来自**格**（\(A\)、\(z_i\) 的 low-norm）。

### 4.5 一个 \(C\)，多个位置【老师讲义】

\[
C v_1+Az_1=m_1,\quad C v_2+Az_2=m_2,\quad\ldots,\quad C v_L+Az_L=m_L
\]
\[
\boxed{\text{同一个 }C\text{ 被所有位置共享}}
\]
"短" 指表示规模比完整保存 \(m_1..m_L\) 更紧凑——是**简洁承诺**，不是 ZIP 压缩。

---

## 5. 广播集合 \(S\) 如何编码进承诺（N=4, S={2,4}）

**【老师讲义 p34】** 这是"承诺"变成"广播加密"的关键一步。

### 5.1 编码规则
\[
m_j=
\begin{cases}
p+t_j, & j\in S\\
0,     & j\notin S
\end{cases}
\]

### 5.2 取 \(N=4,\;S=\{2,4\}\)（叶子示例）

| 位置 \(j\) | \(j\in S\)？ | 被承诺值 \(m_j\) |
|---|---|---|
| 1 | ✗ | \(m_1=0\) |
| 2 | ✓ | \(m_2=p+t_2\) |
| 3 | ✗ | \(m_3=0\) |
| 4 | ✓ | \(m_4=p+t_4\) |

\[
(m_1,m_2,m_3,m_4)=(0,\;p+t_2,\;0,\;p+t_4)
\]
\[
C_S=\operatorname{Com}(pp,\;0,\;p+t_2,\;0,\;p+t_4)
\]

### 5.3 理解要点
- **\(S\) 只影响"哪些位置写入 \(p+t_j\)"**：属于 \(S\) 写 \(p+t_j\)，否则写 \(0\)；
- 因此 \(C_S\) 是一份「**把 \(p\) 悄悄分发给 \(S\) 中用户**」的代数凭证；
- **\(S\) 不进入 \(pp\)，也不进入用户密钥**——只体现在 \(C_S\) 里。

### 5.4 打开关系在 S={2,4} 下的两副面孔
\[
C_S v_i=p+t_i-A z_i \quad (i\in\{2,4\})
\]
\[
C_S v_i=0-A z_i=-A z_i \quad (i\in\{1,3\})
\]
**这两行的差别 = 授权/非授权的分水岭。**

> 【我们的课程实现选择】上表是**概念演示**；真实 \(m_j,p,t_j\) 都是**向量**（\(\mathbb Z_q^n\)），\(C_S\) 是**矩阵**。完整数值 trace 待 `src/mc_dbe/` 实现后由真实 toy 执行导出。

---

## 6. 授权用户为什么能解密（完整推导）

**【老师讲义 p36–38】** 以 \(u_2\in S\) 为例。

### 步骤 1：打开关系
\[
C_S v_2=p+t_2-A z_2
\]

### 步骤 2：两边左乘 \(s^T\)
\[
s^T C_S v_2=s^Tp+s^Tt_2-s^TA z_2
\]

### 步骤 3：移项
\[
\boxed{\;s^T C_S v_2+s^TA z_2=s^Tp+s^Tt_2\;}
\]
- 左边：**全部公开可算**（讲义标注 "public"）；
- 右边：**"dual-Regev ciphertext under \(pk_2\)"**（形如用 \(t_2\) 加密 \(s^Tp\) 的密文）。

### 步骤 4：用私钥 \(y_2\) 消去 \(s^Tt_2\)
因 \(t_2=Ay_2\)，由第 3.3 节：
\[
c_A y_2\approx s^Tt_2
\]
于是（记 \(c_C\approx s^TC_S,\;c_A\approx s^TA\)）：
\[
\boxed{\;c_C v_2+c_A z_2-c_A y_2\approx s^Tp\;}
\]

**掩码 \(s^Tp\) 被恢复！**

> 讲义 p38 气泡原话：**"only user \(i\) can compute \(s^Tt_i\approx s^TAy_i\)"**——因为只有用户 \(i\) 有 \(y_i\)。

### 步骤 5：从 \(s^Tp\) 恢复消息 bit
\[
c_b\approx s^Tp+b\left\lfloor \tfrac q2\right\rfloor
\quad\Rightarrow\quad
c_b-s^Tp\approx b\left\lfloor \tfrac q2\right\rfloor
\]
- 结果接近 \(0\) → \(b=0\)；接近 \(q/2\) → \(b=1\)；
- 有噪声，故用**阈值/舍入**判定（正式版阈值 \(q/4\)）。

---

## 7. 非授权用户为什么即使有合法私钥也不能解密

**【老师讲义】** 设 \(u_1\notin S\)（\(S=\{2,4\}\)）。

### 7.1 他面对的打开关系
位置 1 承诺的是 \(0\)：
\[
C_S v_1=-Az_1
\quad\Rightarrow\quad
s^TC_S v_1+s^TAz_1=0
\]

### 7.2 他期望 vs 他得到
- **期望**（才能解密）：\(s^Tp+s^Tt_1\)
- **实际得到**：\(0\)

即使 \(u_1\) 有自己的合法私钥 \(y_1\)，最多算出 \(c_Ay_1\approx s^Tt_1\)——但**承诺一侧没有产生 \(s^Tp+s^Tt_1\)**，所以凑不出 \(s^Tp\)。

### 7.3 他能否伪造打开？
想让位置 1 打开成 \(p+t_1\) → 需 \(Az_1'=C_Sv_1-(p+t_1)\) 的 low-norm 解 → **格困难问题**；且 \(C_S\) 已承诺死在 \(0\)（**binding**）。

### 7.4 结论
\[
\boxed{\text{拥有合法私钥}\;\neq\;\text{属于本次广播集合}}
\]

**本质**：授权与否**不取决于"有没有私钥"**，而取决于"**自己那个位置承诺的是 \(p+t_i\) 还是 \(0\)**"。\(S\) 通过承诺值的选择，把"能否解密"**编码进了代数结构**。

---

## 8. 教学化算法全过程信息流（一张图）

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ① Setup            pp = (A, p, v_1 ... v_L)                                 │
│    · A  公开矩阵（讲义版即 base；WW25 版另有 B）                             │
│    · p  公开随机向量（掩码的"载体"）                                          │
│    · v_i 各位置验证向量（public, low-norm）                                  │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ ② KeyGen（用户 i 本地）          ← 私钥本地生成，中心不知                     │
│    y_i ← 随机（low-norm）        （WW25: r_i ← {0,1}^m）                     │
│    t_i  = A · y_i                （WW25: t_i = B r_i + p − A v_i）           │
│    pk_i = t_i → 公开目录 ;  sk_i = y_i → 自留                                │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ ③ Encrypt（向 S 广播 b）          ← S 在这里"编码"进承诺                     │
│    s ← 随机 ;  e, D1, d2 ← 噪声                                             │
│    对每个位置 j:  m_j = p + t_j (j∈S) ;  0 (j∉S)                            │
│    C_S = Com(pp, m_1 ... m_L) ;  得打开 z_1 ... z_L                         │
│    ct = ( c_A = s^T A + e^T ,  c_C = s^T C_S ,  c_b = s^T p + e^T d_2 + ⌊q/2⌋·b ) │
│              ↑公开可算           ↑公开可算              ↑掩码 b             │
└────────────────────────────────────────────────────────────────────────────┘
                        ┌───────────┴───────────┐
                        ▼                       ▼
        ┌────────────────────────────┐  ┌──────────────────────────────────┐
        │ ④ Decrypt（授权 i ∈ S）     │  │ ④' 尝试解密（非授权 j ∉ S）       │
        │  取自己的打开 z_i           │  │  位置 j 承诺 0                   │
        │  c_C v_i + c_A z_i          │  │  → C_S v_j + A z_j = 0           │
        │    ≈ s^T p + s^T t_i        │  │  ≠ s^T p + s^T t_j               │
        │  用 y_i 消去 s^T t_i:       │  │  → 得不到 s^T p                  │
        │    s^T p = 上式 − c_A y_i   │  │  → 无法剥离掩码                  │
        │  从 c_b 减去 s^T p:         │  │  → 无法恢复 b      ✗             │
        │    b⌊q/2⌋ → 阈值判定  ✓     │  │  也不能伪造打开（binding/SIS）    │
        └────────────────────────────┘  └──────────────────────────────────┘
```

### 一句话信息流
```
KeyGen:  私钥 y_i →(A)→ 公钥 t_i →(承诺)→ 位置值 p+t_i
Encrypt: 集合 S →(选位置)→ C_S →(乘 s)→ 密文 ct
Decrypt: ct + 打开 z_i →(消去)→ s^Tp（掩码）→(减)→ b
拒绝:    j∉S → 位置值是 0 → 消不出 s^Tp → 拿不到 b
```

---

## 9. \(z_i\) 究竟是什么？要不要公开？【老师讲义 p23】

- \(z_i\) 是 Matrix Commitment 的 **opening**，**不是用户私钥**。
- 要分清两件事：
  1. 是否像私钥一样**永久保密**？（不是——它是承诺的打开凭证）
  2. 是否应把全部 \(z_1..z_L\) **随密文发送**？（**不应**）
- Matrix Commitment 的重点是**建立可验证、简洁的代数承诺关系**，而非隐藏 \(m_i\)。
- 若发送全部 openings，通信量随用户数增长 → **破坏 succinct/unbounded 目标**。

---

## 10. \(z_i\) 的两副面孔：讲义抽象 vs WW25 `OpenLocalmat`

**【老师讲义 p23/p38】 vs 【WW25 正式构造 Lemma 3.10】**

| 维度 | 【老师讲义】抽象 | 【WW25 正式构造】 |
|---|---|---|
| 符号 | \(z_i\) | \(z_{i,i^*}=\operatorname{OpenLocal}_{mat}(pp_{com},\,u_i^T\otimes t_i,\,i^*)\) |
| 含义 | 位置 \(i\) 的打开 | 承诺 \(C_i\) 的打开矩阵 \(Z_i\) 的**第 \(i^*\) 列** |
| 需要几个 | **1 个** | **\(\lvert S\rvert\) 个**（每个 \(i\in S\) 一个） |
| 解密用法 | 单点代入 | **求和** \(\sum_{i\in S}c_1^T z_{i,i^*}\) |
| 底层承诺 | 对"每位置一个值"的承诺 | 对**每个 \(i\) 各承诺一个稀疏矩阵** \(u_i^T\otimes t_i\) |
| 宽度 | 与 \(L\) 同阶 | \(Z\) **指数宽**（\(L=2^\lambda\)）→ 必须**本地算单列** |
| 为何 local | 讲义未涉及 | 无界用户下 \(Z\) 无法整体存储，须 \(poly(m,\log q,\log L)\) 算一列 |

**要点**：
- 讲义的 \(z_i\) 是**教学简化**（"对位置值的承诺 + 一个打开"）；
- WW25 的 `OpenLocalmat` 是**工程必需**——支持无界用户（\(L\) 指数大）时，\(V_L\)、\(Z\) 都指数宽，只能**按需算一列**；
- 讲义 p34 原话 **"can efficiently commit to exponential number of vectors if poly many are nonzero"** 正是点出"稀疏 + 本地访问"这一能力。

---

## 11. 老师讲义与 WW25 Construction 4.2 的对照

**【老师讲义 p31–38】** 的标题就是 **"DBE For Unbounded Users [WW25]"**——**它讲的就是 WW25**，但为教学做了简化。

| 项 | 【老师讲义】 | 【WW25 正式构造】 |
|---|---|---|
| base matrix | 只出现 \(A\) | **\(B\)（base）+ \(A\)（另采样随机）**，二者分离 |
| 公开参数 | \(pp_{com}\) 含 \(A,v_i\) | **\(pp_{com}=(B,W,T)\)**；\(pp=(N,pp_{com},A,p)\) |
| 秘密钥 | \(y_i\)（low-norm） | **\(r_i\in\{0,1\}^m\)** |
| 公钥 | \(t_i=Ay_i\) | **\(t_i=Br_i+p-Av_i\)** |
| 承诺对象 | 位置 \(j\) 承诺 \(p+t_j\) 或 \(0\) | 对每个 \(i\in S\) 承诺**稀疏矩阵** \(u_i^T\otimes t_i\) |
| 打开关系 | \(C_Sv_i=p+t_i-Az_i\) | \(C_iv_{i^*}=t_{i^*}-Bz_{i^*,i^*}\)(\(i=i^*\))／\(-Bz_{i,i^*}\)(\(i\neq i^*\)) |
| 打开数量 | 1 个 \(z_i\) | **\(\lvert S\rvert\) 个** \(z_{i,i^*}\) |
| 密文 | \((c_A,c_C,c_b)\)，噪声省略 | \((s^TB+e^T,\;s^T(A+\sum C_i)+e^TD_1,\;s^Tp+e^Td_2+\lfloor q/2\rfloor\mu)\) |
| 解密 | 单打开代入 | 对全部 \(i\in S\) 求和，阈值 \(q/4\) |
| 噪声 | 全部省略（"Noise omitted"） | 显式 \(e,D_1,d_2\) + 噪声界 |

**为什么讲义可以这样简化**：
- 教学上，\(t_i=Ay_i\) + "位置承诺 \(p+t_i\)" 更直观地表达「**用户把公钥塞进位置，再从中取回掩码**」；
- 正式上，WW25 需要：(1) 分离 \(B/A\) 配合 succinct LWE 的 trapdoor；(2) 二进制 \(r_i\) 便于噪声分析；(3) 稀疏承诺支持无界 \(L\)；(4) \(\lvert S\rvert\) 个 local opening 完成求和消去；
- **两者表达同一思想，但代数细节不同**——这正是实现时必须明确"采用哪一层"的原因。

---

## 12. 【我们的课程实现选择】

基于上述对照，课程版采用以下策略（**待最终确认**）：

1. **以讲义教学层为主线实现**：真正使用矩阵/向量运算、真正 low-norm 私钥、真正 LWE 型噪声、真正实现 Matrix Commitment / opening relation；
2. **保留广播语义**：\(i\in S\Rightarrow\) 能解；\(i\notin S\Rightarrow\) 不能解；所有用户收**同一份密文**；
3. **明确标注为 TOY**：使用小规模参数（如 \(n,m,q,N\) 取极小值），**不声明工业级安全性**；
4. **不冒充正式构造**：代码与文档中明确区分"讲义教学层"与"WW25 正式层"；
5. **实现前的待确认项**（见第 18 节）。

> 若后续决定改为**忠实实现 WW25 Construction 4.2**，则需补齐 `TrapGen / SamplePre / G / G^{-1} / J_L / Split / ComSparse` 等重型组件，成本显著更高。**此选择需明确记录在 spec 中。**

---

## 13. 安全性声明与 TOY 参数边界

### 13.1 安全性声明（如实）
> 本课程版 Matrix Commitment DBE 是 **TOY / 教学简化**实现，用于演示**代数机制与广播语义**；**不提供**真实密码学安全性，**不声称**工业级，**不声称**忠实实现 WW25 参数。

### 13.2 理论上的安全性来源
【WW25 Theorem 4.4】安全性建立在 **\(\ell\)-succinct LWE** 假设之上：
\[
n\ge\lambda,\quad m\ge 3n\log q,\quad \sigma\ge O(m^3\log m)
\]
课程版**不实现、也不验证**该假设，只作理论背景。

### 13.3 简化对"功能"与"安全"的影响

| 简化 | 影响广播语义？ | 影响安全性？ |
|---|---|---|
| 极小 \(n,m,q,N\) | ✅ 不影响（机制保持） | ✅ 变 toy（可被攻破） |
| 小/象征性噪声 | ✅ 不影响正确性 | ✅ 安全证明失效 |
| 玩具 trapdoor | ✅ 不影响（若仍是真 trapdoor） | ⚠️ 取决于是否真 trapdoor |
| 不做 succinct LWE 归约 | ✅ 不影响（假设照用） | ✅ 变 toy（未验证） |
| \(L\) 取小（失去"无界"） | ✅ 不影响（保留稀疏承诺机制） | ⚠️ 失去无界卖点 |

> **判据**：只要"**承诺 → 打开 → 消去 → 取回掩码**"这条代数链完整，**广播语义**就成立；简化只削弱**安全强度**，不破坏**功能正确性**。

### 13.4 明令禁止的"伪实现"
1. ❌ 用哈希（SHA-256 / Merkle）替代 Matrix Commitment；
2. ❌ 用普通 AES 包装，或**逐用户单独加密**会话密钥；
3. ❌ 去掉格结构（low-norm / \(A\) / \(z_i\)），只留一个 \(C\)；
4. ❌ 把 \(b\) 明文放进密文；
5. ❌ 让 \(i\notin S\) 也能恢复。

---

## 14. 与规格文档的分工

| 文档 | 定位 |
|---|---|
| **本文（theory）** | **为什么这样设计**——教学直觉、信息流、三层对照 |
| `docs/matrix-commitment-dbe-spec.md`（v1.1） | **精确是什么**——WW25 正式公式、六个接口、TOY 参数、测试清单 |

**建议阅读顺序**：本文（懂思想）→ spec v1.1（看正式定义）→ 实现。

---

## 15. 媒体文件如何接入（混合加密）

Matrix Commitment DBE 适合保护**小消息 / 会话密钥**，**不应**直接加密大型视频。

最终工程采用**混合加密**：
```
① 随机生成会话密钥 K
② AES-256-GCM 加密图片/视频
③ Matrix Commitment DBE 广播保护 K
④ 授权用户恢复 K → 解密媒体
⑤ 非授权用户无法恢复 K → 无法解密媒体
```
\[
\boxed{\text{Matrix Commitment DBE}+\text{AES-GCM}}
\]

---

## 16. 动态可视化建议（后续 UI）

重点展示**过程**，而非只显示成功/失败：

1. **Setup**：展示 \(pp\)、\(A\)、\(p\)；
2. **KeyGen**：动画展示 \(A y_i\rightarrow t_i\)；私钥仅显示 fingerprint（**不显示明文**）；
3. **Select Broadcast Set**：选择 \(S=\{u_2,u_4\}\)；
4. **Fill Commitment Slots**：动态显示 \([0,\;p+t_2,\;0,\;p+t_4]\)；
5. **Matrix Commitment**：多槽位"压缩"为一个 \(C_S\)；
6. **Encrypt**：生成 \(s,e\)，展示 \(c_A,c_C,c_b\)；
7. **Authorized Decrypt**：展示 \(C_Sv_2+Az_2=p+t_2\) → \(s^Tp+s^Tt_2\) → 用 \(y_2\) 消去 → \(s^Tp\) → \(b\)；
8. **Unauthorized Decrypt**：槽位为 \(0\)，代数链无法生成 \(s^Tp+s^Tt_i\)，显示失败原因；
9. **Media Recovery**：授权用户恢复会话密钥，媒体从 ciphertext 还原。

---

## 17. 一句话讲给老师听

> 我们用 Matrix Commitment 把本次广播集合编码进一个短的 commitment：集合内用户的位置承诺 \(p+t_i\)，集合外承诺 \(0\)。授权用户利用自己的 verification vector \(v_i\)、opening \(z_i\) 和低范数私钥 \(y_i\)，把公共的 commitment 密文转化为与自身公钥相关的 LWE 密文，通过代数消去恢复公共掩码 \(s^Tp\)，从而解出广播消息；集合外用户的位置没有 \(p+t_i\)，因此**即使拥有自己的合法私钥也无法恢复这个掩码**。

---

## 18. 实现前仍需确认的问题

进入 `src/mc_dbe/` 代码阶段前，需最终确认：

1. 课程版 `Com` 如何具体构造 \(C\) 与 opening？
2. 是否实现 `OpenLocalmat`，还是先采用**有限用户的显式 opening**？
3. low-norm 私钥 \(y_i\) 的具体采样分布？
4. 噪声 \(e\) 的采样方式与参数？
5. toy 参数 \(n,m,q\) 取值？
6. bit-level DBE 如何扩展为**会话密钥 \(K\)**？
7. **哪些步骤严格采用 WW25 formal construction，哪些保留讲义教学抽象？**（对应第 12 节的选择）
8. 规格 v1.1 与本文的分歧（讲义层 vs WW25 层）在代码中如何**标注**？

---

## 19. 最终核心记忆

\[
S\;\rightarrow\;
m_i=\begin{cases}p+t_i,&i\in S\\0,&i\notin S\end{cases}
\;\rightarrow\;C_S
\]

授权用户：
\[
C_Sv_i+Az_i=p+t_i
\;\xrightarrow{\;\times s^T\;}\;
s^Tp+s^Tt_i
\;\xrightarrow{\;\text{用 }y_i\text{ 消去}\;}\;
s^Tp
\;\rightarrow\;b
\]

非授权用户：槽位为 \(0\) → 不能形成 \(s^Tp+s^Tt_i\) → 无法恢复 \(s^Tp\) → 无法恢复 \(b\)。

---

## 20. 参考资料

1. **课程讲义**：`papers/论文PPT.pdf`
   - p3–8 DBE 概念；p21–22 Succinct LWE；**p23–25 Matrix Commitments**；p26–30 Basic Approach；**p31–38 DBE For Unbounded Users [WW25]**
2. **WW25 正式构造**：Hoeteck Wee, David J. Wu. *Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE.* IACR ePrint **2025/1039**, CRYPTO 2025.
   - §3.2（Lemma 3.8 / Remark 3.9 / Lemma 3.10）；§4（Definition 4.1 / **Construction 4.2** / Theorem 4.3 / 4.4）；Appendix A
3. **CHW25**：Champion, Hsieh, Wu. *Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE.* IACR ePrint **2025/044**, CRYPTO 2025.
4. 配套文档：`docs/matrix-commitment-dbe-spec.md`（v1.1）、`docs/ww25-analysis.md`、`docs/official-sources.md`
