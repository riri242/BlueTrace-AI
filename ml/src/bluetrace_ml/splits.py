"""Group-disjoint dataset partitions; every drifter belongs to exactly one split."""

import numpy as np
from sklearn.model_selection import GroupShuffleSplit


def grouped_indices(frame, seed: int = 42, test_fraction: float = 0.15,
                    validation_fraction: float = 0.15):
    if not 0 < test_fraction < 1 or not 0 < validation_fraction < 1 or test_fraction + validation_fraction >= 1:
        raise ValueError("Invalid group split fractions")
    groups = frame["ID"].to_numpy()
    if len(np.unique(groups)) < 6:
        raise ValueError("At least six drifters are required for group-disjoint evaluation")
    indices = np.arange(len(frame))
    trainval, test = next(GroupShuffleSplit(n_splits=1, test_size=test_fraction,
                                           random_state=seed).split(indices, groups=groups))
    relative_valid = validation_fraction / (1 - test_fraction)
    train_local, valid_local = next(GroupShuffleSplit(n_splits=1, test_size=relative_valid,
                                                     random_state=seed + 1).split(
        trainval, groups=groups[trainval]
    ))
    train, valid = trainval[train_local], trainval[valid_local]
    assert not (set(groups[train]) & set(groups[valid]))
    assert not (set(groups[train]) & set(groups[test]))
    assert not (set(groups[valid]) & set(groups[test]))
    return {"train": train, "validation": valid, "test": test}
