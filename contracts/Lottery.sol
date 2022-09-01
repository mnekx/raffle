// SPDX-License-Identifier: MIT

pragma solidity ^0.8.7;

import '@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol';
import '../interfaces/VRFCoordinatorV2Interface.sol';
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";

import "@chainlink/contracts/src/v0.8/interfaces/KeeperCompatibleInterface.sol";

contract Lottery is VRFConsumerBaseV2, KeeperCompatibleInterface{

    /* State variables */
    // Chainlink VRF Variables
    VRFCoordinatorV2Interface private immutable vrfCoordinator;
    AggregatorV3Interface private immutable ethUsdPriceFeed;
    uint64 private immutable subscriptionId;
    bytes32 private immutable gasLane;
    uint32 private immutable callbackGasLimit;
    uint16 private constant REQUEST_CONFIRMATIONS = 3;
    uint32 private constant NUM_WORDS = 1;

    // lottery variables
    enum LOTTERY_STATE {Open, Close, CalculatingWinner}
    LOTTERY_STATE private State;
    address payable[] private players;
    uint256 private immutable interval;
    uint256 private immutable entranceFee;
    uint256 private lastTimeStamp;
    address payable private recentWinner;

    // Errors
    error Raffle__UpkeepNotNeeded(uint256 currentBalance, uint256 numPlayers, uint256 State);
    error Raffle__TransferFailed();
    error Raffle__SendMoreToEnterRaffle();
    error Raffle__RaffleNotOpen();

    /* Events */
    event RequestedRaffleWinner(uint256 indexed requestId);
    event RaffleEnter(address indexed player);
    event WinnerPicked(address indexed player);

    error NotEnoughEntryFee();
    error LotteryIsNotOpen();
    error CanNotStartNew();

    constructor(
        address _vrfCoordinatorV2,
        uint64 _subscriptionId,
        bytes32 _gasLane, // keyHash
        uint256 _interval,
        uint256 _entranceFee,
        uint32 _callbackGasLimit,
        address _ethUsdFeedAddress
    ) VRFConsumerBaseV2(_vrfCoordinatorV2) {
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinatorV2);
        gasLane = _gasLane;
        interval = _interval;
        subscriptionId = _subscriptionId;
        entranceFee = _entranceFee;
        State = LOTTERY_STATE.Close;
        lastTimeStamp = block.timestamp;
        callbackGasLimit = _callbackGasLimit;
        ethUsdPriceFeed = AggregatorV3Interface(_ethUsdFeedAddress);
    }

    function enter() public payable{
        if(msg.value < entranceFee ) {
            revert NotEnoughEntryFee();
        }
        if(State != LOTTERY_STATE.Open) {
            revert LotteryIsNotOpen();
        }
        players.push(payable(msg.sender));
    }

    function startNew() external {
        if(State != LOTTERY_STATE.Close ) {
            revert CanNotStartNew();
        }
        State = LOTTERY_STATE.Open;
    }

    function getEntranceFeeInEther() public view returns(uint256) {
        (
            ,
        int256 price,
        ,
        ,
        ) = ethUsdPriceFeed.latestRoundData();

        // 50 usd worth of eth is the entry fee
        return (entranceFee * 10**18) / (uint256(price) * 10**10);
    }

    /**
     * @dev This is the function that the Chainlink Keeper nodes call
     * they look for `upkeepNeeded` to return True.
     * the following should be true for this to return true:
     * 1. The time interval has passed between raffle runs.
     * 2. The lottery is open.
     * 3. The contract has ETH.
     * 4. Implicity, your subscription is funded with LINK.
     */
    function checkUpkeep(
        bytes memory /* checkData */
    )
        public
        view
        override
        returns (
            bool upkeepNeeded,
            bytes memory /* performData */
        )
    {
        bool isOpen = LOTTERY_STATE.Open == State;
        bool timePassed = ((block.timestamp - lastTimeStamp) > interval);
        bool hasPlayers = players.length > 0;
        bool hasBalance = address(this).balance > 0;
        upkeepNeeded = (timePassed && isOpen && hasBalance && hasPlayers);
        return (upkeepNeeded, "0x0"); // can we comment this out?
    }

    /**
     * @dev Once `checkUpkeep` is returning `true`, this function is called
     * and it kicks off a Chainlink VRF call to get a random winner.
     */
    function performUpkeep(
        bytes calldata /* performData */
    ) external override {
        (bool upkeepNeeded, ) = checkUpkeep("");
        // require(upkeepNeeded, "Upkeep not needed");
        if (!upkeepNeeded) {
            revert Raffle__UpkeepNotNeeded(
                address(this).balance,
                players.length,
                uint256(State)
            );
        }
        State = LOTTERY_STATE.CalculatingWinner;
        uint256 requestId = vrfCoordinator.requestRandomWords(
            gasLane,
            subscriptionId,
            REQUEST_CONFIRMATIONS,
            callbackGasLimit,
            NUM_WORDS
        );
        // Quiz... is this redundant?
        emit RequestedRaffleWinner(requestId);
    }

    /**
     * @dev This is the function that Chainlink VRF node
     * calls to send the money to the random winner.
     */
    function fulfillRandomWords(
        uint256, /* requestId */
        uint256[] memory randomWords
    ) internal override {
        // s_players size 10
        // randomNumber 202
        // 202 % 10 ? what's doesn't divide evenly into 202?
        // 20 * 10 = 200
        // 2
        // 202 % 10 = 2
        uint256 indexOfWinner = randomWords[0] % players.length;
        address payable _recentWinner = players[indexOfWinner];
        recentWinner = _recentWinner;
        // Reset
        players = new address payable[](0);
        State = LOTTERY_STATE.Close;
        lastTimeStamp = block.timestamp;
        (bool success, ) = recentWinner.call{value: address(this).balance}("");
        // require(success, "Transfer failed");
        if (!success) {
            revert Raffle__TransferFailed();
        }
        emit WinnerPicked(recentWinner);
    }

    function getPlayers() public view returns(address payable[] memory) {
        return players;
    }

    function getRecentWinner() public view returns(address payable) {
        return recentWinner;
    }

    function getState() public view returns(uint16) {
        return uint16(State);
    }
}