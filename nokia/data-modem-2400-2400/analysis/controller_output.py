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


def output01(state,previous0,previous1,flags,payload):
    a,b,c,d,e,f=payload;flag22,flag23,flag24=flags[:3]
    def bit(value,n):return (value>>n)&1
    values=[0]*8;values[2]=bit(previous0,2)
    if bit(flag22,4):values[7]=1
    elif bit(flag22,3):
        if bit(f,3):values[7]=1 if bit(f,4) else bit(b,6)|bit(flag23,4)
        else:values[7]=0 if bit(f,4) else bit(c,6)
    else:values[7]=not bit(f,0)
    values[6]=bool(state&0x80 and (state&0x40 or (state&31)>=3))
    if state in (0xb6,0x96,0x93,0x95,0xb5) or state&0xf8==0xe0:values[5]=1
    elif state&0xfc==0xc0 or state&0xe8==0xe8:values[5]=bit(a,2)
    else:values[5]=0
    if state==0xc1 or state&0xe8==0xe8:values[4]=bit(a,2)
    else:values[4]=1 if bit(flag24,6) or not bit(e,0) else bit(b,7)
    values[4]&=values[6]
    first_group=state in (0xb6,0x96,0xc0,0xb7) or (state&0xe8==0xe0 and state not in (0xe0,0xe4,0xf0,0xf4))
    if first_group:values[3]=bit(b,7) if bit(e,0) else 1
    elif state==0xc1 or state&0xe8==0xe8:values[3]=bit(a,2)
    else:values[3]=state in (0xc2,0xe4,0xc3)
    values[1]=bool(state&12 or state&3==3) if state&0xe0==0xe0 else bit(flag23,4)
    values[0]=bit(d,7)
    out0=sum(int(v)<<i for i,v in enumerate(values))
    values=[0]*8;values[4]=bit(previous1,4)
    if not (bit(flag23,7) or bit(flag24,6) or state&0xe8==0xe8):
        values[7]=first_group;values[6]=bit(out0,6);values[5]=bit(out0,5)
    values[3]=bit(out0,1)
    if state&0x80 and not state&0x40 and (state&31)<9:values[2]=0
    else:
        values[2]=bit(flag23,3)
        if not bit(flag23,5) and bit(e,3) and bit(e,6):values[2]&=bit(flag24,3)
    values[1]=bit(flag22,4) if state!=0 and bit(flag22,3) and not bit(flag23,5) else 0
    values[0]=not values[2]
    out1=sum(int(v)<<i for i,v in enumerate(values))
    return dict(out0=out0,out1=out1,psw_f0=int(first_group),wire=[out0,out1^3])


def output32(rom,state,previous,flags,input_c,count49,count4a,count65):
    code=output33(rom,state,0,0,0,0)['code']
    flag22,flag23,flag24=flags[:3]
    changed=bool(flag24&0x20);value=previous
    def put(bit,on):
        nonlocal value
        value=(value&~(1<<bit))|(int(bool(on))<<bit)
    if state in (0xc2,0xc3,0xe4):
        action='special';put(7,1)
        if changed or input_c&1:
            count49=count4a=0;put(5,1);action='special-reset'
        else:
            put(5,0)
            total=count4a+0xf6;temp=total&255;carry=int(total>255);subtract=True
            if temp<128:
                total=temp+0xfb;temp=total&255;carry=int(total>255)
                count49=(count49+1)&255
                if temp<128:count49=(count49-1)&255;subtract=False
            if subtract:
                temp=(count49-0x15-carry)&255
                if temp<128:
                    count49=temp;value^=0x40;count4a=(count4a+1)&255;action='special-toggle'
    elif state&0x40 or state in (0xb6,0x96,0xb7):put(7,0);action='disabled'
    else:
        put(7,1)
        if changed:put(5,1);count49=10;action='reload-ten'
        elif value&0x20:
            if count49:count49-=1;action='hold-countdown'
            else:
                put(5,0);action='table-reload'
                raw=rom[0x1be+(state&63)] if state&0x80 else 0
                count49=((raw<<2)|(raw>>6))&255
        else:
            put(5,0);action='countdown'
            if count49:
                count49-=1
                if count49&3==3:value^=0x40;action='countdown-toggle'
    if changed:count65=0;put(4,0)
    elif flag23&0x20:put(4,0)
    else:put(4,((count65+0xec)&255)<128)
    put(3,code&1);put(2,state==0 and changed)
    if code&4:pair=2 if flag23&0x20 or flag22&8 else 1
    else:pair=2 if state in (0,1) else 0
    value=(value&~3)|pair
    return dict(code=code,value=value,count49=count49,count4a=count4a,count65=count65,action=action)


def output_build(rom,state,previous,flags,payload,counters,patterns,initial_p1):
    """Compose 006E–046A, including rotating P1 patterns and C0 override."""
    fourth=output33(rom,state,flags[1],flags[2],payload[3],previous[0])
    third=output32(rom,state,previous[2],flags,payload[2],*counters)
    pair=output01(state,*previous[:2],flags,payload)
    values=[pair['out0'],pair['out1'],third['value'],fourth['value']]
    rotated=[];p1=initial_p1
    for pattern,output_bit,pin in zip(patterns,(3,5),(3,4)):
        if values[0]&(1<<output_bit):
            pattern=((pattern<<1)|(pattern>>7))&255
            level=pattern>>7
        else:pattern=255;level=1
        rotated.append(pattern)
        p1=(p1&~(1<<pin))|(level<<pin)
    p1=(p1&~32)|((fourth['code']&2)<<4)
    scratch=values[0]
    if payload[2]&1:values[0]|=254;p1&=~24
    return dict(values=values,code=fourth['code'],psw_f0=pair['psw_f0'],
                counters=[third['count49'],third['count4a'],third['count65']],
                patterns=rotated,p1=p1,scratch=scratch)
