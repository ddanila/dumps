local m=manager.machine
local cpu=m.devices[':keyboard']
local log=assert(io.open('trace.tsv','w'))
local function emit(k,v) log:write(string.format('%s\t%.9f\t%s\n',k,m.time:as_double(),v)) end
taps={}
taps[1]=cpu.spaces['io']:install_write_tap(0,0x1fff,'serial',function(a,d,mask) emit('BIT',tostring(d&1)) end)
taps[2]=cpu.spaces['io']:install_read_tap(0x2000,0x2000,'language_led',function(a,d,mask) emit('LED','language') end)
taps[3]=cpu.spaces['io']:install_read_tap(0xa000,0xa000,'language_led_mirror',function(a,d,mask) emit('LED','language') end)
local function key(tag,mask,value)
 for _,f in pairs(m.ioport.ports[tag].fields) do if f.mask==mask then f:set_value(value); return end end
 error('missing '..tag..' '..mask)
end
local cases={}
for mode=0,2 do
 if mode>0 then table.insert(cases,{name='toggle_'..mode,tag=':row_08',mask=0x80}) end
 for shift=0,1 do
  for _,row in ipairs({'00','10','20','30','40','50','60','70','18','28','38','48'}) do
   for bit=0,7 do
    local found=false
    for _,f in pairs(m.ioport.ports[':row_'..row].fields) do if f.mask==1<<bit then found=true end end
    if found then table.insert(cases,{name=string.format('mode%d_shift%d_%s_%d',mode,shift,row,bit),tag=':row_'..row,mask=1<<bit,shift=shift}) end
   end
  end
 end
end
local frame=0
local index=0
local current=nil
emu.register_frame_done(function()
 frame=frame+1
 local phase=(frame-1)%50
 if phase==0 then
  index=index+1; current=cases[index]
  if not current then m:exit(); return end
  emit('CASE',current.name)
  key(':row_08',2,current.shift or 0)
 end
 if phase==15 then key(current.tag,current.mask,1); emit('DOWN',current.tag..' '..current.mask) end
 if phase==25 then key(current.tag,current.mask,0); emit('UP',current.tag..' '..current.mask) end
end,'frame')
stop_subscription=emu.add_machine_stop_notifier(function() emit('END','complete'); log:close() end)
