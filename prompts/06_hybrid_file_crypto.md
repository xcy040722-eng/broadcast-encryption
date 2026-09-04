# Prompt 06 — Hybrid Encryption for Image/Video

Baseline 已通过密码学测试后，现在加入真实文件。

设计混合加密架构：

原始文件
→ 随机生成会话密钥
→ AEAD 加密文件内容
→ Broadcast Encryption 加密会话密钥
→ 形成一个统一的加密包

要求：

1. 支持 JPG/PNG；
2. 尽量支持 MP4；
3. 保留原始文件名和 MIME/type 等非敏感元数据；
4. 大文件不要直接送入广播加密；
5. 广播加密只负责保护会话密钥；
6. 文件内容使用成熟 AEAD；
7. 正确处理 nonce；
8. 解密后必须进行完整性验证；
9. 授权用户能够恢复文件；
10. 非授权用户不能恢复文件；
11. 加密包结构有版本号；
12. 编写单元测试和集成测试。

不要改变 Baseline 的核心密码学实现。

输出：
- src/file_crypto/
- tests/file_crypto/
- docs/file-encryption-design.md
