//SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";

//So, our contract inherits from this?
import "@openzeppelin/contracts/access/Ownable.sol";

//The code for which lives at:
//https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/access/Ownable.sol

//Yes, because we've used the keyword 'is' which causes our contract to inherit from the contract named 'Ownable'.
contract Lottery is Ownable {
    //So 'address payable' is a special type
    //It's like an address type, but it has additional 'transfer' and 'send' members
    //(in addition to 'balance')
    //Denotes an address that you can send Eth to (as opposed to the address of a contract, which may not support it)

    //Array of address payables, public, called 'players'
    //i.e. those entering the lottery
    address payable[] public players;

    uint256 public usdEntryFee;
    AggregatorV3Interface internal ethUSDPriceFeed;

    //An address that will be set to that of whomever deploys the contract, via the constructor
    //address public owner;

    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }

    LOTTERY_STATE public lottery_state;

    constructor(address _priceFeedAddress) public {
        //Set the owner to the deployer of the contract
        //owner = msg.sender;
        //No need, as the contsructor we've inherited from Ownable does this for us
        //as well as instantiating an 'onlyOwner' modifier we can use

        //Not going to give this 18 decimals unnecessarily
        //usdEntryFee = 50 * 10e18;
        usdEntryFee = 50;
        ethUSDPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
    }

    function enter() public payable {
        //$50 mininum
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enough ETH sent.");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUSDPriceFeed.latestRoundData();
        //price is 8 decimal FP USD price for 1 ETH
        //Adjust entry fee to match
        uint256 usdEntryFee8FP = usdEntryFee * 1e8;
        //We want answer in wei, and to avoid underflow to 0 when doing division
        //So, multiple numerator by 1e18
        //Not sure why, but we need to cast the price to unsigned first?
        uint256 uprice = uint256(price);
        uint256 entranceFeeWei = (usdEntryFee8FP * 1e18) / uprice;
        return entranceFeeWei;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Lottery is already running"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        require(lottery_state == LOTTERY_STATE.OPEN, "Lottery is not running");
    }

    function pickWinner() public onlyOwner {
        //How not to source pseudo randomness:
        //Cast to uint256, the hashed value of the abi-encoded tuple of the transaction nonce,
        //sender address, block difficulty and timestamp used to invoke the function
        //Divide by modulo number of players to select one of them
        /* uint256(
            keccack256(
                abi.encodePacked(
                    nonce,
                    msg.sender,
                    block.difficulty,
                    block.timestamp
                )
            )
        ) % players.length; */
    }

    //Apparently we're using the OpenZeppelin version of onlyOwner for this example, rather than our own

    /* modifier onlyOwner() {
        //require function is invoked only by pre-specified address
        require(msg.sender == owner);
        //modified function runs from here
        _;
    } */
}
