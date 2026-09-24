"""Crack spreads and refining margins (build of Book 3, Chapter 3).

Crude in dollars per barrel; US products quoted in dollars per gallon (42 gallons a barrel);
European gasoil in dollars per metric tonne. A crack is a margin per barrel of crude:
products sold minus crude bought, in a fixed ratio.
"""
import math

GALLONS_PER_BARREL = 42
BARRELS_PER_CUBIC_METRE = 6.28981
LOT_BARRELS = 1_000          # CL, RB and HO lots are all 1,000 barrels (42,000 gallons)


def per_gallon_to_per_barrel(p: float) -> float:
    return p * GALLONS_PER_BARREL


def barrels_per_tonne(density_kg_per_litre: float) -> float:
    """Barrels in one metric tonne of a product of the given density."""
    return BARRELS_PER_CUBIC_METRE / density_kg_per_litre


def per_tonne_to_per_barrel(p: float, density_kg_per_litre: float) -> float:
    return p / barrels_per_tonne(density_kg_per_litre)


def crack(crude: float, products: dict[str, float], ratio: dict[str, int], crude_barrels: int) -> float:
    """Margin per barrel of crude of the crack `crude_barrels` : ratio, all prices per barrel:
    (sum of ratio[p] * products[p] - crude_barrels * crude) / crude_barrels."""
    if sum(ratio.values()) != crude_barrels:
        raise ValueError("a crack sells as many barrels of product as it buys of crude")
    return (sum(n * products[p] for p, n in ratio.items()) - crude_barrels * crude) / crude_barrels


def three_two_one(crude: float, gasoline_gal: float, diesel_gal: float) -> float:
    """3-2-1 crack with US products quoted per gallon."""
    return crack(crude, {"gasoline": per_gallon_to_per_barrel(gasoline_gal),
                         "diesel": per_gallon_to_per_barrel(diesel_gal)}, {"gasoline": 2, "diesel": 1}, 3)


def gross_refining_margin(crude: float, yields: dict[str, float], products: dict[str, float]) -> float:
    """Value of the products a barrel of crude yields (volume fractions, which may sum above 1:
    processing gain) less the crude price."""
    return sum(y * products[p] for p, y in yields.items()) - crude


def hedge_lots(throughput_bpd: float, days: int, ratio: dict[str, int], crude_barrels: int) -> dict[str, int]:
    """Futures lots that lock a crack on a throughput: buy crude, sell products in the ratio.
    Positive = buy. Volumes are rounded to whole lots."""
    crude_bbl = throughput_bpd * days
    lots = {"crude": round(crude_bbl / LOT_BARRELS)}
    for p, n in ratio.items():
        lots[p] = -round(crude_bbl * n / crude_barrels / LOT_BARRELS)
    return lots


def arbitrage_open(origin: float, destination: float, freight: float, other: float = 0.0) -> float:
    """Profit per unit of moving a product from origin to destination (positive: the window is open)."""
    return destination - origin - freight - other


def is_whole(x: float) -> bool:
    return math.isclose(x, round(x))
