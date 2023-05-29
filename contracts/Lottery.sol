//SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
//import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

//So, our contract inherits from this?
import "@openzeppelin/contracts/access/Ownable.sol";

//Using Chainlink for randomness
//OK, so the on-chain version on Sepolia is VRFConsumerBaseV2.sol
//Which is likely why there's a reversion when attempting to get randomness
//Can we switch to V2 without screwing everything up?
//Entails switching to solidity 0.8.4 minimum rather than 0.6.6.
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

//Will either have to rewrite this using VRFV2WrapperConusmer base as per:
//https://docs.chain.link/vrf/v2/direct-funding/examples/get-a-random-number
//Or just test on Rinkeby
//Which doesn't appear to be active.  So, refactor.
//Actually, there appears to be a v1 VRF on goerli...

//The code for which lives at:
//https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/access/Ownable.sol

//Yes, because we've used the keyword 'is' which causes our contract to inherit from the contract named 'Ownable'.
//Furthermore, we're now also inheriting from 'VRFConsumerBase' at the same time?
contract Lottery is VRFConsumerBase, Ownable {
    //So 'address payable' is a special type
    //It's like an address type, but it has additional 'transfer' and 'send' members
    //(in addition to 'balance')
    //Denotes an address that you can send Eth to (as opposed to the address of a contract, which may not support it)

    //Array of address payables, public, called 'players'
    //i.e. those entering the lottery
    address payable[] public players;

    address payable public recentWinner;
    uint256 public randomness;

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

    uint256 public oracle_fee;
    bytes32 public oracle_keyhash;

    //Adding a event.  Events are like structured logging output from the blockchain.
    //They're not directly accessible by contracts.
    //This is almost like defining a type (i.e. the structure of the event is, in this case, just a bytes32 but could be something else)
    event RequestedRandomness(bytes32 requestId);

    //We can actually hit the constructor of a parent contract by mentioning it explicitly here
    //And even pass along the parameters we pass into our constructor, into the constructor of the parent contract
    //thusly, with the address of the vrf coordinator, and address of the version of LINK we're using (testnet or otherwise)
    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _linkToken,
        uint256 _oracle_fee,
        bytes32 _oracle_keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _linkToken) {
        //Set the owner to the deployer of the contract
        //owner = msg.sender;
        //No need, as the contsructor we've inherited from Ownable does this for us
        //as well as instantiating an 'onlyOwner' modifier we can use

        //Not going to give this 18 decimals unnecessarily
        //usdEntryFee = 50 * 10e18;
        usdEntryFee = 50;
        ethUSDPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        oracle_fee = _oracle_fee;
        oracle_keyhash = _oracle_keyhash;
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

        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        //The definition of this function has 'returns (bytes32 requestId) in it, so we don't need
        //to explicitly do:
        //bytes32 whatever = requestRandomness(oracle_keyhash, oracle_fee);
        //Note that this is an asynchronous process
        //So, we make the request, and we have a handler function somwhere that the oracle will hit up
        //when it delivers the random number
        bytes32 requestId = requestRandomness(oracle_keyhash, oracle_fee);
        emit RequestedRandomness(requestId);
    }

    //So, the parent contract VRFConsumerBase has the stub of a definition for this, tagged 'virtual'
    //which means that when we inherit it, we have to populate it with a function that actually does something via the 'override' keyword
    //Scope is 'internal' which allows calls from this contract or contracts deriving from it (i.e. deriving from VRFConsumerBase,
    //which this contract obviously does, since it is our parent)
    //Don't want anyone calling this function and supplying spurious randomness
    function fulfillRandomness(
        bytes32 _requestid,
        uint256 _randomness
    ) internal override {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "Not in the process of calculating a result"
        );
        require(_randomness > 0, "no randomness provided");
        //modulo divide randomness to get an index
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        //transfer the funds to the winner
        recentWinner.transfer(address(this).balance);
        //reset the lottery
        //Wipe out the existing array of payable addresses
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }

    //function pickWinner() public onlyOwner {
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
    // }

    //Apparently we're using the OpenZeppelin version of onlyOwner for this example, rather than our own

    /* modifier onlyOwner() {
        //require function is invoked only by pre-specified address
        require(msg.sender == owner);
        //modified function runs from here
        _;
    } */
}
