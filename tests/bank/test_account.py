import pytest

from difflume.bank.account import AccountError, NotEnoughMoneyError


def test_account_init_balance(account):
    assert account.balance == 0


def test_balance_after_deposit(account):
    account.deposit(100_00)

    assert account.balance == 100_00


def test_balance_after_withdraw(account):
    account.deposit(100_00)
    account.withdraw(50_00)

    assert account.balance == 50_00


def test_balance_after_withdraw_not_enough_money(account):
    account.deposit(100_00)

    with pytest.raises(AccountError):
        account.withdraw(200_00)

    assert account.balance == 100_00


def test_withdraw_not_enough_money_error(account):
    account.deposit(100_00)

    with pytest.raises(NotEnoughMoneyError, match="Not enough money"):
        account.withdraw(200_00)
