// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Slot {
    uint256 public v;

    function set(uint256 x) external {
        v = x;
    }
}

contract SlotTwice {
    uint256 public v;

    function twice(uint256 a, uint256 b) external returns (uint256 first, uint256 second) {
        uint256 g0 = gasleft();
        v = a;
        uint256 g1 = gasleft();
        v = b;
        uint256 g2 = gasleft();
        first = g0 - g1;
        second = g1 - g2;
    }
}
