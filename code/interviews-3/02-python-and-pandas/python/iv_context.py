from contextlib import contextmanager


class Held:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        self.log.append("acquire")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.log.append("release")
        return False                  # True would swallow the exception


@contextmanager
def held(log):
    log.append("acquire")
    try:
        yield
    finally:
        log.append("release")
