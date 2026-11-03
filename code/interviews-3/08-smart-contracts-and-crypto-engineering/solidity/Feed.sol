// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

contract Feed {
    int256 public answer;
    uint256 public updatedAt;

    function push(int256 a, uint256 t) external {
        answer = a;
        updatedAt = t;
    }
}

contract Consumer {
    function trusting(Feed f) external view returns (uint256) {
        return uint256(f.answer());
    }

    function careful(Feed f, uint256 maxAge) external view returns (uint256) {
        int256 a = f.answer();
        require(a > 0, "bad answer");
        require(block.timestamp - f.updatedAt() <= maxAge, "stale");
        return uint256(a);
    }
}
