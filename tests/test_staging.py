from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVS,
    get_account,
    get_contract,
    listen_for_event,
)
from brownie import network, exceptions, VRFConsumerV2, config
from brownie.network.gas.strategies import LinearScalingStrategy
import pytest
from web3 import Web3


def test_can_get_eth_price():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip()
    # Arrange
    account = get_account()
    price_feed = get_contract("eth_usd")
    # Act
    price = price_feed.latestRoundData()
    # Assert
    assert isinstance(price[1], int)
    assert price[1] > 0


def test_can_get_entrance_fee(lottery_contract):
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip()
    # Arrange
    # Act
    expected_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery_contract.getEntranceFee()
    # Assert
    assert expected_fee > entrance_fee


def test_cant_enter_if_not_enough_entry_fee(lottery_contract):
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip()
    account = get_account()
    # Act
    print(lottery_contract.getEntranceFee())
    # lottery_contract.startNew({"from": account, 'gas_limit': 6721975, 'allow_revert': True})
    # Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery_contract.enterRaffle({"from": account, "value": 20, 'gas_limit': 6721975, 'allow_revert': True})

def test_can_enter_lottery(lottery_contract):
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip()
    account1 = get_account()
    # account2 = get_account(index=2)
    # account3 = get_account(index=3)
    # Act
    # lottery_contract.startNew()
    lottery_contract.enterRaffle({"from": account1, "value": 50, 'gas_limit': 6721975, 'allow_revert': True})
    # lottery_contract.enter({"from": account2, "value": 50})
    # lottery_contract.enter({"from": account3, "value": 50})
    players = lottery_contract.getPlayer(0)
    # Assert
    assert len(players) == 42
    assert lottery_contract.getRaffleState() == 0


def test_can_check_upkeep(lottery_contract):
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip()
    account1 = get_account()
    # account2 = get_account(index=2)
    # account3 = get_account(index=3)
    # lottery_contract.startNew({"from": account1})
    lottery_contract.enterRaffle({"from": account1, "value": 50, 'gas_limit': 6721975, 'allow_revert': True})
    # lottery_contract.enter({"from": account2, "value": 50})
    # lottery_contract.enter({"from": account3, "value": 50})
    # fund_with_link(lottery_contract.address)
    upkeep_needed, perform_data = lottery_contract.checkUpkeep("")
    # Assert
    assert isinstance(upkeep_needed, bool)
    assert isinstance(perform_data, bytes)


def test_can_request_random_number():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip()
    # Arrange
    account = get_account()
    # subscription_id = create_subscription()
    # fund_subscription(subscription_id=subscription_id)
    subscription_id = config['networks'][network.show_active()]['subscription_id']
    vrf_coordinator = get_contract("vrf_coordinator")
    link_token = get_contract("link_token")
    keyhash = config["networks"][network.show_active()]["keyhash"]
    vrf_consumer = VRFConsumerV2.deploy(
        subscription_id,
        vrf_coordinator,
        link_token,
        keyhash,
        {"from": account, "gas_limit": 6721975, "allow_revert": True},
    )
    # Act
    tx = vrf_consumer.requestRandomWords({"from": account, 'gas_limit': 6721975, 'allow_revert': True})
    tx.wait(1)
    request_id = tx.events[0]["request_id"]
    # Assert
    assert isinstance(request_id, int)


def test_returns_random_number_testnet():
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        pytest.skip("Only for testnet testing")
    # # Arrange
    # gas_strategy = LinearScalingStrategy("1 gwei", "5000000 gwei", 1.1)
    # gas_price(gas_strategy)
    account = get_account()
    subscription_id = config['networks'][network.show_active()]['subscription_id']
    gas_lane = config["networks"][network.show_active()]["keyhash"]
    vrf_coordinator = get_contract("vrf_coordinator")
    link_token = get_contract("link_token")
    vrf_consumer = VRFConsumerV2.deploy(
        subscription_id,
        vrf_coordinator,
        link_token,
        gas_lane,
        {"from": account, 'gas_limit': 6721975, 'allow_revert': True},
    )
    tx = vrf_coordinator.addConsumer.transact(
        subscription_id, vrf_consumer.address, {"from": account, "gas_limit": 6721975, "allow_revert": True}
    )
    tx.wait(1)

    # Act
    tx = vrf_consumer.requestRandomWords({"from": account, 'gas_limit': 6721975, 'allow_revert': True})
    tx.wait(1)
    event_response = listen_for_event(vrf_consumer, "ReturnedRandomness")

    # Assert
    assert event_response.event is not None
    assert vrf_consumer.s_randomWords(0) > 0
    assert vrf_consumer.s_randomWords(1) > 0
