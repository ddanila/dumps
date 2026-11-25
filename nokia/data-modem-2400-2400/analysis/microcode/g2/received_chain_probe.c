/* Receive a USART frame, then preserve one 8031 image through four states/sends. */
#define main interface_probe_original_main
#include "../../interface_probe.c"
#undef main

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    unsigned selector=strtoul(argv[2],0,0);
    if (selector>255) return 2;
    FILE *rom=fopen(argv[1],"rb"); if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
    c.except=exception; c.xread=xread; c.xwrite=xwrite;
    reset(&c,0);
    for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    decoding_probe=1; memset(decode_seen,0,sizeof decode_seen);
    errors=event_count=0;
    c.mSFR[REG_SP]=113;
    c.mLowerData[112]=0x00; c.mLowerData[113]=0x1f; /* RET sentinel 1F00 */
    c.mPC=0x800;
    unsigned char input[7]={0xa5,0,0,0,0,(unsigned char)selector,0};
    unsigned received=0,rx_due=0;
    for (cycle=0;cycle<1000 && c.mPC!=0x1f00;cycle++) {
        tick(&c);
        if ((c.mSFR[REG_SCON]&0x11)==0x10 && received<7) {
            if (!rx_due) rx_due=cycle+8;
            if (cycle>=rx_due) {
                c.mSFR[REG_SBUF]=input[received++];
                c.mSFR[REG_SCON]|=1;
                rx_due=0;
            }
        }
    }
    if (c.mPC!=0x1f00 || received!=7 || errors) return 3;
    unsigned stored=c.mLowerData[0x2e];
    c.mLowerData[0x34]=0xa0;
    c.mLowerData[0x22]|=0x10;
    c.mSFR[REG_IE]=0;
    printf("{\"received\":%u,\"selector\":%u,\"stored_2e\":%u,\"rows\":[",
           received,selector,stored);
    for (unsigned step=0;step<4;step++) {
        unsigned before=c.mLowerData[0x34];
        c.mLowerData[0x24]&=(unsigned char)~0x20;
        c.mLowerData[0x17]=0x80; c.mLowerData[0x16]=0;
        c.mLowerData[0x15]=0;
        c.mPC=0x1000;
        unsigned state_cycles=0;
        for (;state_cycles<200 && c.mPC!=0x1755;state_cycles++,cycle++) tick(&c);
        if (c.mPC!=0x1755 || errors) return 4;
        unsigned after=c.mLowerData[0x34];
        unsigned first_event=event_count;
        c.mPC=0x1ee2; sending=1; tx_due=0;
        unsigned completed=0;
        for (unsigned count=0;count<2000 && c.mPC!=0x1ee8;count++,cycle++) {
            tick(&c);
            if (tx_due && cycle>=tx_due) {
                c.mSFR[REG_SCON]|=2; tx_due=0; completed++;
            }
        }
        if (c.mPC!=0x1ee8 || errors) return 5;
        unsigned wire[4]={0},writes=0;
        for (unsigned i=first_event;i<event_count;i++)
            if (!strcmp(events[i].kind,"tx")) {
                if (writes<4) wire[writes]=events[i].value;
                writes++;
            }
        if (writes!=4 || completed!=4) return 6;
        printf("%s{\"before\":%u,\"after\":%u,\"state_cycles\":%u,\"wire\":[%u,%u,%u,%u]}",
               step?",":"",before,after,state_cycles,wire[0],wire[1],wire[2],wire[3]);
    }
    printf("],\"errors\":%u}\n",errors);
    return errors!=0;
}
