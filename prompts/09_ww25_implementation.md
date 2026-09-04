# Prompt 09 — WW25 Implementation

只有在 docs/ww25-analysis.md 判定 GREEN 或用户明确批准后执行。

第一步：不要写完整系统。

先实现最小密码学核心：

Setup
KeyGen/Register
Encrypt
Decrypt

要求：

1. 每个函数对应论文算法；
2. 标注对应论文章节和公式；
3. 不自行简化；
4. 如果为了可运行性进行参数缩小，明确标记为实验参数；
5. 写 correctness tests；
6. 测试多个用户；
7. 测试授权/非授权用户；
8. 对失败情况进行明确处理；
9. 与论文参数/算法差异写入 docs/ww25-implementation-notes.md。

完成后先运行测试。

不要加入 GUI。
不要加入图片/视频。
不要重构整个项目。
