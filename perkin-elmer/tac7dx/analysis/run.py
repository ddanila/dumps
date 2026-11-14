#!/usr/bin/env python3
"""Run TAC7/DX code on MAME 0.251's 6809 with synthetic peripherals."""
from pathlib import Path
import argparse
import os
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--seconds', type=int, default=16)
parser.add_argument('--scenario', choices=['synthetic', 'missing-clock', 'bad-rom'],
                    default='synthetic')
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--irq-test', action='store_true')
mode.add_argument('--request', help='ASCII command including $; CR appended')
parser.add_argument('--output', help='Output directory, relative to this script or absolute')
args = parser.parse_args()
if args.seconds <= 0:
    parser.error('--seconds must be positive')
if args.request is not None:
    if not args.request.isascii() or len(args.request) > 1000:
        parser.error('--request must be ASCII and at most 1000 characters')
    default_output = 'results/query'
elif args.irq_test:
    default_output = 'results/irq'
else:
    default_output = 'results/boot' if args.scenario == 'synthetic' else 'results/' + args.scenario
out = (BASE / (args.output or default_output)).resolve()
if (args.request is not None or args.irq_test) and out == BASE / 'results/boot':
    parser.error('Function tests cannot overwrite their boot snapshot')
out.mkdir(parents=True, exist_ok=True)
# Keep modes independent even if the caller has exported previous test variables.
env = {k: v for k, v in os.environ.items() if not k.startswith('TAC_')}
env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
           TAC_ROMDIR=str(BASE.parent), TAC_SCENARIO=args.scenario)
if args.request is not None:
    env['TAC_REQUEST'] = args.request + '\r'
if args.irq_test:
    env['TAC_IRQ_TEST'] = '1'
if args.request is not None or args.irq_test:
    env.update(TAC_SNAPSHOT=str(BASE / 'results/boot/memory.bin'),
               TAC_PIA_SNAPSHOT=str(BASE / 'results/boot/peripheral-state.txt'),
               TAC_HIGH_SNAPSHOT=str(BASE / 'results/boot/highram.bin'))
with tempfile.TemporaryDirectory(prefix='tac7dx-') as temporary:
    temp = Path(temporary)
    (temp / 'cpu09').mkdir()
    (temp / 'cpu09/tavbug.bin').write_bytes(bytes(4096))
    command = ['/usr/games/mame', 'cpu09', '-rompath', temporary, '-video', 'none',
               '-sound', 'none', '-nothrottle', '-skip_gameinfo',
               '-seconds_to_run', str(args.seconds), '-autoboot_delay', '0',
               '-autoboot_script', str(BASE / 'probe.lua'), '-debug', '-debugger',
               'none', '-cfg_directory', str(temp / 'cfg'),
               '-nvram_directory', str(temp / 'nvram')]
    result = subprocess.run(command, cwd=out, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=120)
    (out / 'mame.log').write_text(result.stdout)
    result.check_returncode()
    if 'LUA ERROR' in result.stdout:
        raise RuntimeError(result.stdout)
    listing = out / 'disassembly.txt'
    if listing.exists():
        listing.write_text('\n'.join(line.rstrip() for line in listing.read_text().splitlines()) + '\n')
print(out)
