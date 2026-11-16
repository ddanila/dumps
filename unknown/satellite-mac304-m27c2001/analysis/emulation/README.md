# Executing MAC 3.04

This harness executes the unchanged ROM using an MIT-licensed 8051 core,
banked code memory and synthetic peripherals. It is a research emulator,
not a complete satellite receiver. See the [investigation](../README.md)
and [detailed harness notes](README.txt) for assumptions, ABI and exit codes.

From this directory, with a C compiler, POSIX shell and Python 3:

```sh
python3 run_all.py --rom ../../mac304-m27c2001.bin --out /tmp/mac304-results
```

The suite builds the core, runs stack/timing regressions, boots the ROM,
checks all 1,424 main text entries, exercises 310 screen/state/language cases,
471 service edits and 319 dispatch scenarios, and generates a gallery.
It takes roughly one to several minutes. Large intermediate traces are removed
unless `--keep-details` is supplied. Input ROM bytes are never modified.

Published results:

- [Summary](output/SUMMARY.json)
- [Captured menu gallery](output/gallery/index.html) — open locally in a browser
- [Text captures](output/gallery/frames.txt) and [exact row bytes](output/gallery/frames.json)
- [Individual results](output/results/) and [selected compressed traces](output/evidence/)

The gallery is an ASCII approximation of persistent display-memory writes.
Physical glyphs, video, RF input and card records are not emulated. Five dispatch
cases intentionally enter power-down; these require the expected nonzero
completion status and PCON state rather than being treated as ordinary returns.

Core source comes from [jarikomppa/emu8051](https://github.com/jarikomppa/emu8051),
commit `5dc681275151c4a5d7b85ec9ff4ceb1b25abd5a8`. The [provenance manifest](UPSTREAM.json)
records original and modified hashes; [core-fixes.patch](core-fixes.patch)
documents upper-stack, cycle-delay and instrumentation changes. The upstream
[MIT license](emu8051/LICENSE) is retained. The core regression checks are
specific to these changes, not an exhaustive CPU conformance suite.
