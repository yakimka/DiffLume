import pytest

from difflume.bank.account import Account
from difflume.bank.storage import AccountAlreadyExistsError, Storage


@pytest.fixture()
def storage():
    return Storage()


def test_add_account(storage, user, account):
    storage.add_account(user, account)

    assert storage.get_accounts(user) == [account]


def test_delete_account(storage, user, account):
    storage.add_account(user, account)
    storage.delete_account(user, account)

    assert storage.get_accounts(user) == []


def test_unknown_user_accounts(storage, user):
    result = storage.get_accounts(user)

    assert result == []


def test_get_account_by_name(storage, user):
    account = Account(name="jar")
    storage.add_account(user, account)

    result = storage.get_account_by_name(user, "jar")

    assert result == account


def test_get_unknown_account_by_name(storage, user):
    result = storage.get_account_by_name(user, "jar")

    assert result is None


def test_cant_add_same_account_twice(storage, user, account):
    storage.add_account(user, account)

    with pytest.raises(AccountAlreadyExistsError, match="Account already in storage"):
        storage.add_account(user, account)
