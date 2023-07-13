import random

import pytest
from hypothesis import assume
from hypothesis import example
from hypothesis import given
from hypothesis import strategies as st

from updatable_sampler import UpdatableSampler
from updatable_sampler.sampler import CoinSampler
from updatable_sampler.sampler import TreeBasedSampler


@pytest.mark.parametrize("cls", [UpdatableSampler, TreeBasedSampler])
def test_sampling_from_single_element(cls):
    sampler = cls([1])
    assert sampler.sample(random) == 0
    assert sampler[0] == 1


@pytest.mark.parametrize("cls", [UpdatableSampler, TreeBasedSampler])
def test_sampling_correct_element(cls):
    sampler = cls([0, 1])
    for _ in range(100):
        assert sampler.sample(random) == 1


@pytest.mark.parametrize("cls", [UpdatableSampler, TreeBasedSampler])
def test_empty_colletion_has_zero_weight(cls):
    sampler = cls()
    assert sampler.total_weight == 0


@example(weights=[0, 0, 0, 0, 0, 0, 1])
@pytest.mark.parametrize("cls", [UpdatableSampler, TreeBasedSampler])
@given(weights=st.lists(st.integers(min_value=0)))
def test_has_correct_total_weight(weights, cls):
    sampler = cls(weights)
    assert sampler.total_weight == sum(weights, start=0)


@example(weights=[1, 1])
@pytest.mark.parametrize("cls", [UpdatableSampler, TreeBasedSampler])
@given(weights=st.lists(st.integers(min_value=0), min_size=1))
def test_pops_last_element(weights, cls):
    sampler = cls(weights)
    assert sampler.pop() == weights[-1]
    assert list(sampler) == weights[:-1]
    assert sampler.total_weight == sum(sampler)


def test_always_true_coin_sampler():
    cs = CoinSampler(false_weight=0, true_weight=1)
    for _ in range(100):
        assert cs.sample(random)


def test_always_false_coin_sampler():
    cs = CoinSampler(false_weight=1, true_weight=0)
    for _ in range(100):
        assert not cs.sample(random)


def test_balanced_coin_sampler():
    cs = CoinSampler(false_weight=1, true_weight=1)
    n = sum(cs.sample(random) for _ in range(1000))
    assert 200 <= n <= 800


@pytest.mark.parametrize("cls", [UpdatableSampler, TreeBasedSampler])
@given(
    weights=st.lists(st.integers(min_value=0), min_size=1),
    data=st.data(),
    rnd=st.randoms(use_true_random=True),
)
def test_boosting_increases_chances(cls, weights, data, rnd):
    i = data.draw(st.integers(0, len(weights) - 1))
    assume(sum(weights) > 0)
    sampler = cls(weights)

    sampler[i] = 10 * sampler.total_weight

    n = sum(sampler.sample(rnd) == i for _ in range(100))

    assert n >= 20


def test_cannot_sample_from_zero_weight():
    x = UpdatableSampler([0])
    with pytest.raises(ValueError):
        x.sample(random)


def test_equality():
    x = UpdatableSampler([1, 2, 3])
    assert x == x
    assert x == x.copy()
    assert x != list(x)
    b = x == list(x)
    assert not b

    assert x != UpdatableSampler([1, 2, 3, 0])
    assert x != UpdatableSampler([3, 2, 1])


def test_invalid_weights():
    with pytest.raises(TypeError):
        UpdatableSampler([0.0])

    with pytest.raises(ValueError):
        UpdatableSampler([-1])
