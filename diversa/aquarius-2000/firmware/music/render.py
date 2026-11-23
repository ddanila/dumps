"""Turn a 4 MHz PB3 logic trace from verify.c into mono listening audio."""
import argparse
from array import array
from math import exp, pi
from pathlib import Path
import sys
import wave

CLOCK = 4_000_000
RATE = 44_100


def render(trace, output):
    # Integer boundaries in CPU clocks * RATE. Average the high fraction in
    # each PCM bin so even the narrowest PB3 pulses contribute to the audio.
    edges = [tuple(map(int, line.split())) for line in trace.read_text().splitlines()]
    origin = edges[0][0]
    duration = (edges[-1][0] - origin) * RATE
    duty = array("f", [0]) * ((duration + CLOCK - 1) // CLOCK)
    for (begin, level), (end, _) in zip(edges, edges[1:]):
        if level:
            begin = (begin - origin) * RATE
            end = (end - origin) * RATE
            while begin < end:
                i = begin // CLOCK
                next_edge = min(end, (i + 1) * CLOCK)
                duty[i] += (next_edge - begin) / CLOCK
                begin = next_edge

    # Remove DC and normalize only the listening copy.
    feedback = exp(-2 * pi * 20 / RATE)
    previous = filtered = 0.0
    for i, value in enumerate(duty):
        filtered = value - previous + feedback * filtered
        duty[i] = filtered
        previous = value
    gain = 30000 / max(abs(value) for value in duty)
    pcm = array("h", (round(value * gain) for value in duty))
    if sys.byteorder != "little":
        pcm.byteswap()
    with wave.open(str(output), "wb") as wav:
        wav.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        wav.writeframes(pcm.tobytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.trace, args.output)
