// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Amm {
    function amountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut)
        external pure returns (uint256)
    {
        uint256 afterFee = amountIn * 997;
        return afterFee * reserveOut / (reserveIn * 1000 + afterFee);
    }
}
