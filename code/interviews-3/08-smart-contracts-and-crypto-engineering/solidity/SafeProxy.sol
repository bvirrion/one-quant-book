// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

// Not printed: the implementation address kept in a slot no variable will reach.
contract SafeProxy {
    bytes32 constant SLOT = keccak256("example.proxy.implementation");

    constructor(address i) {
        bytes32 s = SLOT;
        assembly { sstore(s, i) }
    }

    function impl() external view returns (address a) {
        bytes32 s = SLOT;
        assembly { a := sload(s) }
    }

    fallback(bytes calldata data) external returns (bytes memory) {
        address a = this.impl();
        (bool ok, bytes memory out) = a.delegatecall(data);
        require(ok);
        return out;
    }
}
