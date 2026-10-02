## 2024-05-18 - Dictionary Iteration Pattern
**Learning:** In Python, iterating over a dictionary using `for k in d:` and removing items dynamically (e.g. `d.pop(k)`) followed immediately by `break` is safe and significantly faster than taking a full copy using `list(d.items())`. This matters when processing large caches inside hot loops like message deletion events where it was doing O(N) allocation for every deletion.
**Action:** When finding a single item in a dictionary cache to remove it, iterate keys instead of `list(dict.items())` to save memory and execution time.
