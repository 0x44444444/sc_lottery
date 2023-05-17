from brownie import (
    network,
    config,
    accounts,
    MockV3Aggregator,
    Contract,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)
from web3 import Web3

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
DECIMALS = 8
STARTING_PRICE = 200000000000


# See https://github.com/PatrickAlphaC/smartcontract-lottery/blob/main/contracts/test/VRFCoordinatorMock.sol
# And https://vrf.chain.link/goerli
# Slightly modified version, not quite as per the tutorial
def get_account(index=None, id=None):

    if index:
        # Allows us to grab an arbitrary account from brownie/ganache
        return accounts[index]
    if id:
        # Not putting private keys in a .env, so ignoring this one
        # return brownie.accounts.add(brownie.config["wallets"]["from_key"])
        # return accounts.load("development-bs-738")
        return accounts.load(id)
    # Figure out if we're using a real network and need a private key, or whether just to use the first accounnt in ganache
    if (network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS) or (
        network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]


# Mapping of contract names to contract types
# Note that the contract type isn't just the name of the type, it is a ContractContainer object, containing instances of all
# previously deployed contracts of the type in question that Brownie knows about.
# string => ContractContainer
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}

# We've pulled these contracts from: https://github.com/smartcontractkit/chainlink-mix
# (which are set up to work with this tutorial)
# But could just as easily have been:
# https://github.com/smartcontractkit/chainlink/tree/develop/contracts/src/v0.6/tests


def get_contract(contract_name):
    """Returns the contract address from brownie-config.yaml (if defined) for a given contract name.
    Otherwise deploys a mock verison of the contract, and returns the address of that

    Args:
        contract_name(string)

    Returns:
        brownie.network.contract.ProjectContract:  The most recently deployed version of this contract,
        as per Brownie's store of such
    """
    # contract_type is of type ContractContainer
    # 'contract_type' is a shitty variable name, changing it to something meaningful
    mock_container = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # If Brownie's contract container (list-ish) for this type of contract is empty, we need to deploy a mock
        if len(mock_container) <= 0:
            deploy_mocks()
        # I don't like this, we're just assuming the deployment of the mock succeeded.
        # Would prefer to return the contract from the deploy_mocks() function and check the return value is valid
        # But then, the deploy_mocks() function is now deploying more than one mock (rather than one function call for each)
        contract = mock_container[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # With the address of a deployed contract, and the ABI, we can create a ProjectContract object
        # ContractContainer -> deployed -> ProjectContract
        # ContractContainer is a list(ish) of previously deployed ProjectContracts (and their associated attributes)
        # As all of the deployed contracts are identical, the attributes on the ContractContainer are also identical
        # So, changing the code changes the type of the contract as far as Brownie is concerned?
        contract_abi = mock_container.abi
        # Pull a ProjectContract object corresponding to a previously deployed on-chain version
        # Presumably this assumes that the version we've imported into Brownie matches the version that
        # (someone else) deployed on chain.
        contract = Contract.from_abi(
            mock_container._name, contract_address, contract_abi
        )
    return contract


def deploy_mocks(decimals=DECIMALS, initial_value=STARTING_PRICE):
    # If we're deploying mocks, is it not always the case that account is going to be account[0]
    # UCalling get_account() seems redundant at best

    account = get_account()
    MockV3Aggregator.deploy(
        decimals,
        initial_value,
        {"from": account},
    )
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    # Apparently we're not doing this via a return value
    # return mock_price_feed
    # Presumably because we're not deploying more than one mock
    print("Mocks deployed")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=260000000000000000
):
    # Python weirdness
    # Means 'if account, account = account, else account = get_account()
    account = account if account else get_account()
    # Grab a link_token contract object
    link_token = link_token if link_token else get_contract("link_token")
    # So, oddly, the transfer function is owned by the token contract and not the address of the account
    # from which the $LINK will be transferred?
    # transfer(destination, amount, source)
    # Yes, because the function is being called by the msg.sender to make the transfer...

    tx = link_token.transfer(contract_address, amount, {"from": account})

    # If we don't have the full contract source code available and imported into Brownie
    # but we do have the interface (see 'interfaces') we can do the following instead
    # as the interface will compile down to a compliant ABI for accessing the contract
    # at the address in question.
    # So, this is like having the address of a contract, with no source, but an interface has been made available

    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})

    tx.wait(1)
    print("Contract funded")
    return tx


# So.  If you have the abi for an existing contract, but not the source:
#
# contract = Contract.from_abi(
#            contract_name, contract_address, contract_abi
#        )
#
# Or, if you have the interface, but not the source:
#
# contract = interface.[NameOfInterface](contract_address)
#
