// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Wallet {
    address owner;

    constructor() payable { owner = msg.sender; }

    function sendAllByOrigin(address payable to) external {
        require(tx.origin == owner);
        to.transfer(address(this).balance);
    }

    function sendAllBySender(address payable to) external {
        require(msg.sender == owner);
        to.transfer(address(this).balance);
    }
}

contract Trap {
    function claimPrize(Wallet w, bool byOrigin) external {
        address payable me = payable(address(this));
        if (byOrigin) w.sendAllByOrigin(me);
        else w.sendAllBySender(me);
    }

    receive() external payable {}
}
