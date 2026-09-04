# Prompt 03 — Algorithm Specification

现在你是密码学算法规格分析员。

基于已经确认的论文，禁止直接写项目代码。

将选定的 Baseline 广播加密方案转换成严格的算法规格。

必须分别写：

Setup()
KeyGen()
Encrypt()
Decrypt()

对于每个算法，给出：

1. 输入
2. 输出
3. 参数
4. 随机变量
5. 密钥
6. 中间变量
7. 数学公式
8. 每个变量的含义
9. 数据依赖关系
10. 正确性条件
11. 安全性依赖
12. 对应论文章节/公式

然后给出：

Paper
↓
Mathematical Definition
↓
Pseudocode
↓
Implementation Mapping

任何无法确认的地方标记 [UNCERTAIN]。

不要自行补全论文没有给出的步骤。

输出：
docs/algorithm-spec.md
