// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Relay {
    mapping(address => uint256) public balance;

    function fund(address who) external payable {
        balance[who] += msg.value;
    }

    function pay(address to, uint256 amount, uint8 v, bytes32 r, bytes32 s) external {
        bytes32 digest = keccak256(abi.encodePacked(to, amount));
        address from = ecrecover(digest, v, r, s);
        require(from != address(0) && balance[from] >= amount);
        balance[from] -= amount;
        balance[to] += amount;
    }
}

contract SafeRelay {
    mapping(address => uint256) public balance;
    mapping(address => uint256) public nonce;

    function fund(address who) external payable {
        balance[who] += msg.value;
    }

    function digestFor(address from, address to, uint256 amount)
        public view returns (bytes32)
    {
        return keccak256(
            abi.encode(block.chainid, address(this), from, nonce[from], to, amount)
        );
    }

    function pay(address from, address to, uint256 amount, uint8 v, bytes32 r, bytes32 s)
        external
    {
        require(from != address(0));
        require(ecrecover(digestFor(from, to, amount), v, r, s) == from);
        require(balance[from] >= amount);
        nonce[from] += 1;
        balance[from] -= amount;
        balance[to] += amount;
    }
}
