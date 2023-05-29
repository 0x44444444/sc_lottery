from brownie import network, accounts, Contract, Lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
)
from scripts.deploy_lottery import deploy_lottery
import pytest, time


def test_can_pick_winner_integration():
    # Integration tests only for non local enviornments
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    lottery = deploy_lottery()
    account = get_account()

    lottery.startLottery({"from": account})

    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1})

    tx = fund_with_link(lottery.address)
    tx.wait(1)
    tx = lottery.endLottery(
        {"from": account, "gas_limit": 12000000, "allow_revert": True}
    )
    time.sleep(120)

    assert lottery.recentWinner() == account
    assert lottery.balance() == 0


# Ironically, integration testing revealed I had the wrong contract address set for goerli LINK
# Had to create this extra test to figure that out
def test_can_fund_with_link_integration():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    account = get_account()
    # lottery = Contract("0xaF12BD515C4553145c0d2AFAc2fCBfE6c94e969f")
    # lottery = Contract("0x6A1C57C06D9e0CE92FcaA09415B16c6f1cC3E7D2")
    lottery = Lottery[-1]
    print(f"Using the previously deployed lottery at: {lottery.address}")

    tx = fund_with_link(lottery.address)


def test_can_end_lottery_integration():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    # So this is failing because we're not setting the fee high enough (from the config file, or passing in when making the call)
    # Formula is: Gas price x (Verification gas + Callback gas limit + Wrapper gas overhead)
    # For Sepolia (https://docs.chain.link/vrf/v2/direct-funding/supported-networks) values are:
    # Verification gas (same thing as 'Coordinator Gas Overhead): 90000
    # Callback gas limit (arbitrary?): 100000
    # Wrapper gas overhead: 40000
    # Gas is about 7 wei on Sepolia (or 0.000000008 gwei)
    # 0.000000008 *(230000) = 1610000 wei, or essentially zero.  But not quite.
    # Convert to LINK via: https://data.chain.link/ethereum/mainnet/crypto-eth/link-eth?_ga=2.110621766.2138183752.1684777753-2139637652.1666701572
    # 0.00349654 is the LINK/ETH exchange rate
    # So 0 / 0.00349654 = a tiny amount of LINK
    # Add the LINK premium, 0.25, for a total of 0.2500000000000001 or something stupid.
    # Modifying fee accoridingly by adding a bit.

    account = get_account()
    # lottery = Contract("0x6A1C57C06D9e0CE92FcaA09415B16c6f1cC3E7D2")
    lottery = Lottery[-1]
    print(f"Using the previously deployed lottery at: {lottery.address}")
    tx = lottery.endLottery(
        {"from": account, "gas_limit": 12000000, "allow_revert": True}
    )
    time.sleep(120)

    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
