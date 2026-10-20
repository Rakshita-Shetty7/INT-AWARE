"""
Leakage-safe, class-stratified split by template family.

Why not a plain random split?
-----------------------------
Our corpus contains near-variants generated from the same template (e.g.
``cat /home/root/.ssh/id_rsa`` and ``cat /home/admin/.ssh/id_rsa``). A random
row-level split would scatter variants of one template across both train and
test, letting the model "memorise" a template and then be scored on an almost
identical string. That inflates accuracy and is a classic data-leak.

This module instead partitions **whole families** (``group`` = ``family_id``):
every variant of a family lands entirely in train OR entirely in test. The test
score therefore measures generalisation to command templates the model never saw.

To keep every one of the 10 classes present in both splits (GroupShuffleSplit
does not guarantee this), we split the families **within each class**.
"""

from __future__ import annotations

import random
from typing import List, Tuple


def stratified_group_split(
    commands: List[str],
    labels: List[str],
    groups: List[str],
    test_size: float = 0.2,
    seed: int = 1337,
) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str]]:
    """
    Splits the corpus by family, stratified per class.

    Returns (X_train, y_train, g_train, X_test, y_test, g_test).

    Guarantees:
      * No family_id appears in both train and test (no leakage).
      * Every class with >= 2 families contributes >= 1 family to the test set.
    """
    rng = random.Random(seed)

    # Map each class -> its set of family ids.
    class_to_families: dict = {}
    for lbl, grp in zip(labels, groups):
        class_to_families.setdefault(lbl, set()).add(grp)

    test_families = set()
    for lbl, fams in class_to_families.items():
        fam_list = sorted(fams)
        rng.shuffle(fam_list)
        n_test = max(1, round(len(fam_list) * test_size)) if len(fam_list) > 1 else 0
        for fam in fam_list[:n_test]:
            test_families.add(fam)

    X_train, y_train, g_train = [], [], []
    X_test, y_test, g_test = [], [], []
    for cmd, lbl, grp in zip(commands, labels, groups):
        if grp in test_families:
            X_test.append(cmd)
            y_test.append(lbl)
            g_test.append(grp)
        else:
            X_train.append(cmd)
            y_train.append(lbl)
            g_train.append(grp)

    # Safety assertion: disjoint families.
    assert not (set(g_train) & set(g_test)), "LEAKAGE: family present in both train and test"
    return X_train, y_train, g_train, X_test, y_test, g_test
