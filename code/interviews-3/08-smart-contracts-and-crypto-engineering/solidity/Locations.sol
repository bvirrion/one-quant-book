// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Locations {
    struct Point { uint256 x; }
    Point public p = Point(1);

    function viaMemory() external returns (uint256) {
        Point memory m = p;
        m.x = 2;
        return p.x;
    }

    function viaStorage() external returns (uint256) {
        Point storage s = p;
        s.x = 2;
        return p.x;
    }
}
