"""Bit-serial reference for the controller's two 23-bit feedback transforms."""

def transform(history,value,short_delay,inverse=False):
    history&=(1<<23)-1
    output=0
    for bit in range(8):
        incoming=(value>>bit)&1
        outgoing=incoming^(history&1)^((history>>(23-short_delay))&1)
        output|=outgoing<<bit
        feedback=incoming if inverse else outgoing
        history=(history>>1)|(feedback<<22)
    return history,output
