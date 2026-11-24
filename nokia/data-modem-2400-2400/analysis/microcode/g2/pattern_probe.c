/* Execute controller ROM routine 1C07 for every candidate received octet. */
#define main interface_probe_original_main
#include "../../interface_probe.c"
#undef main

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    unsigned state=strtoul(argv[2],0,0), value=strtoul(argv[3],0,0);
    if (state>255 || value>255) return 2;
    FILE *rom=fopen(argv[1],"rb"); if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
    c.except=exception; c.xread=xread; c.xwrite=xwrite;
    reset(&c,0);
    for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    errors=event_count=cycle=0;
    c.mSFR[REG_SP]=113;
    c.mLowerData[112]=0x00; c.mLowerData[113]=0x1f;
    c.mLowerData[0x34]=(unsigned char)state;
    c.mLowerData[0x3a]=(unsigned char)value;
    c.mLowerData[0x21]=0x10; /* 01h.4: new octet available */
    c.mPC=0x1c07;
    for (;cycle<200 && c.mPC!=0x1f00;cycle++) tick(&c);
    printf("{\"state\":%u,\"octet\":%u,\"returned\":%s,\"cycles\":%u,\"flags24\":%u,\"counter63\":%u,\"prior66\":%u,\"pending21\":%u,\"errors\":%u}\n",
        state,value,c.mPC==0x1f00?"true":"false",cycle,c.mLowerData[0x24],
        c.mLowerData[0x63],c.mLowerData[0x66],c.mLowerData[0x21],errors);
    return errors || c.mPC!=0x1f00;
}
