# A controller pin distinguishes A0 from A2 despite identical serial frames

The [direct controller replay](controller_state_pin_channels.py) runs the
unchanged 8031 ROM's four-byte send routine for A0, A1 and A2 under the same
fixed flag/payload fixture as the [frame study](results/controller-frames.json).
It retains every P1 write and checks that the P1.2 latch pulse follows the
fourth serial completion. The code builder independently identifies P1.5 as
raw state-code `K` bit 1 ([controller output construction](../../controller/OUTPUT-BUILD.md)).

| State | Raw `K` | Four transmitted bytes | Final P1 | P1.5 |
| --- | ---: | --- | ---: | ---: |
| A0 | `83` | `80 02 88 7A` | `F8` | 1 |
| A1 | `84` | `80 02 81 7A` | `D8` | 0 |
| A2 | `81` | `80 02 88 7A` | `D8` | 0 |

A0 and A2 are indistinguishable by the four serial bytes in this fixture,
but differ at P1.5. The pair `(frame, P1.5)` distinguishes all three states.
The [machine report](results/controller-state-pin-channels.json) records
the six P1 writes per send, latch and completion cycles, frame bytes and
the candidate CD4094 logical-chip-1 byte.

The [preserved-RAM chain](chain_frames.py) now also records P1 after each
send. All 256 selector runs retain P1.5=0 through their A1 and A2 sends,
with four distinct frame/state chains and no emulator errors. This checks
that the low pin level is not confined to the isolated send fixture.
The chain forces timer expiry and directs the PC between state and send
routines, so it does not establish a natural continuous operating sequence.

P1.5's electrical destination is untraced. It may select a DSP mode, control
another board, or serve a local function. A candidate DSC2847 input model
that uses only the four CD4094 bytes cannot represent this observed A0/A2
distinction. Test P1.5 as an independently logged control input when a
photo-compatible route warrants it; do not infer tone semantics from its
level alone.
