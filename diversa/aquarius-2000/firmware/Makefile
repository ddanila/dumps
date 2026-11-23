ASM = z80asm
CFLAGS = -O2 -Wall -Wextra -Werror
ROM = build/aquarius-exerciser.bin
FACTORY = ../aquarius-2000-27256.bin

.PHONY: all test
all: $(ROM)
$(ROM): exerciser.asm board.asm Makefile | build
	$(ASM) -L -o $@ exerciser.asm 2>build/symbols.txt || { cat build/symbols.txt; rm -f $@; exit 1; }
	test "$$(wc -c < $@)" -eq 32768
	cd build && sha256sum aquarius-exerciser.bin > SHA256SUMS
build:
	mkdir -p $@
build/verify: verify.c | build
	$(CC) $(CFLAGS) -o $@ $< -lz80ex
test: $(ROM) build/verify
	echo '958d3c99aa6b8bf7274a59d6742e516b068e7b2c5fb13c26d64f709a55965a57  $(FACTORY)' | sha256sum -c -
	build/verify $(FACTORY) $(ROM)
