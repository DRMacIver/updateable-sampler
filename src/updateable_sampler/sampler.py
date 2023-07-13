class UpdateableSampler:
    def __init__(self, data=()):
        self.__weights = []

        self.__bit_length_sampler = TreeBasedSampler()
        self.__pools = []
        self.__bit_lengths_index = {}

        for d in data:
            self.append(d)

    def __len__(self) -> int:
        return len(self.__weights)

    @property
    def total_weight(self):
        return self.__bit_length_sampler.total_weight

    def append(self, weight: int):
        i = len(self.__weights)
        self.__weights.append(0)
        self[i] = weight

    def pop(self):
        result = self.__weights[-1]
        self[len(self) - 1] = 0
        self.__weights.pop()
        return result

    def __delitem__(self, i: int):
        for j in range(i, len(self) - 1):
            self[j] = self[j + 1]
        self.pop()

    def __getitem__(self, i: int) -> int:
        return self.__weights[i]

    def __setitem__(self, i: int, v: int):
        prev = self.__weights[i]
        self.__weights[i] = v
        if prev == v:
            return
        n = v.bit_length()
        try:
            bi = self.__bit_lengths_index[n]
        except KeyError:
            bi = len(self.__bit_length_sampler)
            self.__bit_length_sampler.append(0)
            self.__bit_lengths_index[n] = bi
            self.__pools.append(Pool(n))

        pn = prev.bit_length()
        if pn != n:
            if prev > 0:
                prev_bi = self.__bit_lengths_index[pn]
                del self.__pools[prev_bi][i]
                self.__bit_length_sampler[prev_bi] -= prev
            if v > 0:
                self.__bit_length_sampler[bi] += v
                self.__pools[bi][i] = v
        else:
            self.__bit_length_sampler[bi] += v - prev
            self.__pools[bi][i] = v

    def sample(self, random):
        if self.total_weight == 0:
            raise ValueError("Cannot sample with all 0 weights")
        bi = self.__bit_length_sampler.sample(random)
        return self.__pools[bi].sample(random)


class CoinSampler:
    __slots__ = ("choice_weights",)

    def __init__(self, false_weight, true_weight):
        assert false_weight > 0 or true_weight > 0
        self.choice_weights = [(false_weight, true_weight)]

    def sample(self, random):
        i = 0
        while True:
            assert i <= len(self.choice_weights)
            if i == len(self.choice_weights):
                f, t = self.choice_weights[i - 1]
                assert f != t
                if t > f:
                    self.choice_weights.append((f, t - f))
                else:
                    self.choice_weights.append((f - t, t))
            f, t = self.choice_weights[i]
            if f == 0:
                assert t > 0
                return True
            elif t == 0:
                assert f > 0
                return False
            elif f == t:
                return bool(random.getrandbits(1))
            elif random.getrandbits(1):
                return t > f
            else:
                i += 1


class Pool:
    __slots__ = ("bit_length", "__tests", "__index", "__items")

    def __init__(self, bit_length):
        self.bit_length = bit_length
        self.__tests = [1 << k for k in range(bit_length - 1, -1, -1)]

        self.__index = {}
        self.__items = []

    def __setitem__(self, value, weight):
        assert weight > 0
        try:
            i = self.__index[value]
            self.__items[i][1] = weight
        except KeyError:
            i = len(self.__items)
            self.__index[value] = i
            self.__items.append([value, weight])

    def __delitem__(self, value):
        i = self.__index.pop(value)
        assert self.__items[i][0] == value
        replacer = self.__items.pop()
        if i < len(self.__items):
            self.__items[i] = replacer
            self.__index[replacer[0]] = i

    def sample(self, random):
        while True:
            i = random.randrange(0, len(self.__items))
            value, weight = self.__items[i]
            assert weight > 0
            for t in self.__tests:
                bit = random.getrandbits(1)
                test_set = t & weight
                if bit and not test_set:
                    break
                if not bit and test_set:
                    return value
            else:
                return value


class TreeBasedSampler:
    def __init__(self, values=()):
        self.__weights = []
        self.__child_weights = []
        self.__self_samplers = []
        self.__pick_left_samplers = []
        for v in values:
            self.append(v)

    @property
    def total_weight(self):
        return self.__total_weight(0)

    def __len__(self):
        return len(self.__weights)

    def __getitem__(self, i):
        return self.__weights[i]

    def append(self, v):
        self.__weights.append(0)
        self.__child_weights.append(0)
        self.__self_samplers.append(None)
        self.__pick_left_samplers.append(None)
        self[len(self.__weights) - 1] = v

    def pop(self):
        end = len(self.__weights) - 1
        result = self.__weights[end]
        self[end] = 0
        self.__weights.pop()
        self.__child_weights.pop()
        self.__self_samplers.pop()
        self.__pick_left_samplers.pop()
        return result

    def __setitem__(self, i, v):
        assert 0 <= i < len(self)
        if self.__weights[i] == v:
            return
        self.__weights[i] = v
        self.__self_samplers[i] = None
        while i > 0:
            i = (i - 1) // 2
            self.__self_samplers[i] = None
            self.__pick_left_samplers[i] = None
            j1 = i * 2 + 1
            j2 = i * 2 + 2
            self.__child_weights[i] = self.__total_weight(j1) + self.__total_weight(j2)

    def __delitem__(self, i: int):
        for j in range(i, len(self) - 1):
            self[j] = self[j + 1]
        self.pop()

    def __total_weight(self, i):
        if i >= len(self.__weights):
            return 0
        return self.__weights[i] + self.__child_weights[i]

    def sample(self, random):
        i = 0
        while True:
            j1 = 2 * i + 1
            j2 = 2 * i + 2
            if j1 >= len(self):
                return i
            if self.__self_samplers[i] is None:
                self.__self_samplers[i] = CoinSampler(
                    true_weight=self.__weights[i], false_weight=self.__child_weights[i]
                )
            if self.__self_samplers[i].sample(random):
                return i
            if j2 >= len(self):
                return j1
            if self.__pick_left_samplers[i] is None:
                self.__pick_left_samplers[i] = CoinSampler(
                    true_weight=self.__total_weight(j1),
                    false_weight=self.__total_weight(j2),
                )
            if self.__pick_left_samplers[i].sample(random):
                i = j1
            else:
                i = j2
