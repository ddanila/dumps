#!/usr/bin/env python3
"""Check both rt1715lc BIOS options using a MAME build containing the ROM declarations.
Usage: python3 check-bios-selection.py /absolute/path/to/mame
Host placeholders are deliberate: this tests ROM selection, not host boot.
"""
from pathlib import Path
import json, os, subprocess, sys, tempfile, xml.etree.ElementTree as ET
BASE = Path(__file__).resolve().parent
exe = str(Path(sys.argv[1]).resolve())
root = ET.fromstring(subprocess.check_output([exe, 'rt1715lc', '-listxml']))
m = next(m for m in root.findall('machine') if m.get('name') == 'rt1715lc')
bios = {b.get('name'): b.attrib for b in m.findall('biosset')}
assert set(bios) == {'jcuken', 'qwerty'} and bios['jcuken'].get('default') == 'yes', bios
results = {'biossets': bios, 'rom_loads': []}
with tempfile.TemporaryDirectory(prefix='s642-bios-') as tmp:
    p = Path(tmp)
    r = p / 'roms/rt1715lc'
    r.mkdir(parents=True)
    for name, size in [('s502.a25.3', 2048), ('s643.a25.2', 2048), ('s605.a25.1', 2048), ('068.a8.2', 1024), ('069.a8.1', 1024)]:
        (r / name).write_bytes(bytes([0x76 if name.startswith('s502') else 0]) * size)
    for name, source in [('s642.ic8', BASE.parent.parent / 'pc1715-keyboard-s642/s642.ic8'), ('s642-qwerty.bin', BASE.parent / 's642-qwerty.bin')]:
        (r / name).write_bytes(source.read_bytes())
    (p / 'probe.lua').write_text("local f=assert(io.open('loaded.bin','wb'));local s=manager.machine.devices[':keyboard'].spaces.program;for i=0,2047 do f:write(string.char(s:read_u8(i))) end;f:close();manager.machine:exit()\n")
    for option, name in [('jcuken', 's642.ic8'), ('qwerty', 's642-qwerty.bin'), ('default', 's642.ic8')]:
        (p / 'loaded.bin').unlink(missing_ok=True)
        cmd = [exe, 'rt1715lc']
        if option != 'default':
            cmd += ['-bios', option]
        cmd += ['-rompath', str(p / 'roms'), '-video', 'none', '-sound', 'none', '-nothrottle', '-skip_gameinfo', '-autoboot_delay', '0', '-autoboot_script', str(p / 'probe.lua'), '-seconds_to_run', '2', '-cfg_directory', str(p / 'cfg')]
        result = subprocess.run(cmd, cwd=p, env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, (option, result.stdout, result.stderr)
        assert (p / 'loaded.bin').read_bytes() == (r / name).read_bytes(), option
        results['rom_loads'].append({'bios': option, 'bytes_match': True, 'size': 2048})
        print('PASS: BIOS', option, 'loads exactly the intended 2048-byte dump')
(BASE / 'bios-selection-checks.json').write_text(json.dumps(results, indent=2) + '\n')
