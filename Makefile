.PHONY: all clean distclean venv test-code figdata gates

PY := .venv/bin/python
CH ?=

all:
	latexmk

venv:
	# --without-pip: Debian/Ubuntu system pythons often lack ensurepip; the
	# outer pip installs into the venv with --python instead.
	test -x $(PY) || python3 -m venv --without-pip .venv
	python3 -m pip --python $(PY) -q install numpy pandas pytest ruff

# make test-code                      -> everything
# make test-code CH=markets-1/07-pnl  -> one chapter
test-code:
	tools/test_code.sh $(CH)

# Regenerate every chart CSV under figdata/ from its script.
figdata:
	tools/figdata.sh $(CH)

# make gates                 -> every written book
# make gates BOOK=markets-2   -> one book
BOOK ?= markets-1 markets-2 markets-3 methods derivatives rates-credit-risk
gates:
	for b in $(BOOK); do tools/gates.sh book $$b || exit 1; done

clean:
	latexmk -c

distclean:
	latexmk -C
	rm -rf build
