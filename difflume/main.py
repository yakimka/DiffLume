import asyncio

from difflume.tui.app import DiffLume


async def main() -> None:
    app = DiffLume()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
