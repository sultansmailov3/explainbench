# Surviving generated mutants: manual classification (2026-11-17)

Classified with AI assistance (Claude) by reasoning about the code; confirmed by the author on 2026-11-17.
All five are **equivalent** to their reference for every valid input, so no test can detect them.

| Task | Mutant | Change | Why equivalent |
|---|---|---|---|
| t01_sum_to_n | gen003 | `range(1, n+1)` -> `range(0, n+1)` | the extra iteration adds 0 |
| t06_max_of_list | gen000 | `x > m` -> `x >= m` | on equality `m = x` assigns an equal value |
| t06_max_of_list | gen004 | `xs[1:]` -> `xs[0:]` | the first element is compared with itself; `x > m` is false |
| t09_is_palindrome | gen000 | `i < j` -> `i <= j` | the extra step compares the middle character with itself |
| t19_min_index | gen004 | `range(1, len(xs))` -> `range(0, len(xs))` | `xs[0] < xs[0]` is false |

Consequence: of 128 generated mutants 123 are non-equivalent; the full suite detects 123/123 and the
short suite 104/123 (84.6%).
