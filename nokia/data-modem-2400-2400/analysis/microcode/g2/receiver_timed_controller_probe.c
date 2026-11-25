/* Conditional 8251 external-sync receive schedule into the uninterrupted 8031 loop. */
#include "emu8051.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char code[65536], input[8];
static unsigned cycle, pc, errors, tx_due, bit_ticks, pulse_bit;
static unsigned ready, data, shift, count, synced, next_bit;
static unsigned completed, consumed, overruns, status_reads, frame_count;
static unsigned loops, dispatches, status_pc;
static unsigned char consumed_bytes[16], frame[4], last_complete_frame[4];
static unsigned char decoded_bytes[16];
static unsigned consumed_cycles[16], completed_cycles[16];

void sat_trace(struct em8051 *c) {
    pc=c->mPC;
    if(pc>=8192) errors++;
    if(pc==0x1ed3) loops++;
    if(pc==0x1ee8) dispatches++;
    if(pc==0x1dbd) status_pc++;
    if(pc==0x1000) c->mLowerData[0x15]=1;
}
static void exception(struct em8051 *c,int kind) { (void)c;(void)kind;errors++; }
static void sfr_write(struct em8051 *c,uint8_t address) {
    if(address==0x99) {
        frame[frame_count++%4]=c->mSFR[REG_SBUF];
        if(frame_count%4==0) memcpy(last_complete_frame,frame,4);
        tx_due=cycle+8;
    }
}
static unsigned char xread(struct em8051 *c,uint16_t address) {
    (void)c;
    if(pc==0x08e5) return 0;
    if(pc==0x0539 || pc==0x1d9d) return 1;
    if(pc==0x1dbd && address==5) { status_reads++; return ready?2:0; }
    if(pc==0x1dc6 && address==1 && ready) {
        ready=0;
        if(consumed<16) {consumed_bytes[consumed]=data;consumed_cycles[consumed]=cycle;}
        consumed++;
        return data;
    }
    fprintf(stderr,"unexpected read pc=%04X address=%04X cycle=%u\n",pc,address,cycle);
    errors++;return 0;
}
static void xwrite(struct em8051 *c,uint16_t address,uint8_t value) {
    (void)c;(void)value;
    if(address!=1 && address!=2 && address!=5 && address!=6) {
        fprintf(stderr,"unexpected write pc=%04X address=%04X\n",pc,address);errors++;
    }
}
static void rxc_edge(unsigned index) {
    unsigned bit=index<64?1:(input[(index-64)/8]>>((index-64)%8))&1;
    if(index==pulse_bit) {synced=1;count=shift=0;}
    if(!synced) return;
    shift|=bit<<count;
    if(++count==8) {
        if(ready) overruns++;
        else {data=shift;ready=1;}
        if(completed<16) completed_cycles[completed]=cycle;
        completed++;
        count=shift=0;
    }
}
int main(int argc,char **argv) {
    if(argc!=15) return 2;
    bit_ticks=strtoul(argv[2],0,0);
    pulse_bit=strtoul(argv[3],0,0);
    unsigned delay=strtoul(argv[4],0,0);
    unsigned long history=strtoul(argv[5],0,0);
    unsigned selector=strtoul(argv[6],0,0);
    if(!bit_ticks || bit_ticks>10000 || pulse_bit>128 ||
       (delay!=5 && delay!=18) || history>=(1UL<<23) ||
       (selector!=0x40 && selector!=0x60)) return 2;
    for(unsigned j=0;j<8;j++) {
        char *end=0;unsigned long value=strtoul(argv[7+j],&end,0);
        if(!end || *end || value>255) return 2;
        input[j]=value;
    }
    FILE *rom=fopen(argv[1],"rb");if(!rom) return 2;
    memset(code,255,sizeof code);
    if(fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    struct em8051 c={0};
    c.mCodeMem=code;c.mCodeMemMaxIdx=65535;
    c.except=exception;c.xread=xread;c.xwrite=xwrite;
    reset(&c,0);
    for(unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
    c.mSFR[REG_SP]=113;c.mSFR[REG_IE]=0;
    c.mLowerData[0x34]=0xAF;c.mLowerData[0x22]=0x10;
    c.mLowerData[0x24]=(delay==5)?2:0;
    c.mLowerData[0x42]=(history>>16)&255;
    c.mLowerData[0x43]=(history>>8)&255;
    c.mLowerData[0x44]=history&255;
    c.mPC=0x1ed3;
    unsigned char control_input[]={0,7,0,0,0,(unsigned char)selector,0};
    unsigned control_rx=0,last_pre=0;
    unsigned b0_cycle=0;
    for(cycle=0;cycle<(128+10)*bit_ticks && !errors;cycle++) {
        if(next_bit<128 && cycle==next_bit*bit_ticks) rxc_edge(next_bit++);
        unsigned pre=c.mPC;
        if(cycle && pre==0x1ed3 && last_pre!=0x1ed3) control_rx=0;
        tick(&c);
        if((c.mSFR[REG_SCON]&0x10) && !(c.mSFR[REG_SCON]&1) && control_rx<7 &&
           (pre==0x0807 || pre==0x0810 || pre==0x0826 || pre==0x083c ||
            pre==0x0852 || pre==0x0868 || pre==0x087e)) {
            c.mSFR[REG_SBUF]=control_input[control_rx++];c.mSFR[REG_SCON]|=1;
        }
        if(tx_due && cycle>=tx_due) {c.mSFR[REG_SCON]|=2;tx_due=0;}
        if(pre==0x1eeb && consumed && consumed<=16)
            decoded_bytes[consumed-1]=c.mLowerData[0x3a];
        if(c.mLowerData[0x34]==0xB0 && !b0_cycle) b0_cycle=cycle;
        last_pre=pre;
    }
    printf("{\"state\":%u,\"zero_octets\":%u,\"ram24\":%u,\"history\":%u,\"b0_cycle\":%u,\"final_pc\":%u,\"loops\":%u,\"dispatches\":%u,\"status_pc\":%u,\"completed\":%u,\"consumed\":%u,\"overruns\":%u,\"status_reads\":%u,\"errors\":%u,\"completed_cycles\":[",
           c.mLowerData[0x34],c.mLowerData[0x63],c.mLowerData[0x24],
           ((unsigned)c.mLowerData[0x42]<<16)|((unsigned)c.mLowerData[0x43]<<8)|c.mLowerData[0x44],
           b0_cycle,c.mPC,loops,dispatches,status_pc,completed,consumed,
           overruns,status_reads,errors);
    for(unsigned j=0;j<completed && j<16;j++) printf("%s%u",j?",":"",completed_cycles[j]);
    printf("],\"consumed_bytes\":[");
    for(unsigned j=0;j<consumed && j<16;j++) printf("%s%u",j?",":"",consumed_bytes[j]);
    printf("],\"consumed_cycles\":[");
    for(unsigned j=0;j<consumed && j<16;j++) printf("%s%u",j?",":"",consumed_cycles[j]);
    printf("],\"decoded_bytes\":[");
    for(unsigned j=0;j<consumed && j<16;j++) printf("%s%u",j?",":"",decoded_bytes[j]);
    printf("],\"completed_frames\":%u,\"last_completed_frame\":[",frame_count/4);
    for(unsigned j=0;j<4 && frame_count>=4;j++)
        printf("%s%u",j?",":"",last_complete_frame[j]);
    printf("]}\n");
    return errors?3:0;
}
