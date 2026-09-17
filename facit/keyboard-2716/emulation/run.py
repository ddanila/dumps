#!/usr/bin/env python3
"""Run the captured ROM in MAME's F4431 keyboard (host Z80 halted)."""
from pathlib import Path
import os, subprocess, tempfile
BASE = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='facit-kbd-') as tmp:
    root = Path(tmp)
    roms = root/'f4431'; roms.mkdir()
    for name, size in [('11420050-00_4431.d73',4096),('11420060-00_4431.d74',4096),('11420070-00_4431.d75',4096),('11419840-00_cg30.d40',2048),('11419950-00_4431.d57',2048),('11419960-00_4431.d19',32),('earom.d63',200)]:
        (roms/name).write_bytes(bytes([0x76 if size==4096 else 0])*size)
    (roms/'11419660-00_kb31.u3').write_bytes((BASE.parent/'keyboard.bin').read_bytes())
    cmd=['/usr/games/mame','f4431','-rompath',str(root),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-seconds_to_run','4','-autoboot_delay','0','-autoboot_script',str(BASE/'probe.lua'),'-debug','-debugger','none','-cfg_directory',str(root/'cfg'),'-nvram_directory',str(root/'nvram')]
    r=subprocess.run(cmd,cwd=BASE,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60)
    (BASE/'mame.log').write_text(r.stdout)
    r.check_returncode()
    if 'LUA ERROR' in r.stdout: raise RuntimeError(r.stdout)
    trace = (BASE/'probe.tsv').read_text()
    received = [int(line.split('\t')[3], 16) for line in trace.splitlines() if line.startswith('RX\t')]
    country = int(os.environ.get('FACIT_COUNTRY', '224'))
    expected = {224: [0xff, 0x61, 0x41], 192: [0xff, 0x66, 0x46]}
    if country in expected:
        assert received == expected[country], f"Unexpected UART output: {received}"
    print(trace.split('FETCH')[0])
