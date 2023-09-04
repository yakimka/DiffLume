import asyncio

from difflume.tui.app import DiffLume


async def run() -> None:
    app = DiffLume()
    await app.run_async()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
