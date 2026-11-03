// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

// Not printed in full: the same vault with the fix, and with a lock instead.
contract OrderedVault {
    mapping(address => uint256) public balance;

    function deposit() external payable {
        balance[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 amount = balance[msg.sender];
        require(amount > 0);
        balance[msg.sender] = 0;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
    }
}

contract LockedVault {
    mapping(address => uint256) public balance;
    bool locked;

    function deposit() external payable {
        balance[msg.sender] += msg.value;
    }

    function withdraw() external {
        require(!locked);
        locked = true;
        uint256 amount = balance[msg.sender];
        require(amount > 0);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balance[msg.sender] = 0;
        locked = false;
    }
}
