from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from brownie import Lottery, network, config
import time


def deploy_lottery():
    # development-bs-738
    account = get_account()
    # Return the address of the price feed, be it a local mock, or an on-chain version of the contract
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Deployed Lottery")


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("Lottery Started")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 1
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You have entered the lottery.  Yay.")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # We can't end the lottery without funding the contract with $LINK so we can pay for the random number
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    # Asynchronous process, must wait for call back from the oracle
    time.sleep(60)
    print(f"{lottery.recentWinner()} is the new winner.")
    # tx = lottery.endLottery({"from": account})
    # tx.wait(1)


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
