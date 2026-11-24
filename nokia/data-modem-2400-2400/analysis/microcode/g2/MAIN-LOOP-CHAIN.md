# The controller's main loop carries received bytes into state and output frames

The [earlier chain](STATE-FRAME-CROSSCHECK.md#preserved-ram-chain) kept one RAM
image but directed the 8031 PC between state and send routines. This probe
enters the unchanged ROM at its actual polling-loop entry **1ED3**. Eight
iterations traverse the complete `08DD → 0800 → 0620 → 1000 → 1790 → 006E
→ 0899 → 08E9` sequence and branch back to 1ED3 without an internal PC
handoff. RAM and SFR state persist throughout.

The diagnostic fixture starts in RAM34=A0 with RAM22.4 set. Each receive
iteration supplies a sync event and six bytes `07 00 00 00 selector 00`.
The controller's XOR normalization makes the first received state byte zero.
The harness supplies serial receive and transmit-completion events, injects
timer17=80 at each loop boundary to exercise expiry, and returns zero on the
specific external status reads at 08E5, 0539, 1D9D and 1DBD. Interrupts are
disabled. These are explicit peripheral assumptions, not observed modem
traffic or measured timer behavior.

All **256 selector values** complete eight iterations without an emulator
error. Each consumes seven receive events and emits four frame bytes per
iteration. The first four state/frame pairs are common to every selector:

| Iterations | State after step | Emitted frame |
| --- | --- | --- |
| 1–2 | A1 | `80 02 A1 7A` |
| 3–4 | A2 | `80 02 A8 7A` |

The fifth iteration branches by the received selector's bit 6. The remaining
frames form six chains:

| Selector condition | Count | States 5–8 | Frames 5–6; 7–8 |
| --- | ---: | --- | --- |
| bit 6=0, bit 0=0, `(bit 1=0 or bit 3=1)` | 48 | B8,B8,B4,B4 | `D0 47 A1 22`; `D0 47 A1 EA` |
| bit 6=0, bit 0=1, `(bit 1=0 or bit 3=1)` | 48 | B8,B8,B4,B4 | `C0 47 A1 22`; `C0 47 A1 EA` |
| bit 6=0, bit 0=0, bit 1=1, bit 3=0 | 16 | B8,B8,B4,B4 | `D0 42 A1 22`; `D0 42 A1 EA` |
| bit 6=0, bit 0=1, bit 1=1, bit 3=0 | 16 | B8,B8,B4,B4 | `C0 42 A1 22`; `C0 42 A1 EA` |
| bit 6=1, bit 0=0 | 64 | A3,A3,A4,A4 | `D0 42 A1 BA` throughout |
| bit 6=1, bit 0=1 | 64 | A3,A3,A4,A4 | `C0 42 A1 BA` throughout |

This is stronger than the handoff experiment: the received bytes pass through
the ROM's input decoder and the real caller path before the state fork and
output. It also corrects the assumption that the handoff fixture's outgoing
bytes are a complete command trace. For example, its first A1 frame was
`80 02 81 7A`; the uninterrupted input path sends `80 02 A1 7A`. The
physical recipient and meaning of these frames remain unknown, so the bytes
cannot yet be assigned tone, training or data labels.

The [report](results/main-loop-chain.json) retains every selector's eight
steps, cycle positions, bus writes, the six group memberships and source
hashes. Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/main_loop_chain.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -p 'test_main_loop_chain.py'
```

The next G2 step is to carry an actual controller call's line-side bytes and
these frames into a candidate DSC2847 interface, then identify a recurring
microcode signal path. This probe itself neither runs DSC2847 nor establishes
the frame-to-DSP wiring.
