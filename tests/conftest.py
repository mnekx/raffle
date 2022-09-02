import pytest
from brownie import Raffle

from scripts.deploy_lottery import deploy_lottery

@pytest.fixture()
def lottery_contract():
    raffle_contract = Raffle[-1] if len(Raffle) > 0 else deploy_lottery()
    return raffle_contract