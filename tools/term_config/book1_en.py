"""Book 1 (Markets I) -- en. Curation only; the rules live in tools/termlink/.

Market vocabulary is ordinary English: most one-word terms carry an everyday
sense outside their defining chapter. STOP keeps a term linkable in its own
chapter and nowhere else; DROP removes it everywhere. Curated after the
English text landed. Regenerate with:
  python3 tools/link_defined_terms.py --book 1 --unwrap --apply
  python3 tools/link_defined_terms.py --book 1 --apply
"""
AMBIG_POLICY = "drop"
# Ordinary English in every chapter but their own: linked only where defined.
STOP = {
    "Agent",
    "Alpha",
    "Assignment",
    "Assigns",
    "Basis",
    "Benchmark",
    "Broker",
    "Carry",
    "Clearing",
    "Closing price",
    "Dividend",
    "Exchange",
    "Expiry",
    "Fair value",
    "Franchise",
    "Front month",
    "Gamma",
    "Haircut",
    "Hedger",
    "In kind",
    "In the money",
    "Level 1",
    "Level 2",
    "Level 3",
    "Leverage",
    "Locate",
    "Lot size",
    "Maker",
    "Mandate",
    "Mid price",
    "Notional",
    "Position",
    "Premium",
    "Principal",
    "Recall",
    "Roll",
    "Settlement",
    "Special",
    "Speculator",
    "Tick",
    "Variance",
    "agent",
    "alpha",
    "assignment",
    "assigns",
    "basis",
    "benchmark",
    "broker",
    "carry",
    "clearing",
    "closing price",
    "dividend",
    "exchange",
    "expiry",
    "fair value",
    "franchise",
    "front month",
    "gamma",
    "haircut",
    "hedger",
    "in kind",
    "in the money",
    "level 1",
    "level 2",
    "level 3",
    "leverage",
    "locate",
    "lot size",
    "maker",
    "mandate",
    "mid price",
    "notional",
    "position",
    "premium",
    "principal",
    "recall",
    "roll",
    "settlement",
    "special",
    "speculator",
    "tick",
    "variance",
}
# Too frequent to be worth a link anywhere.
DROP = {"order", "share", "Order", "Share"}
NO_CAPITAL = set()
EXTRA = {}
_G = r'(?:[^{}]|\{[^{}]*\})'
EXTRA_PROTECT = [
    r'\\texttt\{' + _G + r'*\}',                        # identifiers, not prose
    r'\\omcode\{[^{}]*\}\{[^{}]*\}\{[^{}]*\}\{' + _G + r'*\}',   # listing captions feed the list of listings
    r'\\begin\{omsources\}.*?\\end\{omsources\}',        # titles of other people's documents
    r'\\begin\{dated\}\{[^{}]*\}\{' + _G + r'*\}',        # box titles
    r'\\bfield\{[^{}]*\}',
    r'basis\s+points?',                                  # the unit, not the futures basis
    r'[Ss]pecial\s+(?:dividend|opening|case|purpose)s?',
]
