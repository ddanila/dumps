# The candidate frame-byte mode edge survives a long receive handoff

The [short frame-mode replay](RECEIVER-MASK04-FRAME-MODE-DECISIONS.md)
found that held `81`, held `A1` and a synthetic `81→A1` controller
frame-byte edge leave the frozen two-visit receive features intact on
two 16-symbol streams. This follow-up carries that exact **untraced**
third-frame-byte-to-`3EB` hypothesis through the earlier
[eight-zero-octet handoff](RECEIVER-MASK04-DUAL-ZERO-HANDOFF.md).

For the call and answer selectors, the controller's actual line octets
for eight scrambled zero bytes follow 32 `11` preamble symbols. The
mask-`04` joint map executes **768,047 real PROM instructions** per
case, with 24,000 complementary ADC visits, 24,001 candidate Y5–Y7
latch edges and 96,001 wrapper `3EB` reads. The offered wrapper byte
switches from `81` to `A1` at wrapper visit 48,000, the assumed
preamble/data symbol boundary. Every offered mode byte is selected by
the executed ALU. The resulting full trace digests differ from the
otherwise identical `01`-mode baseline.

| Case | Recovered PROM decisions | Recovered line bytes | Paced aligned 8251/8031 |
| --- | ---: | --- | --- |
| Delay 5, 75° | 0 wrong, 0 unknown / 63 | `62 DE 61 9D 7C 5F E5 E2` | Eight decoded zeros; `AF→B0` |
| Delay 18, 165° | 0 wrong, 0 unknown / 63 | `A5 C2 4C 58 52 47 65 B4` | Eight decoded zeros; `AF→B0` |

The recovered bytes match the baseline fixture despite the changed
PROM traces. An external SYNDET pulse at the assumed bit-64 boundary
reaches `B0` in each paced controller run. A pulse one bit early, one
bit late, no pulse, or the opposite DTE selector remains at `AF`.
The first reversal dibit is still an explicit serial-boundary assumption;
all other preamble and data decisions come from the PROM captures.

This strengthens the **conditional** C3 handoff: the candidate frame
mode input can coexist with a long receive stream and controller zero
detector. It does not verify the controller-to-`3EB` wire, ADC bus,
three-bit latch, symbol capture/logic, RxD/RxC/SYNDET nets or pulse
source. The DSC and 8031 are run sequentially under a projected clock
alignment, with a narrow 8251 model and synthetic 8031 serial
completion. The `81→A1` edge still supplies no demonstrated echo
train/freeze behavior for C4. Next constrain the physical serial and
mode routes or test a natural clock-phase stimulus.

The [machine report](results/receiver-mask04-frame-mode-zero-handoff.json)
contains trace/source hashes, scores and controller controls. Reproduce
from the microcode directory with
`python3 g2/receiver_mask04_frame_mode_zero_handoff.py`.
