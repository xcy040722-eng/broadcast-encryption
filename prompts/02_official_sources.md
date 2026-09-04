# Prompt 02 — Official Paper and Source Audit

现在只做资料定位和源码可行性分析，不写业务代码。

目标论文方向：

1. WW25:
   Unbounded Distributed Broadcast Encryption and Registered ABE from Succinct LWE

2. CHW25:
   Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE

任务：

1. 找到作者官方论文页面；
2. 找到正式论文/ePrint；
3. 找到作者提供的 GitHub/官方实现；
4. 确认仓库是否真的对应论文；
5. 记录语言、构建系统、依赖；
6. 找到 README、examples、tests；
7. 尝试只做“构建/运行原始示例”，不要修改源码；
8. 判断源码属于：
   - 完整论文实现
   - 实验代码
   - 原型
   - 辅助代码
   - 其他
9. 判断能否用于本课程设计；
10. 判断是否适合直接接入 Python GUI。

输出：

docs/official-sources.md

最后给出：
GREEN = 可以直接研究/复用
YELLOW = 可以研究，但需要较多工程工作
RED = 当前不建议作为主实现

不要因为“有 GitHub”就默认可以直接使用。
