// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Fixed {
    uint256 constant ONE = 1e18;

    function divFirst(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        return a / b * c;
    }

    function mulFirst(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        return a * c / b;
    }

    function wmul(uint256 a, uint256 b) external pure returns (uint256) {
        return a * b / ONE;
    }
}
