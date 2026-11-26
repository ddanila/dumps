# Controller-like mode bytes and a freeze-edge do not gate the tested RAM pulse

The [corrected RAM pulse replay](JOINT-MASK04-RAM-PULSE-FREEZE.md)
demonstrated a delayed `3FA` output through one explicitly assumed
external-memory route. This [mode comparison](joint_mask04_ram_mode_pulse.py)
asks whether held candidate `D3EB` bytes `01`, `81`, `A1` and `C1`, or
synthetic `81→A1` and `81→C1` edges at the write-freeze boundary,
suppress or alter that effect. `81`, `A1` and `C1` occur in controller frames; their
physical connection to `3EB` and the edge timing remain untraced.

Twenty-four runs use the same 64-sample reference ADC stream, with or without
the single sample-25 `51→B1` pulse. For each mode fixture, a write/freeze
control is paired with a three-sample delayed read from the modeled
256×8 RAM into `3FA` D's low nibble. The RAM latches `3F9` Y's low
nibble, writes at `3EC` through sample 25, and then freezes. The address
ticks once per held ADC sample, with four `3EA` visits and four `3EC`
writes accounted for per ADC visit. Every case completes **96,047 real
PROM microinstructions** and **3,000 ADC visits** without a loop exit.
The `01` control's ADC, RAM and full-trace hashes exactly replay the
earlier result.

| `D3EB` fixture | Changed frozen RAM byte | `3FA` differences three samples later | First delayed `3FA` codes, baseline→pulse | Write-only delayed differences |
| --- | --- | ---: | --- | ---: |
| `01` | address 26, `01→0F` | 47 visits | `20→2E` | 0 |
| `81` | address 26, `01→0F` | 47 visits | `20→2E` | 0 |
| `A1` | address 26, `01→0F` | 47 visits | `30→3E` | 0 |
| `C1` | address 26, `01→0F` | 47 visits | `20→2E` | 0 |
| `81→A1` at freeze | address 26, `01→0F` | 47 visits | `30→3E` | 0 |
| `81→C1` at freeze | address 26, `01→0F` | 47 visits | `20→2E` | 0 |

At the delayed sample, `3F8` and `3F9` show no pulse difference in any
mode fixture. The altered `A1` upper nibble shows that this mode can affect
the `3FA` output code, but it does not gate the stored low-nibble pulse in
this fixture. The synthetic edge switches after sample 25, at the same
boundary where the independent RAM write gate freezes; it also preserves
the delayed response. At all 3,000 visits of each measured site (`3F8`,
`3F9`, `3FA`), held `C1` and `81→C1` produce **zero Y-byte differences**
from held `81` under both inputs and both routes. Their full execution
trace digests differ, but their final RAM hashes agree. Thus the
controller-observed bit-6 toggle reaches this assumed input without
controlling this candidate RAM response or its measured Y sites.
The [split-slice trace](JOINT-MASK04-RAM-RETURN-ARITHMETIC.md) checks
the `3FA` operation itself and shows why the RAM byte changes Y while
the written R13 and Q remain identical across matched pulse controls.

This rejects a **simple direct-`3EB` gate**, including the observed
`81↔C1` mode-bit change held or switched at this one boundary, for this
specific RAM return. It does not reject a
controller-driven training/freeze circuit at its actual timing, another
memory lane or an analog output path. No received bit or
echo residual is identified, so C3/C4 remain open and G2 active. The
next C4 test should vary a photo-compatible write-enable or return
route under paced controller traffic and compare own echo,
remote and mixed inputs with the same write-only control; the present
mode result does not justify calling the path an echo canceller.

Run `python3 g2/joint_mask04_ram_mode_pulse.py` from the microcode
directory. The [machine report](results/joint-mask04-ram-mode-pulse.json)
contains all trace, input and RAM hashes, pulse-window counts and full
Y-byte comparisons against `81`.
