from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AccountError(Exception):
    pass


class NotEnoughMoneyError(AccountError):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        args = args or ("Not enough money",)
        super().__init__(*args, **kwargs)


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


@dataclass
class Transaction:
    id: UUID
    type: TransactionType
    amount: int

    def __int__(self) -> int:
        if self.type == TransactionType.WITHDRAW:
            return self.amount * -1
        return self.amount

    @classmethod
    def deposit(cls, amount: int) -> Transaction:
        return cls(id=uuid4(), type=TransactionType.DEPOSIT, amount=amount)

    @classmethod
    def withdraw(cls, amount: int) -> Transaction:
        return cls(id=uuid4(), type=TransactionType.WITHDRAW, amount=amount)


class Account:
    def __init__(self, *, name: str) -> None:
        self.name = name
        self._transactions: list[Transaction] = []

    @property
    def balance(self) -> int:
        return sum(int(tr) for tr in self._transactions)

    def deposit(self, amount: int) -> None:
        self._transactions.append(Transaction.deposit(amount))

    def withdraw(self, amount: int) -> None:
        if self.balance < amount:
            raise NotEnoughMoneyError
        self._transactions.append(Transaction.withdraw(amount))
