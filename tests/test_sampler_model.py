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


@st.composite
def slices(draw):
    model = draw(st.runner()).model_weights
    l = draw(st.none() | st.integers(-len(model), len(model) - 1))
    r = draw(st.none() | st.integers(-len(model), len(model) - 1))
    step = draw(st.none() | st.integers(-3, -3).filter(bool))
    return slice(l, r, step)


@st.composite
def slice_assignment(draw):
    model = draw(st.runner()).model_weights
    s = draw(slices())
    values = model[s]
    return (s, [draw(weights) for _ in values])


nonempty = precondition(lambda self: len(self.model_weights) > 0)

values = (
    st.runner().flatmap(
        lambda self: st.sampled_from(self.model_weights)
        if self.model_weights
        else st.nothing()
    )
    | weights
)


class SamplerStateMachine(RuleBasedStateMachine):
    @initialize(weights=st.lists(weights), random=st.randoms(use_true_random=False))
    def start(self, weights, random):
        self.sampler = UpdateableSampler(weights)
        self.model_weights = weights
        self.random = random

    @rule(i=indices, w=weights)
    @nonempty
    def setitem(self, i, w):
        self.sampler[i] = w
        self.model_weights[i] = w

    @rule(sa=slice_assignment())
    @nonempty
    def setitems(self, sa):
        s, w = sa
        self.sampler[s] = w
        self.model_weights[s] = w

    @rule(i=indices, w=weights)
    @nonempty
    def insert(self, i, w):
        self.sampler.insert(i, w)
        self.model_weights.insert(i, w)

    @rule()
    def reverse(self):
        ls = list(reversed(self.sampler))
        self.sampler.reverse()
        assert list(self.sampler) == ls
        self.model_weights.reverse()

    @rule()
    def copy(self):
        self.sampler = self.sampler.__deepcopy__({})

    @rule()
    def sort(self):
        self.sampler.sort()
        self.model_weights.sort()

    @rule(i=indices | slices())
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

    @rule(w=st.lists(weights))
    def extend(self, w):
        self.sampler.extend(w)
        self.model_weights.extend(w)

    @rule()
    def clear(self):
        self.sampler.clear()
        self.model_weights.clear()

    @rule(i=indices)
    def check_contained(self, i):
        v = self.model_weights[i]
        assert v in self.sampler
        assert self.sampler.index(v) <= i
        assert self.sampler.count(v) >= 1

    @rule(v=values)
    def remove(self, v):
        try:
            self.sampler.remove(v)
            self.model_weights.remove(v)
        except ValueError:
            pass

    @rule(v=values)
    def index(self, v):
        try:
            assert self.sampler.index(v) == self.model_weights.index(v)
        except ValueError:
            pass

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
