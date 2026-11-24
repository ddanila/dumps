local m=manager.machine
local cpu=m.devices[':keyboard']
local log=assert(io.open('trace.tsv','w'))
local function emit(kind, text) log:write(string.format('%s\t%.9f\t%s\n',kind,m.time:as_double(),text)) end
taps={}
local reads=0
taps[1]=cpu.spaces['io']:install_read_tap(0x8000,0x9fff,'matrix',function(a,d,mask) reads=reads+1 end)
taps[2]=cpu.spaces['io']:install_write_tap(0,0x1fff,'serial',function(a,d,mask) emit('BIT',tostring(d&1)) end)
for tag,p in pairs(m.ioport.ports) do
 for name,f in pairs(p.fields) do emit('FIELD',tag..' '..name..' '..f.mask) end
end
m.debugger:command('dasm disassembly.txt,0,800,1,:keyboard')
local function key(tag,mask,v)
 for name,f in pairs(m.ioport.ports[tag].fields) do if f.mask==mask then f:set_value(v); emit('KEY',name..' '..v); return end end
 error('field missing')
end
local cases={}
local rows={'00','10','20','30','40','50','60','70','18','28','38','48'}
for _,row in ipairs(rows) do
 for bit=0,7 do
  local found=false
  for _,f in pairs(m.ioport.ports[':row_'..row].fields) do if f.mask==(1<<bit) then found=true end end
  if found then table.insert(cases,{name='matrix_'..row..'_'..bit,tag=':row_'..row,mask=1<<bit}) end
 end
end
for _,name in ipairs({'plain','shift','control','caps','caps_shift','siso','siso_shift','repeat','repress'}) do
 table.insert(cases,{name=name,tag=':row_70',mask=0x20})
end
local frame=0
local index=0
local current=nil
local function releaseall()
 for tag,p in pairs(m.ioport.ports) do
  if tag:match('^:row_') then for _,f in pairs(p.fields) do f:set_value(0) end end
 end
end
emu.register_frame_done(function()
 frame=frame+1
 local phase=(frame-1)%150
 if phase==0 then
  index=index+1
  current=cases[index]
  if not current then m:exit(); return end
  releaseall()
  -- Restart firmware initialization for independent modifier and lock state.
  cpu.state['PC'].value=0
  emit('CASE',current.name)
 end
 if not current then return end
 if phase==15 then
  if current.name:match('shift') then key(':row_08',2,1) end
  if current.name=='control' then key(':row_08',1,1) end
  if current.name:match('caps') then key(':row_08',0x20,1) end
  if current.name:match('siso') then key(':row_08',0x80,1) end
 end
 if phase==22 then
  if current.name:match('caps') then key(':row_08',0x20,0) end
  if current.name:match('siso') then key(':row_08',0x80,0) end
 end
 if phase==30 then key(current.tag,current.mask,1) end
 if phase==45 and current.name~='repeat' then key(current.tag,current.mask,0) end
 if phase==70 and current.name=='repress' then key(current.tag,current.mask,1) end
 if phase==85 and current.name=='repress' then key(current.tag,current.mask,0) end
 if phase==120 then releaseall(); emit('RELEASE','all') end
end,'frame')
stop_subscription=emu.add_machine_stop_notifier(function() emit('END','matrix_reads='..reads..' pc='..cpu.state['PC'].value); log:close() end)
