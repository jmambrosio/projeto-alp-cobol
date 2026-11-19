COBC = cobc
COBFLAGS = -x -free -Wall -debug

all: caixa exemplos

caixa: caixa.cob
	$(COBC) $(COBFLAGS) -o $@ $<

exemplos: exemplos.cob
	$(COBC) $(COBFLAGS) -o $@ $<

test: caixa
	python3 testar.py ./caixa

.PHONY: all test
