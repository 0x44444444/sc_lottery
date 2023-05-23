from brownie import network, accounts, Contract
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
    tx = lottery.endLottery({"from": account})
    time.sleep(60)

    assert lottery.recentWinner() == account
    assert lottery.balance() == 0


# Ironically, integration testing revealed I had the wrong contract address set for goerli LINK
# Had to create this extra test to figure that out
def test_can_fund_with_link_integration():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    account = get_account()
    lottery = Contract("0xaF12BD515C4553145c0d2AFAc2fCBfE6c94e969f")
    tx = fund_with_link(lottery.address)
