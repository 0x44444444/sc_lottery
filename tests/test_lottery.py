from brownie import Lottery, accounts, config, network
from web3 import Web3


def test_entry_price():
    # If ETH was worth $1500, $50 would be this in wei:
    sane_ceiling_wei = Web3.toWei(0.033, "ether")
    # 33000000000000000
    # If ETH was worth $2500:
    sane_floor_wei = Web3.toWei(0.02, "ether")
    account = accounts[0]
    price_feed_address = config["networks"][network.show_active()]["eth_usd_price_feed"]
    lottery = Lottery.deploy(price_feed_address, {"from": account})
    assert lottery.getEntranceFee() > sane_floor_wei
    assert lottery.getEntranceFee() < sane_ceiling_wei
