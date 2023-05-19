from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account
from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest


def test_get_entrance_fee():
    # Unit tests only for local development
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    # Is Arrange, Act, Assert
    # (not the same thing as Checks, Effect, Interactions)
    #
    # Arrange
    #
    lottery = deploy_lottery()
    #
    # Act
    #
    # We deployed the mock oracle with an eth value of $2000
    # $50 / $2000 = 0.025 eth
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    #
    # Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    # Unit tests only for local development
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    # Arrange
    account = get_account()
    lottery = deploy_lottery()
    value = lottery.getEntranceFee()

    # Act/Assert
    # All is well if we raise the exception shown (try/catch)
    with (pytest.raises(exceptions.VirtualMachineError)):
        lottery.enter({"from": account, "value": value})


def test_can_start_and_enter_lottery():
    # Unit tests only for local development
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip

    # Arrange
    account = get_account()
    lottery = deploy_lottery()
    value = lottery.getEntranceFee()

    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": value})

    # Assert
    # What pieces of state should we have?
    # The lottery state, and the player count
    assert lottery.players(0) == account
    # print("here")
    # print(f"lottery_state is {lottery.lottery_state()}")
    # Enum type, first option 'OPEN' would be 0
    assert lottery.lottery_state() == 0
