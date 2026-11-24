/* Receive seven synthetic USART bytes, then execute one A2 state step. */
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
    c.mLowerData[0x34]=0xa2;
    c.mLowerData[0x22]|=0x10; /* qualification */
    c.mLowerData[0x24]&=(unsigned char)~0x20; /* no timer reload */
    c.mLowerData[0x17]=0x80; c.mLowerData[0x16]=0;
    c.mLowerData[0x15]=0; c.mSFR[REG_IE]=0;
    c.mPC=0x1000;
    unsigned state_cycles=0;
    for (;state_cycles<200 && c.mPC!=0x1755;state_cycles++,cycle++) tick(&c);
    printf("{\"received\":%u,\"stored_2e\":%u,\"state\":%u,\"state_cycles\":%u,\"reached_stop\":%s,\"errors\":%u}\n",
        received,stored,c.mLowerData[0x34],state_cycles,c.mPC==0x1755?"true":"false",errors);
    return errors || c.mPC!=0x1755;
}
