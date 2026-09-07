"""真实媒体文件的字节数据（用于媒体加密闭环 Demo / 测试）。

- PNG：1x1 透明 PNG（67 字节）
- JPEG：1x1 白色 JPEG（~160 字节）
- MP4：最小 ftyp+mdat 结构（32 字节，代表视频文件）
"""

from __future__ import annotations

import base64

# 1x1 透明 PNG
PNG_BYTES: bytes = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

# 1x1 白色 JPEG
JPEG_BYTES: bytes = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/"
    "wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AfwD/2Q=="
)

# 最小 MP4（ftyp box + 空 mdat box）
MP4_BYTES: bytes = bytes.fromhex(
    "00000018"  # ftyp size = 24
    "66747970"  # 'ftyp'
    "69736f6d"  # major_brand = 'isom'
    "00000000"  # minor_version = 0
    "69736f6d"  # compatible_brands = 'isom'
    "00000008"  # mdat size = 8
    "6d646174"  # 'mdat'
)

# 三个媒体：文件名后缀 -> bytes
MEDIA = {
    "image_png": PNG_BYTES,
    "image_jpeg": JPEG_BYTES,
    "video_mp4": MP4_BYTES,
}
