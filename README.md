# Updatable Sampler

This package implements a data structure that stores a list of non-negative integer weights, with the ability to sample an index from the list, such that `i` is sampled with probability proportionate to `ls[i]`.

This is provided by the single type `updatable_sampler.UpdatableSampler`,
whose interface is exactly that provided by `list`, with two additional attributes:

* `total_weight` (property) is the current sum of the list.
* `sample(random)` takes a Random instance (or the random module) and returns a random index into the list, sampling `i` with probability proportionate to its value.


Other than this, and the restriction that its elements be non-negative integers, `UpdatableSampler` behaves exactly like a list.

## Performance

`total_weight` is `O(1)`.

`sample` and updating weights (including append) are worst case `O(log(min(n, log(W))))` where `W` is the maximum weight and `n` is the number of items.

Other methods have similar performance to their list equivalent, possibly with a similar overhead factor if they update the list.

This is a pure Python package (I may implement a C extension at some point) and hasn't been benchmarked with any degree of seriousness, so there is a decent chance

## Support Level

I want this for my own purposes, so I'm interested in receiving bug reports or patches on either correctness or performance issues.

I consider the API to be more or less complete, so am unlikely to accept feature requests.

This is not currently released on PyPI and needs to be installed from git (or just vendor the main file). I may fix this at some point.
