import pytest
from scripts.deploy_lottery import deploy_lottery

@pytest.fixture()
def lottery_contract():
    return deploy_lottery()