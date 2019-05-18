
import asyncio
import random

# ANSI colors
c = (
    "\u001b[30m",     # black
    "\u001b[31m",      # red
    "\u001b[32m",     # green
    "\u001b[33m",    # yellow
    "\u001b[34m",      # blue
    "\u001b[35m",   # magenta
    "\u001b[36m",      # cyan
    "\u001b[37m",     # white
    "\u001b[0m",      # reset
)


async def makerandom(idx: int, threshold: int = 6) -> int:
    print(c[idx + 1+ 2*idx] + f"Initiated makerandom({idx}).")
    i = random.randint(0, 10)
    while i <= threshold:
        print(c[idx + 1 + 2*idx] + f"makerandom({idx}) == {i} too low; retrying.")
        await asyncio.sleep(idx + 1)
        i = random.randint(0, 10)
    print(c[idx + 1 + 2*idx] + f"---> Finished: makerandom({idx}) == {i}" + c[0])
    return i


async def main():
    res = await asyncio.gather(*(makerandom(i, 10 - i - 1) for i in range(3)))
    return res

if __name__ == "__main__":
    random.seed(444)
    loop = asyncio.get_event_loop()
    r = loop.run_until_complete(main())
    #  r1, r2, r3 = asyncio.run(main())
    print()
    print(f"r1: {r[0]}, r2: {r[1]}, r3: {r[2]}")
