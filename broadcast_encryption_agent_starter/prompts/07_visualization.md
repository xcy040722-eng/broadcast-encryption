# Prompt 07 — Visualization

现在制作课程设计可视化原型。

优先考虑简单、易运行的 Python Web UI，例如 Streamlit。

页面至少包含：

1. 用户列表；
2. 用户密钥状态；
3. 文件选择；
4. 广播集合选择；
5. Broadcast Encrypt 按钮；
6. 显示“同一个密文”；
7. 选择用户进行解密；
8. 授权用户显示解密成功；
9. 非授权用户显示解密失败；
10. 图片解密后直接显示；
11. 视频尽量提供播放/下载预览；
12. 显示算法名称；
13. 显示广播集合 S；
14. 显示实验耗时。

建议演示：

Users:
Alice
Bob
Charlie
David

Broadcast Set:
{Alice, Charlie}

Ciphertext:
photo.enc

Alice → ✓
Charlie → ✓
Bob → ✗
David → ✗

重要：
GUI 不得绕过密码学模块。
GUI 只调用已经测试通过的 API。

输出：
demo/
docs/visualization-design.md
