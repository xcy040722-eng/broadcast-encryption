# Prompt 08 — Matrix Commitment and WW25 Feasibility

现在进入高级方案研究。

【禁止直接写完整代码。】

研究讲义中的 Matrix Commitments 和 WW25。

从矩阵承诺开始解释：

C · v_i = m_i − A · z_i

解释：
- C
- v_i
- m_i
- A
- z_i
- low-norm
- commitment
- opening

然后解释 Matrix Commitment 为什么可以作为广播加密构造的基础。

再研究：

Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE

要求说明：

1. 它解决什么问题；
2. 什么是 Unbounded Users；
3. 什么是 Distributed Broadcast Encryption；
4. 什么是 Succinct LWE；
5. Matrix Commitment 在方案中扮演什么角色；
6. Setup；
7. Register/KeyGen；
8. Encrypt；
9. Decrypt；
10. 正确性；
11. 安全性依赖。

最后给出：

GREEN = 可以 faithful implementation
YELLOW = 可以做部分实现/原型
RED = 当前不建议实现

并列出具体 blocker。

输出：
docs/ww25-analysis.md
