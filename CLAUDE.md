# Broadcast Encryption Course Project

## 1. Project Goal

本项目是一个工作实习课程设计，目标是实现并可视化一个广播加密系统。

核心要求：

给定用户集合 U 和广播集合 S，发送者对同一消息生成一个广播密文 C，使得：

- i ∈ S 的用户可以使用自己的密钥解密；
- i ∉ S 的用户不能解密。

最终系统需要支持有意义的文件，优先考虑图片和视频，并提供直观的可视化演示。

教师要求：
1. 查找文献，实现一个早期/经典广播加解密算法；
2. 尝试实现讲义中的“基于矩阵承诺的广播加密算法”；
3. 讲义/任务材料涉及 WW25；
4. 任务材料还提到：
   "Registered ABE and Adaptively-Secure Broadcast Encryption from Succinct LWE";
5. 如果论文有源码，可以研究其工程化和实用化改进；
6. 如果高级方案过难，允许回退到较简单的广播加密方案。

## 2. Development Strategy

必须按照以下阶段推进：

Research
→ Algorithm Specification
→ Minimal Prototype
→ Unit Tests
→ Cryptographic Audit
→ File Encryption
→ Visualization
→ Performance Experiments
→ Documentation

禁止直接从“论文”跳到“大型完整系统”。

## 3. Critical Cryptography Rules

### 3.1 不得臆造密码学算法

任何密码学核心步骤都必须能追溯到：
- 论文算法；
- 论文公式；
- 官方源码；
- 或明确标注为工程/教学简化。

如果无法确认，请标记 `[UNCERTAIN]`，停止继续假设。

### 3.2 区分三种实现

代码和文档中必须明确区分：

1. PAPER-FAITHFUL
   尽量忠实论文。

2. ENGINEERING ADAPTATION
   为了文件、GUI、性能或工程结构进行的改造。

3. TOY / DEMO
   仅用于解释思想，不具有正式密码学安全性。

绝不能把 TOY / DEMO 写成正式密码学实现。

### 3.3 不要把 AES 当成广播加密

如果处理图片/视频，应优先使用混合加密：

文件
→ AEAD（例如 AES-GCM）加密文件内容
→ Broadcast Encryption 加密随机会话密钥

广播加密负责“谁可以获得会话密钥”，AEAD 负责“大文件内容加密”。

### 3.4 不得自行声称“安全”

测试通过不等于密码学安全。

如果没有正式安全证明、标准库、密码学审计或论文依据，只能描述为 educational prototype。

## 4. Agent Behavior

Agent 必须：

- 优先阅读已有文档；
- 修改前说明计划；
- 尽量小范围修改；
- 不要为了一个任务重构整个项目；
- 修改代码后运行相关测试；
- 遇到密码学不确定点先报告，不要猜；
- 不要删除已有测试来“修复”失败；
- 不要通过放宽测试条件来制造绿色结果。

## 5. Repository Structure

推荐：

docs/
papers/
src/
tests/
scripts/
demo/
data/
prompts/

推荐文档：

docs/project-requirements.md
docs/research-notes.md
docs/baseline-analysis.md
docs/algorithm-spec.md
docs/ww25-analysis.md
docs/experiment-plan.md
docs/limitations.md

## 6. Testing Requirements

Baseline 至少测试：

- 单个授权用户；
- 多个授权用户；
- 不同授权集合；
- 非授权用户；
- 空/边界集合（如果方案允许）；
- 多次随机加密；
- 解密失败处理；
- 文件完整性。

## 7. Git Discipline

每完成一个里程碑再提交一次：

M0-init
M1-baseline
M2-file-encryption
M3-visualization
M4-matrix-commitment
M5-ww25-prototype
...

不要在没有测试的情况下提交“最终版”。

## 8. Final Deliverables

最终应尽量包含：

- 可运行源码；
- README；
- 算法原理；
- 算法流程图；
- 用户/广播集合说明；
- 图片/视频演示；
- 授权用户成功解密；
- 非授权用户失败；
- 实验数据；
- 已知限制；
- 论文与源码引用。

## 9. Current Priority

当前阶段默认优先级：

1. 找到适合课程设计的经典广播加密 Baseline；
2. 找到 WW25 / CHW25 的官方论文和源码；
3. 判断高级方案是否可实现；
4. 在 Baseline 上先形成完整可运行闭环。

在用户明确批准之前，不要直接开始 WW25/CHW25 的大规模编码。
