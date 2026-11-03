import heapq
import itertools
import pickle
import tempfile


def external_sort(records, memory_items):
    """Sort an iterable holding at most memory_items at a time; yields records in order."""
    runs = []
    it = iter(records)
    while chunk := list(itertools.islice(it, memory_items)):
        chunk.sort()
        run = tempfile.TemporaryFile()
        for r in chunk:
            pickle.dump(r, run)
        run.seek(0)
        runs.append(run)

    def read(f):
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                return

    yield from heapq.merge(*(read(f) for f in runs))
