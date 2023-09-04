import asyncio

from difflume.diffapp.modules import FSModule
from difflume.tui.app import DiffLume


async def main() -> None:
    left_module = FSModule("data/me-old.json")
    right_module = FSModule("data/me-current.json")

    app = DiffLume(
        left_module=None,
        right_module=None,
    )
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
