"""Book 3 -- fr. Curation only; the rules live in tools/termlink/.

The French pilot edition (2026-11-09). STOP keeps a term linkable in its own chapter and nowhere else; DROP removes it
everywhere. Curated by the edition's coordinator from this edition's own harvest, with the frequency census against the
English twin (translation_instruction.md, "Term linking"). Regenerate with:
  python3 tools/link_defined_terms.py --book 3 --lang fr --unwrap --apply
  python3 tools/link_defined_terms.py --book 3 --lang fr --apply
"""
_G = r'(?:[^{}]|\{[^{}]*\})'
# The structural masks of book3_en.py: code identifiers, listing captions, other people's documents, box titles,
# build-field names. They are not prose in any language.
EXTRA_PROTECT = [
    r'\\texttt\{' + _G + r'*\}',
    r'\\omcode\{[^{}]*\}\{[^{}]*\}\{[^{}]*\}\{' + _G + r'*\}',
    r'\\begin\{omsources\}.*?\\end\{omsources\}',
    r'\\begin\{dated\}\{[^{}]*\}\{' + _G + r'*\}',
    r'\\bfield\{[^{}]*\}',
    r'points?\s+de\s+base',                              # the unit, not the futures basis
]
AMBIG_POLICY = "drop"
STOP = set()
DROP = set()
NO_CAPITAL = set()
EXTRA = {}
DERIVED = {}
PRIMARY_OK = set()
