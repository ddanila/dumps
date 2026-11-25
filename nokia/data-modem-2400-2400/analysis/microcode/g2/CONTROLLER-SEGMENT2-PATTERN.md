# A4 emits the V.26 ter segment-2 digital pattern in both scrambler modes

[ITU-T V.26 ter Table 3 and Appendix I](https://www.itu.int/rec/dologin_pub.asp?id=T-REC-V.26ter-198811-I%21%21PDF-E&lang=e&type=items)
give the first 19 phase changes of segment 2 and the feedback rules for
scrambling input ones with GPC (taps 18/23) or GPA (taps 5/23). At 2400
bit/s, each segment-2 pattern lasts 64 bits, or 32 dibits. The left digit
of each dibit is the first bit in time; the 0/90/180/270° mapping comes
from Table 1.

The [screen](controller_segment2_pattern.py) takes the unchanged 8031's
[64-iteration port-01 output](MAIN-LOOP-LONG.md). It transcribes the printed
19-dibit prefix into 38 bits, verifies those bits against the published
recurrence, and predicts the remaining 26 bits. It then searches **every
64-bit window** of each controller output under both serial bit orders.

| Selector | Controller scrambler | A4 port-01 bytes, first block | First A5 byte | Exact standard windows |
| --- | --- | --- | --- | --- |
| `40` | GPC, tap 18 | `F9 07 F8 1C 1C F0 81 31` | `FC` | bits 1–64 and 321–384 |
| `60` | GPA, tap 5 | `F8 07 F8 9C 0F C2 09 D9` | `D9` | bits 1–64 and 321–384 |

The four listed windows match **all 64 bits**, LSB-first. Each starts at the
second bit of the first A4 byte and ends with the first bit of the following
A5 byte. They are the only exact windows in the four 64-iteration streams;
the best 64-bit match in the `00` and `20` streams is 50 and 45 bits,
respectively. Both A4 blocks in each `40`/`60` run repeat the same eight
bytes after the A6/A3 return. The recorded A4 source byte is `FF` throughout,
and the next A5 source byte is `03`; every port-01 output was independently
checked against the controller scrambler in the earlier run.

This is strong evidence that the controller generates the standard's **digital
segment-2 synchronization sequence** on its `40`/`60` branch. The first
38 target bits come from the printed table, while the remaining 26 are
out-of-table predictions. The one-bit offset and crossing into A5 mean the
exact segment boundary in hardware is not yet identified. Forced timer and
serial events do not establish natural duration, and no DAC or analog line
output is proved. The [PROM calibration](PHOTO-SEGMENT2-STANDARD-CALIBRATION.md)
tests these actual bits as candidate DSC inputs. The
[machine report](results/controller-segment2-pattern.json) includes all
four selector controls, exact windows and source hashes.

An [interrupt-paced controller run](MAIN-LOOP-TIMER1-SEGMENT2.md) now reaches
the same A4/A5 byte sequence without forcing expiry at each polling pass,
under an explicit positive-RAM15 gate. It also observes 25 modeled Timer 1
interrupts through the preceding A3 interval and no A3 port-01 writes.
