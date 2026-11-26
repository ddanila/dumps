# A seven-state phase rule survives changed receive level across selectors

The [level replay](JOINT-MASK04-Q05-PHASE-LEVEL.md) shows three new
four-bit states after ADC quantization changes. This
[offline rule test](joint_mask04_q05_phase_level_map.py) keeps the
original `5→0`, `8→1`, `C→2`, `D→3` phase map frozen. It uses only
the call selector's 75% and 125% executed captures and their known
dibits to solve phase-difference constraints for new states. The
result is `6→0`, `9→1`, `B→2`; all 128 call training decisions are
consistent. The rule is frozen before scoring the answer selector's
75% and 125% captures.

| Selector and role | Level | Preamble/pipeline | Data | Modeled aligned controller payload |
| --- | ---: | ---: | ---: | --- |
| `40` development | 0.75, 1.25 | 32/32 each | 32/32 each | `42 DB 19 E7 24 B6 68 93` |
| `60` holdout | 0.75, 1.25 | **32/32 each** | **32/32 each** | `42 DB 19 E7 24 B6 68 93` |
| Both nominal controls | 1.00 | 32/32 each | 32/32 each | `42 DB 19 E7 24 B6 68 93` |

The answer-side changed-level holdout contributes **128/128 correct
dibits** with no unknowns. The modeled 8251/unchanged 8031 consumes
and descrambles eight correct bytes at the aligned SYNDET pulse in
both levels; the one-bit-early pulse misaligns the bytes and the
one-bit-late pulse supplies only seven. The six executed DSC receive
traces and their line/ADC hashes are retained in the source report.

This is a cross-selector level holdout, not a fresh decoded payload:
call and answer use different scrambled line bytes but the same
eight-byte source payload. The new phase labels were inferred from
reference answers and do not identify Nokia logic. The latch clock,
ADC path, phase combinator, bit serializer, RxD/RxC and SYNDET route
are still photo-compatible assumptions. C2/C3/G2 remain open. Test
fresh data and carrier phase with the frozen seven-state rule, then
constrain a circuit and timing path without waiting for continuity.

The [machine report](results/joint-mask04-q05-phase-level-map.json)
records the learned phase assignments, six decoded streams and
controller controls. Reproduce with
`python3 g2/joint_mask04_q05_phase_level_map.py` from the microcode
directory.
