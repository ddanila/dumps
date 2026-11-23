"""State encoding and flag selection for controller output byte RAM33."""

def output33(rom,state,flags23,flags24,input2d,output30):
    if not state&0x80:code=0;source='zero'
    elif state&0x40:code=0x5c;source='constant'
    else:
        source='0095' if state&0x20 else '00b5'
        code=rom[int(source,16)+(state&31)]
    if state&0xf8==0xe8:pair=6;reason='e8-group'
    elif flags24&0x40 or not (flags23&0x80 or input2d&0x80):pair=2;reason='default'
    elif not output30&0x20 or state==0xb3 or flags23&0x60:pair=4;reason='special-single'
    elif flags23&0x80 or (input2d&4 and not flags23&2):pair=6;reason='special-both'
    else:pair=0;reason='special-clear'
    value=(code&0xf8)|pair|((flags23>>5)&1)
    return dict(code=code,source=source,reason=reason,value=value,wire_value=value^0xf8)
