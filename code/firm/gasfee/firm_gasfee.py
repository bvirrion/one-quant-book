"""Transaction fees and confirmation times (build of Book 3, Chapter 14).

Ethereum's base fee follows EIP-1559 exactly, in integer wei: it rises or falls by at most one
eighth a block according to how far the parent block's gas used was from its target (half its
limit). Fees are in gwei (1e9 wei) per unit of gas; prices of ether in dollars.
"""
DENOMINATOR = 8
ELASTICITY = 2
GWEI = 10**9


def next_base_fee(parent_base_fee: int, gas_used: int, gas_limit: int) -> int:
    """Base fee (wei) of the next block under EIP-1559."""
    target = gas_limit // ELASTICITY
    if gas_used == target:
        return parent_base_fee
    if gas_used > target:
        delta = max(parent_base_fee * (gas_used - target) // target // DENOMINATOR, 1)
        return parent_base_fee + delta
    delta = parent_base_fee * (target - gas_used) // target // DENOMINATOR
    return parent_base_fee - delta


def project(base_fee: int, usage: list[float], gas_limit: int) -> list[int]:
    """Base fees of the next blocks when each block uses the given fraction of its gas limit."""
    out = []
    for u in usage:
        base_fee = next_base_fee(base_fee, int(u * gas_limit), gas_limit)
        out.append(base_fee)
    return out


def tx_cost_usd(gas: int, base_fee_gwei: float, priority_gwei: float, eth_usd: float) -> float:
    """Cost of a transaction: gas used times (base fee + priority fee), in dollars."""
    return gas * (base_fee_gwei + priority_gwei) * 1e-9 * eth_usd


def confirmation_seconds(chain: str, confirmations: int = 6) -> float:
    """Expected time until a transfer is treated as settled: Bitcoin, `confirmations` blocks of ten
    minutes on average; Ethereum, finality after two epochs of 32 slots of 12 seconds."""
    if chain == "bitcoin":
        return confirmations * 600.0
    if chain == "ethereum":
        return 2 * 32 * 12.0
    raise ValueError(chain)
