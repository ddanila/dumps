local m = manager.machine
local cpu = m.devices[':kbd:mcu']
local country = tonumber(os.getenv('FACIT_COUNTRY') or '224')
local log = assert(io.open('probe.tsv','w'))
log:write('kind\ttime\tpc\tvalue\n')
local accesses, reads, writes, lastp1, lastp2 = {}, 0, 0, -1, -1
taps = {}
taps[1] = cpu.spaces['program']:install_read_tap(0,0xfff,'kbd_probe',function(addr,data,mask)
    accesses[addr] = (accesses[addr] or 0)+1
    local p1 = cpu.state['P1'].value
    if p1 ~= lastp1 then
        log:write(string.format('P1\t%.9f\t%03x\t%02x\n',m.time:as_double(),cpu.state['PC'].value,p1))
        lastp1=p1
    end
end)
taps[2] = cpu.spaces['io']:install_read_tap(0,255,'matrix_probe',function(addr,data,mask)
    reads=reads+1
    if addr==1 and (cpu.state["P2"].value & 0x1f)==0 then return (data & 0x1f) | country end
end)
taps[3] = cpu.spaces['io']:install_write_tap(0,255,'speaker_probe',function(addr,data,mask) writes=writes+1 end)
m.debugger:command('dasm disassembly.txt,0,800,1,:kbd:mcu')
local frame=0
emu.register_frame_done(function()
    frame=frame+1
    local host=m.devices[':maincpu'].spaces['program']
    if (host:read_u8(0x6001) & 2) ~= 0 then log:write(string.format('RX\t%.9f\t000\t%02x\n',m.time:as_double(),host:read_u8(0x6000))) end
    if frame==80 then m.devices[':maincpu'].spaces['program']:write_u8(0x5000,0); log:write('HOST\t'..m.time:as_double()..'\t0\t00\n') end
    if frame==140 or frame==190 then m.ioport.ports[':kbd:A8'].fields['a  A']:set_value(1); log:write('KEY\t'..m.time:as_double()..'\t0\tA down\n') end
    if frame==150 or frame==200 then m.ioport.ports[':kbd:A8'].fields['a  A']:set_value(0); log:write('KEY\t'..m.time:as_double()..'\t0\tA up\n') end
    if frame==180 then m.ioport.ports[':kbd:A0'].fields['Shift']:set_value(1); log:write('KEY\t'..m.time:as_double()..'\t0\tShift down\n') end
    if frame==210 then m.ioport.ports[':kbd:A0'].fields['Shift']:set_value(0); log:write('KEY\t'..m.time:as_double()..'\t0\tShift up\n') end
end,'frame')
stop_subscription = emu.add_machine_stop_notifier(function()
    local n=0; for a,count in pairs(accesses) do n=n+1 end
    log:write(string.format('SUMMARY\t%.9f\t%03x\taddresses=%d matrix_reads=%d speaker_writes=%d\n',m.time:as_double(),cpu.state['PC'].value,n,reads,writes))
    for a=0,0xfff do if accesses[a] then log:write(string.format('FETCH\t0\t%03x\t%d\n',a,accesses[a])) end end
    log:close()
end)
