"""Reference for controller 0620 input decoding; bit names deliberately unassigned."""

def decode_inputs(payload,state,byte_6e):
    ram=[0]*128;ram[0x2a:0x30]=payload;ram[0x22:0x28]=state;ram[0x6e]=byte_6e
    def bit(address,n):return (ram[address]>>n)&1
    def put(address,n,value):ram[address]=(ram[address]&~(1<<n))|(int(bool(value))<<n)
    def b(n):return bit(0x2b,n)
    def c(n):return bit(0x2c,n)
    def e(n):return bit(0x2e,n)
    def f(n):return bit(0x2f,n)
    put(0x22,1,0)
    override=c(7) and c(6) and bit(0x2d,0) and all(b(n) for n in (1,0,3,2))
    if override:
        for address,n,value in ((0x2f,6,0),(0x2f,5,1),(0x2d,7,1),(0x2d,0,0),
                                (0x2b,1,0),(0x2e,7,0),(0x2e,6,0)):put(address,n,value)
    put(0x22,2,1)
    old=bit(0x22,3);put(0x20,0,old)
    mode=(b(4) if f(5) else 1) if f(6) else (0 if f(5) else c(7))
    put(0x22,3,mode);put(0x22,1,old^mode)
    for address,n in ((0x23,4),(0x23,5),(0x23,6),(0x23,7),(0x24,6)):put(address,n,0)
    if c(3):kind='c3';sets=[(0x23,4,1),(0x23,5,1),(0x24,6,c(4))]
    elif c(1):kind='c1';sets=[(0x23,4,1),(0x23,7,1)]
    elif c(2):kind='c2';sets=[(0x23,4,1),(0x23,6,1),(0x24,6,c(4))]
    elif c(4):kind='c4';sets=[(0x23,4,1),(0x24,6,1)]
    elif b(2) and b(1):kind='b2_b1';sets=[(0x23,4,1),(0x23,5,1)]
    elif b(3) and bit(0x2d,0):kind='b3_d0';sets=[(0x23,4,1),(0x23,6,1)]
    else:kind='none';sets=[]
    for address,n,value in sets:put(address,n,value)
    flag= b(6) or bit(0x24,6) or c(2) or bit(0x23,7)
    signal=bit(0x2a,7) or bit(0x2a,5)
    timed='both' if bit(0x22,5) or byte_6e==255 else 'clear'
    if c(3):action='only4'
    elif not mode:action=('only4' if flag else 'clear') if f(0) else 'only4'
    elif f(4):
        if f(3):
            put(0x2f,2,1)
            action='keep5' if signal or bit(0x23,5) else timed
        else:action='only4' if flag else 'clear'
    elif f(3):
        if (signal or bit(0x23,5)) and flag:action='keep5'
        elif b(6) or bit(0x24,6) or bit(0x23,7):action=timed
        else:action='clear'
    else:
        put(0x2f,2,1)
        action='keep5' if signal else timed if c(6) else 'clear'
    put(0x22,4,action!='clear')
    if action!='keep5':put(0x22,5,action=='both')
    if bit(0x22,5):first=1
    elif e(5):first=b(4) if e(4) else 1
    else:first=0 if e(4) else bit(0x2a,5)
    put(0x23,1,first)
    if e(3):pair=(1,1)
    elif e(2):pair=(not b(5),b(5)) if e(1) else (0,1)
    else:pair=(1,0) if e(1) else (c(5),not c(5))
    put(0x23,2,pair[0]);put(0x23,3,pair[1])
    return dict(ram=ram,override=bool(override),priority=kind,action=action)
