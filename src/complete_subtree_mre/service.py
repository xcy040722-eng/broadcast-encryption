"""GmSSL-backed service layer for NNL01 Complete Subtree.

The tree/cover logic follows the Complete Subtree method.  NNL01 leaves the
symmetric primitive E_L abstract; this engineering implementation instantiates
E_L with SM4-GCM so it shares the same native GmSSL backend and safety boundary
as the SM2+SM4 workbench.
"""

from __future__ import annotations

from io import BytesIO
from typing import Mapping

from src.sm2_sm4_mre.backend import CryptoBackend
from src.sm2_sm4_mre.gmssl_backend import GmsslBackend

from .cover import cover
from .errors import CsEnvelopeError
from .tree import CompleteSubtreeTree
from .types import (
    CS_HEADER_MAGIC,
    CS_HEADER_VERSION,
    CS_KEY_SIZE,
    CS_PACKAGE_ID_SIZE,
    CsHeaderEntry,
    CsMaterial,
    CsRecoverResult,
    CsRecoverStatus,
    CsRecoverTrace,
    CsTraceEvent,
)


def _backend_or_default(backend: CryptoBackend | None) -> CryptoBackend:
    return backend if backend is not None else GmsslBackend()


def fingerprint(backend: CryptoBackend, data: bytes) -> str:
    """Safe display fingerprint; never expose raw keys in normal traces."""
    return backend.sm3(data).hex()[:16]


def setup(
    n: int,
    *,
    backend: CryptoBackend | None = None,
) -> tuple[CompleteSubtreeTree, dict[int, bytes]]:
    """Create the CS tree and one independent 128-bit key for every node."""
    b = _backend_or_default(backend)
    if b.sm4_key_size != CS_KEY_SIZE:
        raise ValueError(
            f"backend SM4 key size is {b.sm4_key_size}, expected {CS_KEY_SIZE}"
        )
    tree = CompleteSubtreeTree(n)
    node_keys = {
        node_id: b.random_bytes(CS_KEY_SIZE)
        for node_id in range(1, tree.node_count + 1)
    }
    return tree, node_keys


def keygen(
    tree: CompleteSubtreeTree,
    node_keys: Mapping[int, bytes],
    user_id: int,
) -> dict[int, bytes]:
    """Provision one receiver with the keys on its root-to-leaf path."""
    path = tree.root_to_user_path(user_id)
    return {node_id: node_keys[node_id] for node_id in path}


def generate_material(
    *,
    backend: CryptoBackend | None = None,
) -> CsMaterial:
    """Generate a fresh broadcast ID and one 128-bit content/session key K."""
    b = _backend_or_default(backend)
    return CsMaterial(
        package_id=b.random_bytes(CS_PACKAGE_ID_SIZE),
        content_key=b.random_bytes(CS_KEY_SIZE),
    )


def _node_bytes(node_id: int) -> bytes:
    if not 1 <= node_id <= 0xFFFFFFFF:
        raise ValueError(f"node id out of encodable range: {node_id}")
    return node_id.to_bytes(4, "big")


def _header_aad(package_id: bytes, node_id: int) -> bytes:
    if len(package_id) != CS_PACKAGE_ID_SIZE:
        raise ValueError("invalid package_id length")
    return b"CS-HDR-AAD1" + package_id + _node_bytes(node_id)


def _encode_envelope(package_id: bytes, node_id: int, content_key: bytes) -> bytes:
    if len(package_id) != CS_PACKAGE_ID_SIZE:
        raise ValueError("invalid package_id length")
    if len(content_key) != CS_KEY_SIZE:
        raise ValueError("invalid content key length")
    return (
        CS_HEADER_MAGIC
        + bytes([CS_HEADER_VERSION])
        + package_id
        + _node_bytes(node_id)
        + content_key
    )


def _decode_envelope(
    data: bytes,
    *,
    expected_package_id: bytes,
    expected_node_id: int,
) -> bytes:
    expected_len = len(CS_HEADER_MAGIC) + 1 + CS_PACKAGE_ID_SIZE + 4 + CS_KEY_SIZE
    if len(data) != expected_len:
        raise CsEnvelopeError("invalid CS key-envelope length")
    if data[: len(CS_HEADER_MAGIC)] != CS_HEADER_MAGIC:
        raise CsEnvelopeError("invalid CS key-envelope magic")
    pos = len(CS_HEADER_MAGIC)
    if data[pos] != CS_HEADER_VERSION:
        raise CsEnvelopeError("unsupported CS key-envelope version")
    pos += 1
    package_id = data[pos : pos + CS_PACKAGE_ID_SIZE]
    pos += CS_PACKAGE_ID_SIZE
    node_id = int.from_bytes(data[pos : pos + 4], "big")
    pos += 4
    content_key = data[pos : pos + CS_KEY_SIZE]
    if package_id != expected_package_id:
        raise CsEnvelopeError("CS key-envelope package_id mismatch")
    if node_id != expected_node_id:
        raise CsEnvelopeError(
            f"CS key-envelope node mismatch: {node_id} != {expected_node_id}"
        )
    return content_key


def wrap_content_key(
    node_key: bytes,
    *,
    package_id: bytes,
    node_id: int,
    content_key: bytes,
    backend: CryptoBackend | None = None,
) -> CsHeaderEntry:
    """Instantiate NNL01 E_L(K) with SM4-GCM for one cover node."""
    b = _backend_or_default(backend)
    if len(node_key) != CS_KEY_SIZE:
        raise ValueError("invalid Complete Subtree node-key length")
    iv = b.random_bytes(b.sm4_gcm_iv_size)
    plaintext = _encode_envelope(package_id, node_id, content_key)
    source = BytesIO(plaintext)
    sink = BytesIO()
    b.sm4_gcm_encrypt_stream(
        node_key,
        iv,
        _header_aad(package_id, node_id),
        source,
        sink,
        chunk_size=4096,
    )
    return CsHeaderEntry(node_id=node_id, iv=iv, ciphertext=sink.getvalue())


def unwrap_content_key(
    node_key: bytes,
    entry: CsHeaderEntry,
    *,
    expected_package_id: bytes,
    backend: CryptoBackend | None = None,
) -> bytes:
    """SM4-GCM-decrypt one Complete Subtree header entry and verify binding."""
    b = _backend_or_default(backend)
    source = BytesIO(entry.ciphertext)
    sink = BytesIO()
    b.sm4_gcm_decrypt_stream(
        node_key,
        entry.iv,
        _header_aad(expected_package_id, entry.node_id),
        source,
        sink,
        chunk_size=4096,
    )
    return _decode_envelope(
        sink.getvalue(),
        expected_package_id=expected_package_id,
        expected_node_id=entry.node_id,
    )


def build_header(
    tree: CompleteSubtreeTree,
    node_keys: Mapping[int, bytes],
    revoked: set[int],
    material: CsMaterial,
    *,
    backend: CryptoBackend | None = None,
) -> tuple[CsHeaderEntry, ...]:
    r"""Compute Cover(U\R) and encrypt the same K under every cover-node key."""
    b = _backend_or_default(backend)
    roots = cover(tree, revoked)
    return tuple(
        wrap_content_key(
            node_keys[node_id],
            package_id=material.package_id,
            node_id=node_id,
            content_key=material.content_key,
            backend=b,
        )
        for node_id in roots
    )


def recover_content_key(
    tree: CompleteSubtreeTree,
    user_keyring: Mapping[int, bytes],
    user_id: int,
    entries: tuple[CsHeaderEntry, ...],
    package_id: bytes,
    *,
    backend: CryptoBackend | None = None,
) -> tuple[bytes | None, CsRecoverResult]:
    """Recover K for one receiver using exactly one matching cover-node key."""
    b = _backend_or_default(backend)
    path = tree.root_to_user_path(user_id)
    trace = CsRecoverTrace(user_id=user_id, user_path_nodes=path)
    entry_map = {entry.node_id: entry for entry in entries}
    if len(entry_map) != len(entries):
        trace.events.append(
            CsTraceEvent("header", "error", "duplicate cover-node entry")
        )
        return None, CsRecoverResult(
            CsRecoverStatus.INVALID_HEADER,
            "header contains duplicate cover-node entries",
            trace,
        )

    matching = [node_id for node_id in path if node_id in entry_map]
    if not matching:
        trace.events.append(
            CsTraceEvent("cover-match", "denied", "receiver path hits no cover node")
        )
        return None, CsRecoverResult(
            CsRecoverStatus.REVOKED,
            f"u{user_id} has no matching Complete Subtree header entry",
            trace,
        )
    if len(matching) != 1:
        trace.events.append(
            CsTraceEvent(
                "cover-match",
                "error",
                f"receiver path unexpectedly hits {len(matching)} cover nodes",
            )
        )
        return None, CsRecoverResult(
            CsRecoverStatus.INVALID_HEADER,
            "header violates Complete Subtree disjoint-cover invariant",
            trace,
        )

    node_id = matching[0]
    entry = entry_map[node_id]
    trace.matched_node_id = node_id
    trace.header_fingerprint = fingerprint(b, entry.iv + entry.ciphertext)
    try:
        content_key = unwrap_content_key(
            user_keyring[node_id],
            entry,
            expected_package_id=package_id,
            backend=b,
        )
    except CsEnvelopeError as exc:
        trace.events.append(CsTraceEvent("envelope", "error", str(exc)))
        return None, CsRecoverResult(
            CsRecoverStatus.ENVELOPE_MISMATCH,
            str(exc),
            trace,
        )
    except Exception as exc:
        trace.events.append(CsTraceEvent("header-unwrap", "error", str(exc)))
        return None, CsRecoverResult(
            CsRecoverStatus.HEADER_UNWRAP_FAILED,
            f"SM4-GCM header unwrap failed: {exc}",
            trace,
        )

    trace.content_key_fingerprint = fingerprint(b, content_key)
    trace.events.append(
        CsTraceEvent(
            "header-unwrap",
            "ok",
            f"recovered K through cover node v{node_id}",
        )
    )
    return content_key, CsRecoverResult(
        CsRecoverStatus.SUCCESS,
        f"u{user_id} recovered the broadcast content key through v{node_id}",
        trace,
    )


def force_try_entry(
    tree: CompleteSubtreeTree,
    user_keyring: Mapping[int, bytes],
    user_id: int,
    target_entry: CsHeaderEntry,
    package_id: bytes,
    *,
    attack_node_id: int | None = None,
    backend: CryptoBackend | None = None,
) -> CsRecoverResult:
    """Educational negative path: use one receiver path key on another cover entry."""
    b = _backend_or_default(backend)
    path = tree.root_to_user_path(user_id)
    candidates = [
        node_id for node_id in path
        if node_id in user_keyring and node_id != target_entry.node_id
    ]
    chosen = attack_node_id if attack_node_id is not None else (candidates[-1] if candidates else None)
    trace = CsRecoverTrace(
        user_id=user_id,
        user_path_nodes=path,
        matched_node_id=target_entry.node_id,
        attempted_key_node_id=chosen,
        header_fingerprint=fingerprint(b, target_entry.iv + target_entry.ciphertext),
    )
    if chosen is None or chosen not in user_keyring:
        trace.events.append(CsTraceEvent("force-try", "error", "no usable attack key"))
        return CsRecoverResult(
            CsRecoverStatus.INVALID_HEADER,
            "no receiver path key is available for force-try",
            trace,
        )

    try:
        content_key = unwrap_content_key(
            user_keyring[chosen],
            target_entry,
            expected_package_id=package_id,
            backend=b,
        )
    except CsEnvelopeError as exc:
        trace.events.append(CsTraceEvent("force-envelope", "error", str(exc)))
        return CsRecoverResult(CsRecoverStatus.ENVELOPE_MISMATCH, str(exc), trace)
    except Exception as exc:
        trace.events.append(CsTraceEvent("force-header-unwrap", "error", str(exc)))
        return CsRecoverResult(
            CsRecoverStatus.HEADER_UNWRAP_FAILED,
            f"wrong path key L[{chosen}] cannot unwrap header E[L{target_entry.node_id}](K)",
            trace,
        )

    trace.content_key_fingerprint = fingerprint(b, content_key)
    trace.events.append(
        CsTraceEvent("force-header-unwrap", "unexpected-success", "wrong-key unwrap succeeded")
    )
    return CsRecoverResult(
        CsRecoverStatus.SUCCESS,
        "force-try unexpectedly recovered a valid content key",
        trace,
    )
