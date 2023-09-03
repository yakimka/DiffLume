from typing import Type

import pytest

from difflume.bank.account import Account
from difflume.bank.user import User


@pytest.fixture()
def make_user() -> Type[User]:
    return User


@pytest.fixture()
def user(make_user):
    return make_user(
        name="John Doe",
    )


@pytest.fixture()
def account():
    return Account(name="default")
