/* Preserve one 8031 RAM image across A0/A1/A2 state steps and frame sends. */
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
    errors=event_count=0; cycle=0;
    c.mSFR[REG_SP]=113; c.mSFR[REG_IE]=0;
    c.mLowerData[0x34]=0xa0;
    c.mLowerData[0x22]=0x10;
    c.mLowerData[0x2e]=(unsigned char)selector;
    printf("{\"selector\":%u,\"rows\":[",selector);
    for (unsigned step=0;step<4;step++) {
        unsigned before=c.mLowerData[0x34];
        c.mLowerData[0x24]&=(unsigned char)~0x20;
        c.mLowerData[0x17]=0x80; c.mLowerData[0x16]=0;
        c.mLowerData[0x15]=0;
        c.mPC=0x1000;
        unsigned state_cycles=0;
        for (;state_cycles<200 && c.mPC!=0x1755;state_cycles++,cycle++) tick(&c);
        if (c.mPC!=0x1755 || errors) return 3;
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
        if (c.mPC!=0x1ee8 || errors) return 4;
        unsigned wire[4]={0},writes=0;
        for (unsigned i=first_event;i<event_count;i++)
            if (!strcmp(events[i].kind,"tx")) {
                if (writes<4) wire[writes]=events[i].value;
                writes++;
            }
        if (writes!=4 || completed!=4) return 5;
        printf("%s{\"before\":%u,\"after\":%u,\"state_cycles\":%u,\"wire\":[%u,%u,%u,%u],\"p1\":%u}",
            step?",":"",before,after,state_cycles,wire[0],wire[1],wire[2],wire[3],c.mSFR[REG_P1]);
    }
    printf("],\"errors\":%u}\n",errors);
    return errors!=0;
}
