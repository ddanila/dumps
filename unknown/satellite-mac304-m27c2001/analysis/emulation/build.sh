#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
cc -O2 -g -Wall -Wextra -Wno-unused-parameter -DSAT_TRACE harness.c emu8051/core.c emu8051/opcodes.c emu8051/disasm.c -o build/sat-run
cc -O2 test_core.c emu8051/core.c emu8051/opcodes.c emu8051/disasm.c -o build/test-core
build/test-core
