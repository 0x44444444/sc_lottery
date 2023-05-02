//SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";

contract Lottery {
    //So 'address payable' is a special type
    //It's like an address type, but it has additional 'transfer' and 'send' members
    //(in addition to 'balance')
    //Denotes an address that you can send Eth to (as opposed to the address of a contract, which may not support it)

    //Array of address payables, public, called 'players'
    //i.e. those entering the lottery
    address payable[] public players;

    uint256 public usdEntryFee;
    AggregatorV3Interface internal ethUSDPriceFeed;

    constructor(address _priceFeedAddress) public {
        //Not going to give this 18 decimals unnecessarily
        //usdEntryFee = 50 * 10e18;
        usdEntryFee = 50;
        ethUSDPriceFeed = AggregatorV3Interface(_priceFeedAddress);
    }

    function enter() public payable {
        //$50 mininum
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

    function startLottery() public {}

    function endLottery() public {}
}
