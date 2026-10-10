# TOS/M end-to-end verification

On 2026-10-10, the unchanged S642 dump was tested through the emulated
keyboard CPU, host SIO, TOS/M keyboard driver and PC1715W display.
**The owner also manually confirmed typing and Latin/Cyrillic switching.**

## Results

The automated test types the same four physical matrix keys three times,
with SI/SO between sequences. Both builds receive status `E0`, then `E4`,
then `E0`, with the same keycodes. TOS/M writes `10` and then `00` to port
`1A`. Stock MAME 0.285 ignores those writes; the patched MAME 0.289 display
switches Latin → Cyrillic → Latin.

The four screenshots in each `snapshots-switch-*/rt1715w/` directory show:

1. Initial Latin text.
2. SI/SO alone: display unchanged until another key sends the new status.
3. After more typing: Cyrillic on the patched build, Latin on stock.
4. After a second toggle and typing: Latin restored.

`verify-language-switch.py` compares the static screen heading, excluding
new input and the blinking cursor. It verifies the changed glyphs, exact
restoration, unchanged stock display and identical keyboard/OS traces.
Run `python3 verify-language-switch.py` here to check the saved evidence
(requires Pillow). It passes.

## Configuration and reproduction

- Machine: `rt1715w`, original S550 boot ROM and 74S287 decoder.
- Keyboard: this acquisition's `s642.ic8`, loaded as `roms/rt1715w/s600.ic8`.
  The S600 checksum warning is expected.
- OS: original [TOS/M archive](https://xepb.org/robotron/warez/r1715mt.zip),
  whose CQM image SHA256 is
  `5c97d7145a6fae21033ec42407d455cff473ade2cefe4b2a58380343c59d1bab`.
- Original startup font order: `COMMON0.ZGF[1] KOI71.ZGF[2]`.
  No forced-font diagnostic disk or modified OS/keyboard binary was used.
- Fix: [MAME PR #6](https://github.com/ddanila/mame/pull/6), commit
  `0fdc895312c`, implementing port `1A` bit 4, XORed with GPA0.
  The [CRT schematic](https://xepb.org/robotron/docs/1715w.zip), drawing
  `1.93.310412.6/04`, sheet 2, shows latch A07/ZG2 and XOR gate E08.

With the host ROMs in `roms/rt1715w/` and the CQM image at
`disks/r1715mt.cqm`, run the following once for each build, substituting
`stock` or `patched` for `LABEL` and the executable path for `MAME`:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy MAME rt1715w \
  -rompath roms -flop1 disks/r1715mt.cqm -video none -sound none \
  -nothrottle -skip_gameinfo -autoboot_delay 0 \
  -autoboot_script language-switch.lua -seconds_to_run 315 \
  -snapshot_directory snapshots-switch-LABEL -cfg_directory cfg-LABEL
mv language-switch.tsv language-switch-LABEL.tsv
```

Use empty snapshot directories to preserve the expected screenshot numbering.
Host ROMs and the OS image are not duplicated here. The manual test used the
same patched build and original disk, with Right Ctrl mapped to SI/SO;
after tapping it, typing another letter switched the whole screen's alphabet.

This is a full emulated 1715W input/display test. It does not validate physical
host timing or all hardware of the original `rt1715lc` machine.
