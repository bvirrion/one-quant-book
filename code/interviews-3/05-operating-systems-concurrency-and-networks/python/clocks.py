import time

print(time.clock_getres(time.CLOCK_MONOTONIC))
last = time.monotonic_ns()
backwards = 0
for _ in range(200_000):
    now = time.monotonic_ns()
    backwards += now < last
    last = now
print(backwards)
