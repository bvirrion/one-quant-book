// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Pool {
    uint256 public shares;

    function join() external payable {
        shares += msg.value;
    }

    function price() public view returns (uint256) {
        return address(this).balance * 1e18 / shares;
    }

    function leave(uint256 n) external {
        (bool ok, ) = msg.sender.call{value: n * price() / 1e18}("");
        require(ok);
        shares -= n;
    }
}

contract Reader {
    Pool pool;
    uint256 public seen;

    constructor(Pool p) { pool = p; }

    function run() external payable {
        pool.join{value: msg.value}();
        pool.leave(msg.value);
    }

    receive() external payable {
        seen = pool.price();                 // a lender would value collateral here
    }
}
