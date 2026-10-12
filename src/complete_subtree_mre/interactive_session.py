"""State model for an interactive Complete Subtree teaching workbench.

Like SM2+SM4 InteractiveSession, this class coordinates already-defined crypto
operations one step at a time.  Safe snapshots contain fingerprints and graph
state only; raw node keys and raw K stay private inside the session.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.sm2_sm4_mre.backend import CryptoBackend
from src.sm2_sm4_mre.gmssl_backend import GmsslBackend

from .cover import cover, steiner_tree, verify_cover
from .service import (
    fingerprint,
    force_try_entry,
    generate_material,
    keygen,
    recover_content_key,
    setup,
    wrap_content_key,
)
from .types import CsHeaderEntry, CsMaterial, CsRecoverResult
from .tree import CompleteSubtreeTree


class CsSessionStage(str, Enum):
    CONFIGURING = "CONFIGURING"
    COVER_READY = "COVER_READY"
    MATERIAL_READY = "MATERIAL_READY"
    WRAPPING = "WRAPPING"
    HEADER_READY = "HEADER_READY"


@dataclass(frozen=True)
class CsSessionSnapshot:
    stage: CsSessionStage
    n: int
    revoked_users: tuple[int, ...]
    steiner_nodes: tuple[int, ...]
    cover_roots: tuple[int, ...]
    covered_users: tuple[int, ...]
    package_id: str | None
    content_key_fingerprint: str | None
    wrapped_nodes: tuple[int, ...]
    header_fingerprints: dict[int, str]
    setup_key_count: int
    per_user_key_count: int


class CompleteSubtreeSession:
    """One long-lived CS key tree plus one manually controlled broadcast."""

    def __init__(
        self,
        n: int = 8,
        *,
        backend: CryptoBackend | None = None,
    ) -> None:
        self.backend = backend if backend is not None else GmsslBackend()
        self.tree, self._node_keys = setup(n, backend=self.backend)
        self.revoked_users: set[int] = set()
        self._steiner_nodes: tuple[int, ...] = ()
        self._cover_roots: tuple[int, ...] | None = None
        self._material: CsMaterial | None = None
        self._entries: dict[int, CsHeaderEntry] = {}

    @property
    def stage(self) -> CsSessionStage:
        if self._cover_roots is None:
            return CsSessionStage.CONFIGURING
        if self._material is None:
            return CsSessionStage.COVER_READY
        expected = set(self._cover_roots)
        actual = set(self._entries)
        if actual == expected:
            return CsSessionStage.HEADER_READY
        if actual:
            return CsSessionStage.WRAPPING
        return CsSessionStage.MATERIAL_READY

    def snapshot(self) -> CsSessionSnapshot:
        roots = self._cover_roots or ()
        covered: tuple[int, ...] = ()
        if self._cover_roots is not None:
            check = verify_cover(self.tree, self.revoked_users, roots)
            covered = tuple(check["covered_users"])  # type: ignore[arg-type]
        return CsSessionSnapshot(
            stage=self.stage,
            n=self.tree.n,
            revoked_users=tuple(sorted(self.revoked_users)),
            steiner_nodes=self._steiner_nodes,
            cover_roots=roots,
            covered_users=covered,
            package_id=self._material.package_id.hex() if self._material else None,
            content_key_fingerprint=(
                fingerprint(self.backend, self._material.content_key)
                if self._material
                else None
            ),
            wrapped_nodes=tuple(sorted(self._entries)),
            header_fingerprints={
                node_id: fingerprint(self.backend, entry.iv + entry.ciphertext)
                for node_id, entry in sorted(self._entries.items())
            },
            setup_key_count=len(self._node_keys),
            per_user_key_count=self.tree.height + 1,
        )

    def set_revoked(self, user_id: int, revoked: bool) -> CsSessionSnapshot:
        if self._material is not None or self._entries:
            raise RuntimeError("reset the broadcast before changing the revocation set")
        self.tree.leaf_of_user(user_id)  # validate
        if revoked:
            self.revoked_users.add(user_id)
        else:
            self.revoked_users.discard(user_id)
        self._cover_roots = None
        self._steiner_nodes = ()
        return self.snapshot()

    def compute_cover(self) -> CsSessionSnapshot:
        if self._material is not None or self._entries:
            raise RuntimeError("reset the broadcast before recomputing the cover")
        self._steiner_nodes = steiner_tree(self.tree, self.revoked_users)
        self._cover_roots = cover(self.tree, self.revoked_users)
        check = verify_cover(self.tree, self.revoked_users, self._cover_roots)
        if not check["all_ok"]:
            raise RuntimeError("Complete Subtree cover invariant failed")
        return self.snapshot()

    def generate_content_material(self) -> CsSessionSnapshot:
        if self._cover_roots is None:
            raise RuntimeError("compute the Complete Subtree cover first")
        if self._material is not None:
            raise RuntimeError("content material already exists")
        self._material = generate_material(backend=self.backend)
        return self.snapshot()

    def wrap_for_node(self, node_id: int) -> CsHeaderEntry:
        if self._cover_roots is None or self._material is None:
            raise RuntimeError("cover and content material must exist first")
        if node_id not in self._cover_roots:
            raise ValueError(f"v{node_id} is not a cover root")
        if node_id in self._entries:
            raise ValueError(f"header entry for v{node_id} already exists")
        entry = wrap_content_key(
            self._node_keys[node_id],
            package_id=self._material.package_id,
            node_id=node_id,
            content_key=self._material.content_key,
            backend=self.backend,
        )
        self._entries[node_id] = entry
        return entry

    def wrap_all(self) -> CsSessionSnapshot:
        if self._cover_roots is None:
            raise RuntimeError("compute the cover first")
        for node_id in self._cover_roots:
            if node_id not in self._entries:
                self.wrap_for_node(node_id)
        return self.snapshot()

    def recover_as(self, user_id: int) -> CsRecoverResult:
        if self.stage != CsSessionStage.HEADER_READY or self._material is None:
            raise RuntimeError("Complete Subtree header is not ready")
        user_keys = keygen(self.tree, self._node_keys, user_id)
        recovered, result = recover_content_key(
            self.tree,
            user_keys,
            user_id,
            tuple(self._entries[node] for node in sorted(self._entries)),
            self._material.package_id,
            backend=self.backend,
        )
        if recovered is not None:
            if fingerprint(self.backend, recovered) != fingerprint(
                self.backend, self._material.content_key
            ):
                raise RuntimeError("recovered content-key fingerprint mismatch")
        return result

    def force_try(self, user_id: int, target_node_id: int) -> CsRecoverResult:
        if self.stage != CsSessionStage.HEADER_READY or self._material is None:
            raise RuntimeError("Complete Subtree header is not ready")
        if target_node_id not in self._entries:
            raise ValueError(f"v{target_node_id} has no header entry")
        user_keys = keygen(self.tree, self._node_keys, user_id)
        return force_try_entry(
            self.tree,
            user_keys,
            user_id,
            self._entries[target_node_id],
            self._material.package_id,
            backend=self.backend,
        )

    def reset_broadcast(self, *, keep_revoked: bool = False) -> CsSessionSnapshot:
        if not keep_revoked:
            self.revoked_users.clear()
        self._steiner_nodes = ()
        self._cover_roots = None
        self._material = None
        self._entries.clear()
        return self.snapshot()
