from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine
from hypothesis.stateful import initialize
from hypothesis.stateful import invariant
from hypothesis.stateful import precondition
from hypothesis.stateful import rule

from updateable_sampler import UpdateableSampler
from updateable_sampler.sampler import TreeBasedSampler


weights = st.just(0) | st.integers(min_value=0)

indices = st.runner().flatmap(
    lambda self: st.integers(0, len(self.model_weights) - 1)
    if self.model_weights
    else st.nothing()
)

nonempty = precondition(lambda self: len(self.model_weights) > 0)


class SamplerStateMachine(RuleBasedStateMachine):
    @initialize(
        weights=st.lists(weights),
        random=st.randoms(use_true_random=False),
        cls=st.sampled_from([UpdateableSampler, TreeBasedSampler]),
    )
    def start(self, weights, random, cls):
        self.sampler = cls(weights)
        self.model_weights = weights
        self.random = random

    @rule(i=indices, w=weights)
    @nonempty
    def setitem(self, i, w):
        self.sampler[i] = w
        self.model_weights[i] = w

    @rule(i=indices)
    @nonempty
    def delitem(self, i):
        del self.sampler[i]
        del self.model_weights[i]

    @rule()
    @nonempty
    def pop(self):
        a = self.sampler.pop()
        b = self.model_weights.pop()
        assert a == b

    @rule(w=weights)
    def push(self, w):
        self.sampler.append(w)
        self.model_weights.append(w)

    @rule()
    @precondition(lambda self: sum(self.model_weights, start=0) > 0)
    def sample(self):
        i = self.sampler.sample(self.random)
        assert self.model_weights[i] > 0

    @invariant()
    def all_equal(self):
        assert len(self.model_weights) == len(self.sampler)
        assert self.sampler.total_weight == sum(self.model_weights, start=0)
        for i, v in enumerate(self.model_weights):
            assert self.sampler[i] == v


TestSamplerModel = SamplerStateMachine.TestCase
