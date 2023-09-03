from uuid import UUID

from difflume.bank.account import Transaction, TransactionType


def test_create_deposit():
    result = Transaction.deposit(amount=1_00)

    assert isinstance(result.id, UUID)
    assert result.type == TransactionType.DEPOSIT
    assert int(result) == 1_00


def test_create_withdraw():
    result = Transaction.withdraw(amount=1_00)

    assert isinstance(result.id, UUID)
    assert result.type == TransactionType.WITHDRAW
    assert int(result) == -1_00
