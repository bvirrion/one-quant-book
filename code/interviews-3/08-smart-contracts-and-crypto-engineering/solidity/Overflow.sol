// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Overflow {
    function checkedDec(uint256 x) external pure returns (uint256) {
        return x - 1;
    }

    function uncheckedDec(uint256 x) external pure returns (uint256) {
        unchecked { return x - 1; }
    }

    function narrow(uint256 x) external pure returns (uint8) {
        return uint8(x);
    }
}
