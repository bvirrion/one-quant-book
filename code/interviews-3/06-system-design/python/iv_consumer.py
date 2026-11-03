"""A consumer of a log that can crash at any step. The state and the offset are durable."""


class Crash(Exception):
    pass


def consume(log, mode, crash_at):
    """Runs until the log is done, restarting after each crash. Returns the state."""
    state, offset, steps = 0, 0, 0
    crashes = set(crash_at)

    def step():
        nonlocal steps
        steps += 1
        if steps in crashes:
            raise Crash

    while offset < len(log):
        try:
            step()
            if mode == "atomic":             # one transaction holds both, or neither
                state, offset = state + log[offset], offset + 1
            elif mode == "apply_first":
                state += log[offset]
                step()
                offset += 1
            else:
                offset += 1
                step()
                state += log[offset - 1]
        except Crash:
            pass                             # a restart reads the durable state and offset
    return state
