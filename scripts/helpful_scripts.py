from distutils.command.config import config
from brownie import accounts, network, config, MockV3Aggregator, Contract, VRFCoordinatorV2Mock, network, LinkToken
from web3 import Web3
import time
import web3

DECIMALS = 18
INITIAL_ETH_USD = 2000 * 10**18
GAS_PRICE_LINK = 1e9
BASE_FEE = 100000000000000000

LOCAL_BLOCKCHAIN_ENVS = ['mainnet-fork', 'ganache-local', "mainnet-fork-dev", 'development', 'ganache-local1']
NON_FORKED_LOCAL_BLOCKCHAIN_ENVS = ['ganache-local', 'ganache-local1', 'development']
contracts_to_mock = {
    'eth_usd': MockV3Aggregator,
    'vrf_coordinator': VRFCoordinatorV2Mock,
    'link_token': LinkToken
}

def deploy_mocks(decimals=DECIMALS, initial_eth_usd=INITIAL_ETH_USD):
    account = get_account()
    print(f'The active network is {network.show_active()}')
    print('Deploying mocks...')
    print('-------------------------')
    print('Deploying Link token mock ...')
    link_token = LinkToken.deploy({'from': account})
    print(f'Deployed to {link_token.address}')
    print('Deploying Price feed mock')
    eth_usd = MockV3Aggregator.deploy(decimals, initial_eth_usd, {'from': account})
    print(f'Deployed to {eth_usd.address}')
    vrf_coordinator = VRFCoordinatorV2Mock.deploy(BASE_FEE, GAS_PRICE_LINK, {'from': account})
    print(f'Deployed to {vrf_coordinator.address}')

def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVS:
        return accounts[0]
    return accounts.add(config['wallets']['from_key'])

def get_contract(contract_name):
    contract_type = contracts_to_mock[contract_name]
    if network.show_active() in NON_FORKED_LOCAL_BLOCKCHAIN_ENVS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        try:
            contract_address = config['networks'][network.show_active()][contract_name]
            contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
        except KeyError:
            print(f'{network.show_active()} adddress not found. Perhaps you should add it to the config or deploy mocks?')
            print(f'brownie run scripts/deploy_mocks.py --network {network.show_active()}')
    return contract

def fund_with_link(contract_address, account=None,link_token=None, amount=100000000000000000):
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract('link_token')
    # tx = LinkTokenInterface(link_token.address).transfer(contract_address, amount, {'from': account}) this is without deployment
    tx = link_token.transfer(contract_address, amount, {'from': account, 'gas_limit': 6721975, 'allow_revert': True})
    print(f'Funded 0.1 LINK to address {contract_address}')
    return tx

def listen_for_event(brownie_contract, event, timeout=200, poll_interval=2):
    """Listen for an event to be fired from a contract.
    We are waiting for the event to return, so this function is blocking.
    Args:
        brownie_contract ([brownie.network.contract.ProjectContract]):
        A brownie contract of some kind.
        event ([string]): The event you'd like to listen for.
        timeout (int, optional): The max amount in seconds you'd like to
        wait for that event to fire. Defaults to 200 seconds.
        poll_interval ([int]): How often to call your node to check for events.
        Defaults to 2 seconds.
    """
    Web3.eth.contract
    web3_contract = Web3.eth.contract(
        address=brownie_contract.address, abi=brownie_contract.abi
    )
    start_time = time.time()
    current_time = time.time()
    event_filter = web3_contract.events[event].createFilter(fromBlock="latest")
    while current_time - start_time < timeout:
        for event_response in event_filter.get_new_entries():
            if event in event_response.event:
                print("Found event!")
                return event_response
        time.sleep(poll_interval)
        current_time = time.time()
    print("Timeout reached, no event found.")
    return {"event": None}