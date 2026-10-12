from __future__ import annotations

import itertools

from src.complete_subtree_mre.cover import cover, verify_cover
from src.complete_subtree_mre.service import (
    build_header,
    force_try_entry,
    generate_material,
    keygen,
    recover_content_key,
    setup,
)
from src.complete_subtree_mre.types import CsHeaderEntry, CsRecoverStatus
from tests.test_sm2_sm4_mre_core import FakeBackend


def test_tree_and_cover_match_nnl01_n8_r_u3():
    backend = FakeBackend()
    tree, _ = setup(8, backend=backend)
    assert tree.root_to_user_path(3) == (1, 2, 5, 10)
    assert cover(tree, {3}) == (3, 4, 11)


def test_cover_exactly_partitions_all_small_revocation_sets():
    backend = FakeBackend()
    for n in (1, 2, 4, 8):
        tree, _ = setup(n, backend=backend)
        for r in range(n + 1):
            for revoked_tuple in itertools.combinations(range(1, n + 1), r):
                revoked = set(revoked_tuple)
                roots = cover(tree, revoked)
                check = verify_cover(tree, revoked, roots)
                assert check["all_ok"] is True


def test_setup_uses_128_bit_sm4_node_keys_and_path_keygen():
    backend = FakeBackend()
    tree, node_keys = setup(8, backend=backend)
    assert len(node_keys) == 15
    assert all(len(value) == 16 for value in node_keys.values())
    u4 = keygen(tree, node_keys, 4)
    assert tuple(u4) == (1, 2, 5, 11)


def test_header_roundtrip_authorized_and_revoked():
    backend = FakeBackend()
    tree, node_keys = setup(8, backend=backend)
    revoked = {3}
    material = generate_material(backend=backend)
    entries = build_header(
        tree, node_keys, revoked, material, backend=backend
    )
    assert tuple(entry.node_id for entry in entries) == (3, 4, 11)

    for user_id in range(1, 9):
        recovered, result = recover_content_key(
            tree,
            keygen(tree, node_keys, user_id),
            user_id,
            entries,
            material.package_id,
            backend=backend,
        )
        if user_id == 3:
            assert recovered is None
            assert result.status == CsRecoverStatus.REVOKED
            assert result.trace.content_key_fingerprint is None
        else:
            assert recovered == material.content_key
            assert result.status == CsRecoverStatus.SUCCESS
            assert result.trace.matched_node_id in {3, 4, 11}


def test_force_try_wrong_path_key_is_rejected_by_real_aead_path():
    backend = FakeBackend()
    tree, node_keys = setup(8, backend=backend)
    material = generate_material(backend=backend)
    entries = build_header(
        tree, node_keys, {3}, material, backend=backend
    )
    target = next(entry for entry in entries if entry.node_id == 3)
    result = force_try_entry(
        tree,
        keygen(tree, node_keys, 3),
        3,
        target,
        material.package_id,
        backend=backend,
    )
    assert result.status == CsRecoverStatus.HEADER_UNWRAP_FAILED
    assert result.trace.attempted_key_node_id in {1, 2, 5, 10}
    assert result.trace.content_key_fingerprint is None


def test_tampered_header_entry_is_rejected():
    backend = FakeBackend()
    tree, node_keys = setup(8, backend=backend)
    material = generate_material(backend=backend)
    entries = list(build_header(tree, node_keys, {3}, material, backend=backend))
    original = entries[0]
    buf = bytearray(original.ciphertext)
    buf[-1] ^= 0x01
    entries[0] = CsHeaderEntry(
        node_id=original.node_id,
        iv=original.iv,
        ciphertext=bytes(buf),
    )

    # u5 is under cover root v3, so it hits the tampered entry.
    recovered, result = recover_content_key(
        tree,
        keygen(tree, node_keys, 5),
        5,
        tuple(entries),
        material.package_id,
        backend=backend,
    )
    assert recovered is None
    assert result.status == CsRecoverStatus.HEADER_UNWRAP_FAILED


def test_normal_trace_contains_only_fingerprint_not_raw_content_key():
    backend = FakeBackend()
    tree, node_keys = setup(4, backend=backend)
    material = generate_material(backend=backend)
    entries = build_header(tree, node_keys, {2}, material, backend=backend)
    _, result = recover_content_key(
        tree,
        keygen(tree, node_keys, 1),
        1,
        entries,
        material.package_id,
        backend=backend,
    )
    rendered = repr(result.trace)
    assert material.content_key.hex() not in rendered
    assert not hasattr(result.trace, "content_key")
