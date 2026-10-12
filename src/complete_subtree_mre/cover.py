"""Steiner-tree and cover computation for NNL01 Complete Subtree."""

from __future__ import annotations

from .tree import CompleteSubtreeTree


def validate_revoked(tree: CompleteSubtreeTree, revoked: set[int]) -> None:
    invalid = sorted(uid for uid in revoked if not 1 <= uid <= tree.n)
    if invalid:
        raise ValueError(f"revoked user ids out of range: {invalid}")


def steiner_tree(tree: CompleteSubtreeTree, revoked: set[int]) -> tuple[int, ...]:
    """Return ST(R): union of every revoked leaf-to-root path."""
    validate_revoked(tree, revoked)
    nodes: set[int] = set()
    for user_id in revoked:
        nodes.update(tree.path_to_root(tree.leaf_of_user(user_id)))
    return tuple(sorted(nodes))


def cover(tree: CompleteSubtreeTree, revoked: set[int]) -> tuple[int, ...]:
    r"""Return roots of the disjoint complete subtrees covering U \ R.

    These are exactly the subtrees hanging off ST(R).  When R is empty, the
    whole tree is one cover subset.  When every user is revoked, the cover is
    empty.
    """
    validate_revoked(tree, revoked)
    if not revoked:
        return (tree.root,)

    st = set(steiner_tree(tree, revoked))
    roots: list[int] = []
    for node in sorted(st):
        children = tree.children(node)
        in_st = [child for child in children if child in st]
        if len(in_st) == 1:
            roots.extend(child for child in children if child not in st)
    return tuple(sorted(roots))


def covered_users(tree: CompleteSubtreeTree, roots: tuple[int, ...]) -> tuple[int, ...]:
    users: set[int] = set()
    for root in roots:
        users.update(tree.users_in_subtree(root))
    return tuple(sorted(users))


def verify_cover(
    tree: CompleteSubtreeTree,
    revoked: set[int],
    roots: tuple[int, ...],
) -> dict[str, object]:
    """Return correctness checks used by tests and the future UI."""
    expected = set(range(1, tree.n + 1)) - revoked
    subsets = [set(tree.users_in_subtree(root)) for root in roots]
    union: set[int] = set()
    for subset in subsets:
        union.update(subset)
    pairwise_disjoint = all(
        subsets[i].isdisjoint(subsets[j])
        for i in range(len(subsets))
        for j in range(i + 1, len(subsets))
    )
    return {
        "covered_users": tuple(sorted(union)),
        "union_ok": union == expected,
        "no_revoked_ok": union.isdisjoint(revoked),
        "disjoint_ok": pairwise_disjoint,
        "all_ok": union == expected and union.isdisjoint(revoked) and pairwise_disjoint,
    }
