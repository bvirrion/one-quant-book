// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Rejecter {
    receive() external payable { revert(); }
}

contract Payout {
    mapping(address => bool) public paid;

    function payUnchecked(address to) external payable {
        to.call{value: msg.value}("");
        paid[to] = true;
    }

    function payChecked(address to) external payable {
        (bool ok, ) = to.call{value: msg.value}("");
        require(ok);
        paid[to] = true;
    }
}
