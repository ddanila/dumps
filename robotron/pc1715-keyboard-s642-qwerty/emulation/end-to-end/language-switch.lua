-- Exercise the physical keyboard matrix with the unmodified S642 ROM and TOS/M.
local m = manager.machine
local frame = 0
local log = assert(io.open('language-switch.tsv', 'w'))
local ports = {}
rx_tap = m.devices[':maincpu'].spaces.io:install_read_tap(0x0c, 0x0f, 'keyboard_rx', function(a, d)
  if frame > 14900 and a == 0x0c then
    log:write(string.format('%d\trx\t%02x\n', frame, d))
  end
end)
font_tap = m.devices[':maincpu'].spaces.io:install_write_tap(0x1a, 0x1b, 'font_select', function(a, d)
  if frame > 14900 then
    ports[#ports + 1] = d
    log:write(string.format('%d\tfont\t%02x\n', frame, d))
  end
end)
stop_subscription = emu.add_machine_stop_notifier(function() log:close() end)
local function key(row, mask, value)
  for _, field in pairs(m.ioport.ports[':row_' .. row].fields) do
    if field.mask == mask then field:set_value(value); return end
  end
  error('Missing matrix key')
end
emu.register_frame_done(function()
  frame = frame + 1
  for _, start in ipairs({15000, 15200, 15400}) do
    for i, row in ipairs({'70', '20', '10', '00', '38', '48'}) do
      if frame == start + (i - 1) * 20 then key(row, 0x01, 1) end
      if frame == start + (i - 1) * 20 + 10 then key(row, 0x01, 0) end
    end
  end
  if frame == 15140 or frame == 15340 then key('08', 0x80, 1) end
  if frame == 15150 or frame == 15350 then key('08', 0x80, 0) end
  -- 0000 Latin; 0001 toggle alone; 0002 Cyrillic; 0003 Latin restored.
  if frame == 15130 or frame == 15190 or frame == 15330 or frame == 15530 then
    m.video:snapshot()
  end
  if frame == 15540 then
    assert(#ports == 2 and ports[1] == 0x10 and ports[2] == 0,
      'Expected TOS/M to select font 2 and then restore font 1')
    log:write('PASS: TOS/M requested both font transitions after S642 keypresses\n')
    log:flush()
    m:exit()
  end
end, 'frame')
