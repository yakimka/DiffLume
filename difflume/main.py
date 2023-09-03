import asyncio

from difflume.diffapp.modules import FSModule
from difflume.tui.app import DiffLume


async def main() -> None:
    left_module = FSModule("data/me-old.json")
    right_module = FSModule("data/me-current.json")
    await left_module.read()
    await right_module.read()

    app = DiffLume(
        left_module=left_module,
        right_module=right_module,
    )
    await app.run_async()


if __name__ == "__main__":
    main()
    asyncio.run(main())
