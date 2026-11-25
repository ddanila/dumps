# A later loop relays one D-byte nibble into four internal output slots

Under one explicit candidate mapping, an input change at `D3F8` exits the
`3ED–3FA` loop and reaches a repeated `3A2–3B6` path. This experiment uses
the [read-valid PROM-data mapping](LOWER-I-PROM-DATA-ROUTE.md), previous carry
with inverted polarity for condition select 0, Q=5, and a D1 pulse at the
21st `D3F8` visit to enter that path. All of those routes and timing choices
remain hypotheses. The [runner](lower_i_late_byte_relay.py) then tests the
real 128-bit 8031 scrambler stream at each selected-D site `3A3–3A7`.

In a 1,580-cycle run, the path reaches each candidate D site 103 times and
the fixture's four virtual capture sites `3B3–3B6` 103 times each. Compared
with constant D=`01`, changing the corresponding bit on D1, D2 or D3 changes
this many captured bytes:

| D site | Changed capture bytes, per lane |
| --- | ---: |
| `3A3` | 0 |
| `3A4` | 42 |
| `3A5` | 0 |
| **`3A6`** | **168** |
| `3A7` | 0 |

The `3A6` result has an exact low-nibble rule. For input byte D and
`n = D & 0F`, the captured Y values at `3B3, 3B4, 3B5, 3B6` are:

```text
(F0 | n, F0 | ((n + 1) & 0F), n, 0F - n)
```

All 256 constant D bytes were executed for 512 cycles each; every one of
the 14 reached quartets in each run obeyed the rule. There are 16 distinct
quartets, one per low nibble. A longer 2,000-cycle run independently checks
all **128 real 8031 bits** on each of D1–D3 at `3A6`: every corresponding
quartet follows the same rule, in bit order. This establishes a conditional
controller-byte-to-internal-Y relay through the executed real PROMs. It does
not show that the 8031 is physically wired to `3A6`.

The four Y sites are virtual captures in the fixture. The low-nibble mapping
alone has no demonstrated carrier advance, sample clock, DAC08 input path or
line signal, so it does not meet the transmitter test. Its meaning could
change if a real output latch samples a different word or if these values
feed later arithmetic. The next useful check is a photo-compatible latch
route/timing from this repeated path to DAC08, tested against the expected
changing carrier samples; otherwise vary the input/state mapping while
retaining this exact relay as a constraint.

The [machine report](results/lower-i-late-byte-relay.json) records the site
screen, all-byte check, stream replay, trace digests and source hashes.

```sh
python3 nokia/data-modem-2400-2400/analysis/microcode/g2/lower_i_late_byte_relay.py
```
