// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Loose {
    uint128 a = 1;
    uint256 b = 2;
    uint128 c = 3;
}

contract Tight {
    uint128 a = 1;
    uint128 c = 3;
    uint256 b = 2;
}
