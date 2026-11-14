local m=manager.machine
local cpu=m.devices[':maincpu']
local space=cpu.spaces['program']
local mem={}
for a=0,65535 do mem[a]=0 end
local function load(path,start,size,offset)
 local f=assert(io.open(path,'rb'));local s=f:read('a');f:close()
 for i=0,size-1 do mem[start+i]=s:byte(offset+i+1) end
end
load(os.getenv('TAC_ROMDIR')..'/u35-n5208003-27256-read.bin',0x4000,0x4000,0x4000)
load(os.getenv('TAC_ROMDIR')..'/u36-n5208004-27256-read.bin',0x8000,0x8000,0)
local log=assert(io.open('io.tsv','w'));log:write('kind\tpc\taddress\tvalue\n')
local reads,writes={},{}
local highram={}
for a=0x8000,0xffff do highram[a]=0 end
local ram_enabled=false
local scenario=os.getenv('TAC_SCENARIO') or 'synthetic'
local irq_test=os.getenv('TAC_IRQ_TEST')
if scenario=='bad-rom' then mem[0x4002]=mem[0x4002]~1 end
local serial=assert(io.open('serial.tsv','w'));serial:write('kind\tport\tbyte\n')
local rx={[0x3080]={},[0x3100]={}}
local command={[0x3080]=0,[0x3100]=0}
local pia={}
for _,base in ipairs({0x3004,0x3008,0x3010,0x3020,0x3040}) do pia[base]={ddr={0,0},out={0,0},ctrl={0,0}} end
local polls=0
local inject=false
local checkpoints={[0x8002]='reset',[0xa003]='ROM-check-return',[0xa017]='RAM-check-return',[0xa021]='PIA-check-return',[0xa02c]='clock-check-return',[0xa037]='type-check-return',[0xa042]='analog-check-return',[0xa04d]='serial-check-return',[0x50cf]='main-loop',[0xa057]='diagnostic-failure',[0xa354]='diagnostic-command-loop'}
local seen={}
checkpoints[0xa56a]='IRQ-entry'
checkpoints[0xa59c]='periodic-service'
checkpoints[0x41f5]='channel-scan'
checkpoints[0xa59b]='IRQ-return'
checkpoints[0x2f00]='test-return'
local running=false
local function input(base,port)
 if base==0x3010 and port==1 then return 0x10 end -- synthetic instrument type 1
 if base==0x3020 and port==1 then
  return (pia[0x3004].out[1]>=128) and 0x80 or 0
 end
 return 0
end
local function peripheral_read(a)
 for base,p in pairs(pia) do
  if a>=base and a<base+4 then
   local r=a-base;local port=(r%2)+1
   if r>=2 then
    local v=p.ctrl[port]
    if irq_test and base==0x3004 and port==1 then return v|0x40 end
    if base==0x3004 and port==1 and v==0x1c and scenario~='missing-clock' then
     polls=polls+1;if polls>=110 then v=v|0x40 end
    end
    return v
   end
   if (p.ctrl[port]&4)==0 then return p.ddr[port] end
   if base==0x3004 and port==1 then polls=0 end
   return (p.out[port]&p.ddr[port]) | (input(base,port)&(~p.ddr[port]&255))
  end
 end
 for base,q in pairs(rx) do
  if a==base then local v=table.remove(q,1) or 0;serial:write(string.format('RX\t%04x\t%02x\n',base,v));return v end
  if a==base+1 then return 5 | ((#q>0) and 2 or 0) end
 end
 return mem[a]
end
local function peripheral_write(a,d)
 for base,p in pairs(pia) do
  if a>=base and a<base+4 then
   local r=a-base;local port=(r%2)+1
   if r>=2 then p.ctrl[port]=d&63
   elseif (p.ctrl[port]&4)==0 then p.ddr[port]=d else p.out[port]=d end
   return
  end
 end
 for base,q in pairs(rx) do
  if a==base+3 then command[base]=d end
  if a==base then
   serial:write(string.format('TX\t%04x\t%02x\n',base,d))
   if (command[base]&0x80)~=0 then table.insert(q,d) end
  end
 end
end
local count=0
local function record(kind,a,d)
 count=count+1
 if count<2000 then log:write(string.format('%s\t%04x\t%04x\t%02x\n',kind,cpu.state['PC'].value,a,d)) end
end
taps={}
taps[1]=space:install_read_tap(0,65535,'tacread',function(a,d,mask)
 reads[a]=(reads[a] or 0)+1
 if running and checkpoints[a] and not seen[a] and a+1==cpu.state['PC'].value then
  seen[a]=true
  log:write(string.format('CHECK %s A=%02x B=%02x DP=%02x S=%04x\n',checkpoints[a],cpu.state['A'].value,cpu.state['B'].value,cpu.state['DP'].value,cpu.state['S'].value))
 end
 if running and a==0xa06f and a+1==cpu.state['PC'].value and not inject then
  inject=true;for c in ('%\r'):gmatch('.') do table.insert(rx[0x3080],string.byte(c)) end
 end
 if a>=0x8000 and ram_enabled then return highram[a] end
 if a>=0x3000 and a<0x4000 then local v=peripheral_read(a);record('R',a,v);return v end
 return mem[a]
end)
taps[2]=space:install_write_tap(0,65535,'tacwrite',function(a,d,mask)
 writes[a]=(writes[a] or 0)+1
 if a>=0x3000 then record('W',a,d) end
 if a>=0x3000 and a<0x4000 then peripheral_write(a,d) end
 if a==0x3200 or a==0x3000 then ram_enabled=true end
 if a==0x3201 or a==0x3001 then ram_enabled=false end
 if a>=0x8000 and ram_enabled then highram[a]=d end
 if a<0x4000 then mem[a]=d end
 return 0 -- underlying carrier device receives zero, never TAC control values
end)
if not os.getenv('TAC_REQUEST') and not irq_test and scenario=='synthetic' then m.debugger:command('dasm disassembly.txt,4000,c000,1') end
reads={};writes={};running=true

for _,r in ipairs({'A','B','DP','X','Y','U','S'}) do cpu.state[r].value=0 end
cpu.state['CC'].value=0x50
cpu.state['PC'].value=0x8002
local request=os.getenv('TAC_REQUEST')
if request or irq_test then
 load(os.getenv('TAC_SNAPSHOT'),0,0x3000,0)
 local f=assert(io.open(os.getenv('TAC_HIGH_SNAPSHOT'),'rb'));local s=f:read('a');f:close()
 for a=0x8000,0xffff do highram[a]=s:byte(a-0x8000+1) end
 local f=assert(io.open(os.getenv('TAC_PIA_SNAPSHOT'),'r'))
 for line in f:lines() do
  local b,p,d,o,c=line:match('^(%d+) (%d+) (%d+) (%d+) (%d+)$')
  if b then local q=pia[tonumber(b)];p=tonumber(p);q.ddr[p]=tonumber(d);q.out[p]=tonumber(o);q.ctrl[p]=tonumber(c) end
 end
 f:close()
 local function word(a,v) mem[a]=(v>>8)&255;mem[a+1]=v&255 end
 mem[0x2f00]=0x20;mem[0x2f01]=0xfe
 if request then
 word(0x0549,0);word(0x054b,#request)
 for i=1,#request do mem[0x054f+i]=request:byte(i) end
 word(0x0ba9,0);word(0x0bab,0)
 cpu.state['S'].value=0x1c7c;word(0x1c7c,0x2f00)
 cpu.state['PC'].value=0xa831;word(0xfffe,0xa831) -- test-only reset entry; original ROM files untouched
 else
  -- Full 6809 interrupt frame: CC,A,B,DP,X,Y,U,PC. RTI restores sentinel PC.
  for a=0x1c70,0x1c7b do mem[a]=0 end
  mem[0x1c70]=0xc0;word(0x1c7a,0x2f00)
  cpu.state['S'].value=0x1c70;cpu.state['PC'].value=0xa56a;word(0xfffe,0xa56a)
 end
end
local frames=0
emu.register_frame_done(function()
 frames=frames+1
 if frames%10==0 then log:write(string.format('PC\t%04x\t0000\t00\n',cpu.state['PC'].value)) end
end,'frame')
stop_subscription=emu.add_machine_stop_notifier(function()
 log:write(string.format('END\t%04x\t%04x\t%02x\n',cpu.state['PC'].value,cpu.state['S'].value,cpu.state['CC'].value));log:close();serial:close()
 local f=assert(io.open('registers.tsv','w'));for k,v in pairs(cpu.state) do f:write(k..'\t'..v.value..'\n') end;f:close()
 local f=assert(io.open('peripheral-state.txt','w'));for b,p in pairs(pia) do for i=1,2 do f:write(string.format('%d %d %d %d %d\n',b,i,p.ddr[i],p.out[i],p.ctrl[i])) end end;f:close()
 local f=assert(io.open('memory.bin','wb'));for a=0,65535 do f:write(string.char(mem[a])) end;f:close()
 local f=assert(io.open('highram.bin','wb'));for a=0x8000,0xffff do f:write(string.char(highram[a])) end;f:close()
 f=assert(io.open('accesses.tsv','w'));f:write('address\treads\twrites\n');for a=0,65535 do if reads[a] or writes[a] then f:write(string.format('%04x\t%d\t%d\n',a,reads[a] or 0,writes[a] or 0)) end end;f:close()
end)
