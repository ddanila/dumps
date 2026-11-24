# Continuous controller calls produce verified scrambled USART bytes

The [main-loop chain](MAIN-LOOP-CHAIN.md) used a zero USART-status stub and
recorded no write to the line-side data address 01. This experiment sets the
transmit-ready status bit at the ROM's reads at 0539 and 1D9D, leaving the
same initial A0 state, seven receive events per iteration, synthetic timer
underflow, and uninterrupted polling-loop control flow. The receive-ready bit
at 1DBD remains clear. It runs **12 iterations for every one of the 256
received selector bytes**.

Every run completes without an emulator error. After the A2 state fork, each
active iteration writes one byte to external data address 01. The byte at
RAM37 entering ROM routine 053E and its 23-bit history were captured before
execution. For **every** address-01 write, the independently implemented
bit-serial scrambler computes exactly the byte that the unchanged ROM writes.
The four distinct source/output streams are:

| Selector condition | Selectors | State branch | Short tap | RAM37 source bytes | Port-01 bytes |
| --- | ---: | --- | ---: | --- | --- |
| bit 6=0; bit 5=0 or bit 4=1 | 96 | B8→B4 | 18 | `00 00 FF FF FF FF FF FF` | `06 F8 84 1C 90 CF B1 09` |
| bit 6=0; bit 5=1 and bit 4=0 | 32 | B8→B4 | 5 | `00 00 FF FF FF FF FF FF` | `E7 7B 97 DE 79 DB 6B 8E` |
| bit 6=1; bit 5=0 or bit 4=1 | 96 | A3→A4 | 18 | `FF FF FF FF FF FF` | `F9 07 F8 1C 1C F0` |
| bit 6=1; bit 5=1 and bit 4=0 | 32 | A3→A4 | 5 | `FF FF FF FF FF FF` | `F8 07 F8 9C 0F C2` |

In this fixture, bit 6 controls the state fork and changes when port-01
transmission begins: iteration 5 for B8, iteration 7 for A3. Bits 5 and 4
select the 5- or 18-bit short scrambler tap. The remaining selector bits may
still affect the four-byte frames, but these 12-iteration line-byte streams
fall into the four groups above. This gives G2 an actual controller-ROM byte
stream and call/answer-like scrambler alternatives to drive into DSC2847
candidate inputs; it does not establish which branch is the physical call
mode or what the DSP receives.

The [report](results/main-loop-serial.json) records every selector's state,
four-byte frames, pre-scrambler source bytes, chosen delay and port-01 output.
The zero-status [control report](results/main-loop-chain.json) has no port-01
writes in any of its 256 eight-iteration runs. Reproduce with:

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/main_loop_serial.py
python3 -m unittest discover -s nokia/data-modem-2400-2400/analysis/microcode/g2 -p 'test_main_loop_serial.py'
```

The USART-ready status, timer underflow, and receive frame are diagnostic
stimuli. Address 01 is identified by the controller's bus write; the external
USART and its timing are not emulated here. These bytes are neither captured
line signals nor proof that DSC2847 consumes this exact stream. A C2 test must
still route them under an explicit board connection and show a changing,
dibit-dependent microcode output waveform.
