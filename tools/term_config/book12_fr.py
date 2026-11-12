"""Book 12 (Machine Learning for Markets) -- fr. Curation only; the rules live in tools/termlink/.

The French pilot edition (2026-11-11/12). STOP keeps a term linkable in its own chapter and nowhere else; DROP removes it
everywhere. Seeded from book12_en.py through GLOSSARY_BOOK_12_FR.run.md (draft/pilot-quant-fr/mkconfig.py), then
curated by the coordinator with the frequency census against the English twin. Regenerate with:
  python3 tools/link_defined_terms.py --book 12 --lang fr --unwrap --apply
  python3 tools/link_defined_terms.py --book 12 --lang fr --apply
"""
AMBIG_POLICY = "drop"
# The English STOP list of book12_en.py, term by term through the glossary: ordinary words outside their own chapter.
STOP = {
    'Annuité',
    'Barre',
    'Barres',
    'Base nette',
    'Cap',
    'Convexité',
    'Convexité négative',
    'Cote',
    'Coupon',
    'Coupon couru',
    'DV01',
    'Devise de base',
    'Devise de cotation',
    'Drawdown',
    'Duration effective',
    'Débouclage',
    'Débouclages',
    'Gilt',
    'High yield',
    "Indice de référence de l'inflation",
    'Intensité de défaut',
    'Investment grade',
    'Jambe fixe',
    'Jambe variable',
    'Largeur',
    'Mark-out',
    'Off-the-run',
    'On-the-run',
    'Ordre au fixing',
    'Pair',
    'Paire de devises',
    'Pass-through',
    'Pip',
    'Prix pied de coupon',
    'Prix plein coupon',
    'Prédicteur',
    'Prédicteurs',
    'Pénalité de suspens',
    'Rang de séniorité',
    'Remboursement anticipé',
    'Rendement actuariel',
    'Rendement réel',
    'Réserves',
    'Specialness',
    'Swaption',
    "Taux d'escompte",
    'Taux de croissance',
    'Taux directeur',
    'Temps de rétention',
    'Tranche',
    'Volatilité normale',
    'Z-spread',
    'annuité',
    'barre',
    'barres',
    'base nette',
    'cap',
    'convexité',
    'convexité négative',
    'cote',
    'coupon',
    'coupon couru',
    'dV01',
    'devise de base',
    'devise de cotation',
    'drawdown',
    'duration effective',
    'débouclage',
    'débouclages',
    'gilt',
    'high yield',
    "indice de référence de l'inflation",
    'intensité de défaut',
    'investment grade',
    'jambe fixe',
    'jambe variable',
    'largeur',
    'mark-out',
    'off-the-run',
    'on-the-run',
    'ordre au fixing',
    'pair',
    'paire de devises',
    'pass-through',
    'pip',
    'prix pied de coupon',
    'prix plein coupon',
    'prédicteur',
    'prédicteurs',
    'pénalité de suspens',
    'rang de séniorité',
    'remboursement anticipé',
    'rendement actuariel',
    'rendement réel',
    'réserves',
    'specialness',
    'swaption',
    "taux d'escompte",
    'taux de croissance',
    'taux directeur',
    'temps de rétention',
    'tranche',
    'volatilité normale',
    'z-spread',
    'Événement de crédit',
    'événement de crédit',
}
# The English DROP list of book12_en.py, through the glossary.
DROP = {
    'Bundle',
    'Edge',
    'Inventaire',
    'Largeur',
    'Pack',
    'bundle',
    'edge',
    'inventaire',
    'largeur',
    'pack',
}
NO_CAPITAL = set()
EXTRA = {}
DERIVED = {}
PRIMARY_OK = set()
# The structural masks of book12_en.py: code identifiers, listing captions, other people's documents, box titles.
_G = r'(?:[^{}]|\{[^{}]*\})'
EXTRA_PROTECT = [
    r'\\texttt\{' + _G + r'*\}',                        # identifiers, not prose
    r'\\omcode\{[^{}]*\}\{[^{}]*\}\{[^{}]*\}\{' + _G + r'*\}',   # listing captions feed the list of listings
    r'\\begin\{omsources\}.*?\\end\{omsources\}',        # titles of other people's documents
    r'\\begin\{dated\}\{[^{}]*\}\{' + _G + r'*\}',        # box titles
    r'\\bfield\{[^{}]*\}',
    r'basis\s+points?',                                  # the unit, not the futures basis
    r'[Ss]pecial\s+(?:dividend|opening|case|purpose)s?',
    r'(?:zero|low|high)-coupon',                         # compounds, not the defined coupon
    r'fat-tailed',
    r'points?\s+de\s+base',                              # the unit, not the futures basis
]
