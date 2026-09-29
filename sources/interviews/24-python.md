# 24. Python — brief and source ledger

## Brief

- **Hook.** A helper that appends each fill to a default list argument works in the unit test and doubles every position by the end of the first live day. The candidate asked about it in an interview has twenty seconds to say why the list was shared, and another minute to say how he would have found it without being told.
- **Sections.** The data model: names, objects, mutability and the special methods; Iterators, generators and context managers; The interpreter lock, threads, processes and async; The numerical stack: vectorisation, views and copies, dtypes and performance.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** global interpreter lock (B15.8), interpreter overhead (B15.8), array programming (B15.8), process-based parallelism (B15.8), chunked processing (B15.8), window function (B15.10), Welford's algorithm (B4.25), output-prediction question (ch22).
- **Question bank.** 13 questions, 4/5/4. Families: output prediction (mutable default arguments; late-binding closures in a loop; is against ==; integer caching left as implementation detail, stated; a generator consumed twice; dict ordering and mutation during iteration) -- each run and asserted, with the CPython 3.10 behaviour stated where it is an implementation detail; write a generator pipeline for a large file with constant memory; a context manager that restores state on error; the interpreter lock (what threads speed up and what they do not, numeric on a counted workload, never timed); numpy views against copies (which operations copy; a silent chained-assignment bug in pandas); vectorise a loop (a rolling statistic with cumulative sums, checked against the loop); floating-point summation (math.fsum against sum on a planted case). Roles: researcher 5, developer 5, mle 3. Firms: systematic fund 4, market maker 3, multi-manager fund 2, bank 1, any 3.
- **Facts to verify.** The Python Language Reference and Library Reference for 3.10 (the pinned interpreter), and the notes where 3.12 behaves differently (CI's system python is not the test interpreter); numpy and pandas documentation for view and copy semantics at the pinned versions (pandas 2.3 copy-on-write status).
- **Data.** Figures: none planned. Code: python/iv_py.py (coding answers), python/snippets/*.py (output-prediction snippets); tests run each snippet in a subprocess with the venv interpreter and assert stdout; vectorised answers asserted equal to the loop over seeds.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | CPython keeps a single object for each integer in [-5, 256] (implementation detail of PyLong_FromLong) | Python C API documentation, Integer Objects | https://docs.python.org/3.10/c-api/long.html | 2026-09-29 | "The current implementation keeps an array of integer objects for all integers between -5 and 256" (behaviour asserted by the identity snippet) | solution iq 3 |
| F2 | pandas copy-on-write: under CoW chained assignment never works (use .loc); CoW announced as the default for pandas 3.0 | pandas user guide, Copy-on-Write | https://pandas.pydata.org/pandas-docs/version/2.3/user_guide/copy_on_write.html | 2026-09-29 | "Copy-on-Write will become the default in pandas 3.0"; "Chained assignment will never work" | solution iq 12 |

## EXCLUDED

