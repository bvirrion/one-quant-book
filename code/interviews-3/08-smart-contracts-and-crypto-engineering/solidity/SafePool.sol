// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

// Not printed: the fix, with shares reduced first, and a lock that a view can see.
contract SafePool {
    uint256 public shares;
    bool locked;

    function join() external payable {
        shares += msg.value;
    }

    function price() public view returns (uint256) {
        require(!locked, "in a call");
        return address(this).balance * 1e18 / shares;
    }

    function leave(uint256 n) external {
        uint256 amount = n * price() / 1e18;
        locked = true;
        shares -= n;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        locked = false;
    }
}

contract SafeReader {
    SafePool pool;
    uint256 public seen;
    bool public refused;

    constructor(SafePool p) { pool = p; }

    function run() external payable {
        pool.join{value: msg.value}();
        pool.leave(msg.value);
    }

    receive() external payable {
        try pool.price() returns (uint256 p) {
            seen = p;
        } catch {
            refused = true;
        }
    }
}
