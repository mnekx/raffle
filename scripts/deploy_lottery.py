from brownie import Raffle, network, config
from scripts.helpful_scripts import get_account, get_contract
from scripts.vfr_scripts.create_subscription import create_subscription

'''
address _vrfCoordinatorV2,
uint64 _subscriptionId,
bytes32 _gasLane, // keyHash
uint256 _interval,
uint256 _entranceFee,
uint32 _callbackGasLimit
'''

def deploy_lottery(entrance_fee=50):
    account = get_account()
    print('Deploying contract...')
    vrf_coordinator = get_contract('vrf_coordinator')
    subscription_id = config['networks'][network.show_active()]['subscription_id']
    keyhash = config['networks'][network.show_active()]['keyhash']
    interval = 5 # 5 seconds
    # entrance_fee = entry_fee if entry_fee else  # 50USD worth of eth
    gas_limit = 1000000000
    # eth_usd_feed_address = get_contract('eth_usd').address;
    lotter_contract = Raffle.deploy(
        vrf_coordinator.address, 
        subscription_id,
        keyhash,
        interval,
        entrance_fee,
        gas_limit,
        # eth_usd_feed_address,
        {'from': account}, publish_source=config['networks'][network.show_active()]['verify'])
    print(f'contract deployed at {lotter_contract.address}')
    return lotter_contract

def main():
    deploy_lottery()