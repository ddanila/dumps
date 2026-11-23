"""Event accumulator and polling qualification, without physical signal labels."""

def edge(low,high,accumulator,initial_ie=0):
    added=0
    if accumulator<128 and high==255 and 0xbd<=low<=0xf2:
        added=(256-low)//4
    return dict(low=255,high=255,accumulator=(accumulator+added)&255,added=added,ie=(initial_ie|8)&~4)


def qualify(low,high,accumulator,mode,out0,out1,state22,initial_ie=0):
    ie=initial_ie;action='hold';reset=False
    if high==255 and low>=0x60:
        if low<0xfb:ie|=4
    else:
        ie|=4;accumulator&=0x3f;out0&=0xfb;out1&=0xef;action='clear-outputs'
        if mode==0:state22&=0xdf
        if mode==0 or high<0xd9:
            accumulator=0;high=0xd8;low=0xf0;ie|=8;action='restart';reset=True
    if not reset and accumulator<128:
        if 40<=accumulator<63:
            accumulator=0xbf;out0|=4;out1|=16;action+=':latch-bf'
        elif accumulator>=103:
            accumulator=0xff;out0|=4;out1|=16;action+=':latch-ff'
    return dict(low=low,high=high,accumulator=accumulator,out0=out0,out1=out1,state22=state22,ie=ie,action=action)
