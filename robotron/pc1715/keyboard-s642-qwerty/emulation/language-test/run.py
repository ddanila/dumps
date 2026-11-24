#!/usr/bin/env python3
"""Isolated keyboard firmware test. Host CPU runs a dummy HALT ROM."""
from pathlib import Path
import os, subprocess, tempfile, sys
BASE = Path(__file__).resolve().parent
rom = Path(sys.argv[1]) if len(sys.argv)>1 else BASE.parent.parent/'s642-qwerty.bin'
with tempfile.TemporaryDirectory(prefix='s642-test-') as tmp:
    root=Path(tmp); d=root/'rt1715'; d.mkdir()
    for name,size in [('s502.a25.3',2048),('s619.a25.2',2048),('s602.a25.1',2048),('068.a8.2',1024),('069.a8.1',1024)]:
        (d/name).write_bytes(bytes([0x76 if name=='s502.a25.3' else 0])*size)
    (d/'s600.ic8').write_bytes(rom.read_bytes())
    cmd=['/usr/games/mame','rt1715','-rompath',str(root),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-seconds_to_run','600','-autoboot_delay','0','-autoboot_script',str(BASE/'probe.lua'),'-debug','-debugger','none','-cfg_directory',str(root/'cfg'),'-nvram_directory',str(root/'nvram')]
    r=subprocess.run(cmd,cwd=BASE,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
    (BASE/'mame.log').write_text(r.stdout)
    print(r.stdout)
    r.check_returncode()
    assert 'LUA ERROR' not in r.stdout
