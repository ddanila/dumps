import pathlib,sys,subprocess,tempfile
lo,hi=(int(x,16) for x in sys.argv[1:3]);n=max(0,(lo-0x8000)//0x8000);a=lo-n*0x8000 if lo>=0x8000 else lo
b=(pathlib.Path(__file__).resolve().parents[2]/'mac304-m27c2001.bin').read_bytes()
assert 0 <= lo < hi <= 0x28000 and lo//0x8000 == (hi-1)//0x8000, 'Select a range inside one populated 32 KiB region'
with tempfile.NamedTemporaryFile(dir=pathlib.Path(__file__).parent) as f:
 f.write(b[:0x8000]+b[0x8000+n*0x8000:0x10000+n*0x8000]);f.flush()
 subprocess.run(['r2','-q','-a','8051','-e','scr.color=0','-e','asm.comments=false','-e','asm.lines=false','-c',f'pD {hi-lo} @ {a};q',f.name])
