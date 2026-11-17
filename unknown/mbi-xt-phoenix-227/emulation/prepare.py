#!/usr/bin/env python3
"""Prepare an isolated 86Box XT VM using supplied DOS 5 disk and device ROMs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dos-disk', type=Path, required=True,
                        help='Original MS-DOS 5.00 720 KiB DISK1.IMG')
    parser.add_argument('--roms', type=Path, required=True,
                        help='86Box device ROM collection root')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--raw', action='store_true', help='Unmodified control')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw = (here.parent / 'mbi-xt-phoenix-227-raw.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '3f2b7bce83b44a0c5fe49a115a9c7cd174c6721c9c7c9c0371dc77ea17b107eb'
    bios = bytearray(raw)
    if not args.raw:
        bios[0x1f3a] = 0x42
        assert sum(bios) % 256 == 0
    roms = output / 'roms'
    (roms / 'machines/genxt').mkdir(parents=True)
    for path in args.roms.resolve().iterdir():
        if path.name != 'machines':
            (roms / path.name).symlink_to(path, target_is_directory=path.is_dir())
    (roms / 'machines/genxt/pcxt.rom').write_bytes(bios)
    image = output / 'dos5-360.img'
    image.write_bytes(bytes(360 * 1024))
    run('mformat', '-i', image, '-f', '360', '::')
    disk = bytearray(image.read_bytes())
    boot = bytearray(args.dos_disk.read_bytes()[:512])
    assert boot[510:512] == b'\x55\xaa'
    boot[11:36] = disk[11:36]  # 360 KiB BPB; retain DOS boot code.
    disk[:512] = boot
    image.write_bytes(disk)
    for name in ('IO.SYS', 'MSDOS.SYS', 'COMMAND.COM'):
        run('mcopy', '-i', args.dos_disk, '::' + name, output / name)
        run('mcopy', '-i', image, output / name, '::' + name)
    run('nasm', '-f', 'bin', here / 'bioschk.asm', '-o', output / 'BIOSCHK.COM')
    for name in ('BIOSCHK.COM', 'AUTOEXEC.BAT'):
        source = output / name if name.endswith('.COM') else here / name
        run('mcopy', '-i', image, source, '::' + name)
    disk = bytearray(image.read_bytes())
    disk[-512:] = bytes([0xa5]) * 512
    image.write_bytes(disk)
    shutil.copy2(here / '86box.cfg', output / '86box.cfg')
    (output / 'global.cfg').write_text(
        '[Emulator]\ndo_auto_pause = 0\ndo_auto_dialog_pause = 0\n'
        'confirm_reset = 0\nconfirm_exit = 0\nconfirm_save = 0\n')
    record = {'raw_control': args.raw, 'bios_sha256': hashlib.sha256(bios).hexdigest(),
              'dos_source_sha256': sha(args.dos_disk), 'initial_disk_sha256': sha(image),
              'probe_sha256': sha(output / 'BIOSCHK.COM'),
              'dos_files': {n: sha(output / n) for n in ('IO.SYS', 'MSDOS.SYS', 'COMMAND.COM')}}
    (output / 'inputs.json').write_text(json.dumps(record, indent=2) + '\n')
    print(f'Prepared {output}; launch 86Box with -P, -O and -R pointing here.')


if __name__ == '__main__':
    main()
