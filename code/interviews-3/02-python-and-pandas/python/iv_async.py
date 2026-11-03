import asyncio


async def heartbeat(log):
    for _ in range(3):
        log.append("beat")
        await asyncio.sleep(0)


def blocking_work(log):
    log.append("work")


async def handler_blocks(log):
    for _ in range(3):
        blocking_work(log)            # no await: nothing else can run during this


async def handler_yields(log):
    for _ in range(3):
        await asyncio.to_thread(blocking_work, log)


async def main(handler):
    log = []
    await asyncio.gather(heartbeat(log), handler(log))
    return log
