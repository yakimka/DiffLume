from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from difflume.bank.account import Account
    from difflume.bank.user import User


class AccountAlreadyExistsError(Exception):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        args = args or ("Account already in storage",)
        super().__init__(*args, **kwargs)


class Storage:
    def __init__(self) -> None:
        self._data: dict[Any, list[Account]] = defaultdict(list)

    def add_account(self, user: User, account: Account) -> None:
        if account in self._data[user.id]:
            raise AccountAlreadyExistsError
        self._data[user.id].append(account)

    def get_accounts(self, user: User) -> list[Account]:
        return self._data[user.id]

    def get_account_by_name(self, user: User, account_name: str) -> Account | None:
        for account in self._data[user.id]:
            if account.name == account_name:
                return account
        return None

    def delete_account(self, user: User, account: Account) -> None:
        self._data[user.id].remove(account)
