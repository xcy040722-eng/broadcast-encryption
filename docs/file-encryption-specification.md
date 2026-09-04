# 文件级混合广播加密规格（NNL01-CS + AES-256-GCM）

> 阶段：M2 · 对应 Prompt 06
> 前置：`src/cs/`（NNL01 Complete Subtree Baseline）已冻结，39 项测试通过。
> 性质：在 CS Baseline 之上实现文件级混合加密闭环，**不修改 CS 核心算法**。

---

## 1. 系统架构

```
NNL01 Complete Subtree (CS)   +   AES-256-GCM
        │                              │
   广播 Session Key K            加密文件内容 M
        │                              │
        └──────── Hybrid Broadcast Encryption ────────┘
```

- **CS 层**：负责「谁能够获得会话密钥 K」——由 NNL01 §3.1 的密钥分发结构保证。
- **AES-GCM 层**：负责「文件内容的机密性与完整性」——由 AES-256-GCM 的 AEAD 性质保证。

## 2. 为什么使用 Session Key（混合加密）

CS **不直接加密文件**，而是：

```
文件 M
   │
   ├── AES-256-GCM(K) ──────► encrypted body（大文件内容）
   │
   └── CS(K) ───────────────► header（会话密钥的受控分发）
```

原因：

1. **CS 的 header 长度随覆盖子树数量增长**（`r·log(N/r)`），把大文件直接交给 CS 会严重膨胀 header。
2. **CS 是广播加密**，其本质是「把同一个密钥分发给一个集合」，天然适合保护一个短密钥而非大文件。
3. **分层解耦**：CS 与 AES-GCM 各自独立、职责清晰，符合 CLAUDE.md §3.3「AEAD 加密文件 + BE 保护会话密钥」原则。

## 3. 密钥流

```
L_i（节点密钥，CS 长寿命密钥）
  │
  └─ NNL01 CS ──► K（会话密钥，256-bit，每文件新鲜随机）

K
  │
  └─ AES-256-GCM ──► 文件内容 M
```

## 4. 文件容器格式

版本化 JSON 结构（`src/file_crypto/format.py`）：

```json
{
    "version": 1,
    "algorithm": "NNL01-CS-AES256GCM",
    "original_filename": "...",
    "original_size": 123456,
    "cs_header": {
        "indices": [3, 4, 11],
        "encrypted": ["<base64>", ...]
    },
    "body": {
        "nonce": "<base64 12 bytes>",
        "ciphertext": "<base64 ciphertext||tag>"
    }
}
```

- 所有二进制字段（`encrypted`、`nonce`、`ciphertext`）均 base64 编码后存入 JSON。
- **绝不包含明文 Session Key K**（K 仅以 AES-GCM 密文形式存在于 `cs_header.encrypted`）。

## 5. Nonce 与 AAD 设计

### 5.1 两层 nonce 严格区分

系统中存在两层独立的 AES-256-GCM：

| 层 | 密钥 | 加密对象 | nonce 来源 | 存储位置 |
|---|---|---|---|---|
| CS header | 节点密钥 `L_i` | 会话密钥 K | `src/cs/crypto.py`（每次独立随机） | `cs_header` 各 entry 内嵌 |
| 文件 body | 会话密钥 K | 文件内容 M | `src/file_crypto/crypto.py`（每次独立随机） | `body.nonce` |

两层 nonce 各自独立生成、独立存储，**绝不共用同一个 nonce 管理逻辑**。

### 5.2 AAD

AES-GCM body 使用 AAD 认证关键元数据与 CS header：

```
AAD = 规范化 JSON（sort_keys=True, separators=(',',':'), UTF-8）：
      { version, algorithm, original_filename, original_size, cs_header }
```

- AAD **不包含 body**（nonce/ciphertext）。
- 加密与解密用**完全一致**的 `build_aad()` 生成，逐字节稳定。
- **篡改 version / algorithm / original_filename / original_size / cs_header 中任意一项都会导致 GCM 认证失败**，而不是解密出错误元数据。

## 6. 错误处理

| 情况 | 结果 |
|---|---|
| 用户被撤销（CS 无法恢复 K） | `DecryptionError` |
| header 被篡改 | `DecryptionError`（或 CS 层 InvalidTag → None） |
| body 被篡改 | AES-GCM `InvalidTag` → `DecryptionError` |
| nonce 被篡改 | `InvalidTag` → `DecryptionError` |
| AAD/元数据被篡改 | `InvalidTag` → `DecryptionError` |
| 文件格式损坏 / 版本不支持 / 字段缺失 | `InvalidPackageError`（`ValueError` 子类） |
| 输出文件已存在 | `FileExistsError`（除非 `overwrite=True`） |

### 失败时不留下伪造明文

`decrypt_file` 在**内存中完成 AES-GCM 认证**，认证通过后才写输出文件；任何失败路径都不会产生部分明文文件。

## 7. 大文件处理（第一版）

- 第一版采用 `read file → memory → AES-GCM → write package` 的简单策略。
- **不声称支持任意超大文件**，**不实现流式 AEAD**，**不描述为工业级流式加密**。

## 8. 安全边界

> CS 的安全性来自 NNL01 Complete Subtree Method 的广播密钥分发结构；AES-256-GCM 是工程级文件加密实例化。

- CS 是「文献级 baseline」，其广播安全由 NNL01 的 key-indistinguishability 性质保证。
- AES-256-GCM 是「工程适配」，提供文件内容的 AEAD。

## 9. ENGINEERING ADAPTATION

```
NNL01 E_L / F_K（抽象原语）
       │
       ▼
AES-256-GCM（工程实例化）
```

这是工程适配，**不声称论文原文规定使用 AES-GCM**。NNL01 原文的 `E_L`（header 块密码）与 `F_K`（body 流密码）是抽象原语，本实现统一用 AES-256-GCM 具体化。

## 10. 定位声明

本项目实现了 **NNL01 Complete Subtree Method 的课程设计级工程化版本**，并使用 **AES-256-GCM** 完成文件级混合加密。

- `CS = literature-based baseline`
- `AES-GCM = engineering adaptation`

（不宣称「工业级安全广播加密系统」。）
