// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Impl {
    uint256 public x;

    function setX(uint256 v) external {
        x = v;
    }
}

contract Proxy {
    address public impl;

    constructor(address i) { impl = i; }

    fallback(bytes calldata data) external returns (bytes memory) {
        (bool ok, bytes memory out) = impl.delegatecall(data);
        require(ok);
        return out;
    }
}
