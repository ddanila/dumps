/* Local interface probes against unchanged controller ROM and vendored core.
 * Completion events are synthetic; no serial waveform or DSP connection. */
#include "emu8051.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char code[65536];
static unsigned cycle, pc, delay, tx_due, errors, event_count;
static unsigned port_probe, port_value, decoding_probe, programming;
static unsigned char decode_seen[8192];
struct event { unsigned cycle, pc, value; const char *kind; };
static struct event events[128];
static void event(const char *kind, unsigned at, unsigned value) {
    if (event_count >= 128) { fprintf(stderr,"event overflow\n"); exit(3); }
    events[event_count++] = (struct event){cycle, at, value, kind};
}
void sat_trace(struct em8051 *c) {
    pc = c->mPC;
    if (decoding_probe && pc<8192) decode_seen[pc]=1;
    if (pc >= 8192) { fprintf(stderr,"out-of-ROM execution\n"); exit(3); }
}
static void exception(struct em8051 *c, int kind) { (void)c; errors++; event("exception",pc,kind); }
static void sfr_write(struct em8051 *c, uint8_t address) {
    if (address == 0x99) { event("tx",pc,c->mSFR[REG_SBUF]); tx_due = cycle+delay; }
    if (address == 0x90) event("p1",pc,c->mSFR[REG_P1]);
    if (address == 0x98) event("scon",pc,c->mSFR[REG_SCON]);
    if (port_probe && address == 0xa0) event("p2",pc,c->mSFR[REG_P2]);
}
static unsigned char xread(struct em8051 *c, uint16_t address) {
    if (port_probe && pc==0x8e5) {
        address |= (unsigned)c->mSFR[REG_P2]<<8;
        event("read_address",pc,address); event("read_value",pc,port_value);
        return port_value;
    }
    errors++; event("unexpected_read",pc,address); return 0;
}
static void xwrite(struct em8051 *c, uint16_t address, uint8_t value) {
    if (programming) {
        event("write_address",pc,address | ((unsigned)c->mSFR[REG_P2]<<8));
        event("write_value",pc,value); return;
    }
    (void)c; (void)value; errors++; event("unexpected_write",pc,address);
}
static int bytes(const char *text, unsigned char *out, unsigned length) {
    if (strlen(text) != length*2) return 0;
    for (unsigned i=0;i<length;i++) {
        char s[3]={text[2*i],text[2*i+1],0}, *end;
        unsigned long value=strtoul(s,&end,16);
        if (*end) return 0;
        out[i]=(unsigned char)value;
    }
    return 1;
}
int main(int argc, char **argv) {
    if (argc != 7) return 2;
    unsigned initial_p1=strtoul(argv[2],0,0), initial_changed=strtoul(argv[3],0,0);
    unsigned limit=strtoul(argv[4],0,0), sentinel=strtoul(argv[5],0,0), initial_sp=strtoul(argv[6],0,0);
    if (initial_p1>255 || initial_changed>1 || !limit || sentinel<8192 || sentinel>65535 || initial_sp<2 || initial_sp>=128) return 2;
    FILE *rom=fopen(argv[1],"rb"); if (!rom) return 2;
    memset(code,255,sizeof code);
    if (fread(code,1,8192,rom)!=8192 || fgetc(rom)!=EOF) return 2;
    fclose(rom);
    char line[256], mode[8], frame_text[40], prior_text[32];
    unsigned completions;
    while (fgets(line,sizeof line,stdin)) {
        if (sscanf(line,"%7s %39s %31s %u %u",mode,frame_text,prior_text,&delay,&completions)!=5 || !delay || delay>1000) return 2;
        programming=!strcmp(mode,"program");
        int reading=!strcmp(mode,"read");
        int decoding=!strcmp(mode,"decode");
        int edge=!strcmp(mode,"edge"), qualify=!strcmp(mode,"qualify");
        int event_probe=edge || qualify;
        int output01=!strcmp(mode,"out01"), output32=!strcmp(mode,"out32");
        int build=!strcmp(mode,"build");
        int output_probe=build || output01 || output32 || !strcmp(mode,"out33");
        decoding_probe=programming || decoding || event_probe || output_probe; memset(decode_seen,0,sizeof decode_seen);
        unsigned stop=sentinel, entry=edge?0x13:qualify?0x1790:decoding?0x620:reading?0x800:0x899;
        if (programming) entry=0x1d05;
        if (output_probe) { entry=output01?0x266:output32?0x12f:0x6e; stop=build?0x46c:output01?0x433:output32?0x266:0x12f; }
        port_probe=!strcmp(mode,"port") || !strcmp(mode,"poll1") || !strcmp(mode,"poll2") || !strcmp(mode,"main");
        if (!reading && strcmp(mode,"write") && !port_probe && !decoding && !event_probe && !output_probe && !programming) return 2;
        if (port_probe) {
            entry=0x8dd;
            if (!strcmp(mode,"poll1")) { entry=0x1e37; stop=0x1e3c; }
            if (!strcmp(mode,"poll2")) { entry=0x1e72; stop=0x1e77; }
            if (!strcmp(mode,"main")) { entry=0x1ed3; stop=0x81d; reading=1; }
        }
        unsigned char frame[16]={0}, prior[6]={0};
        if (!bytes(frame_text,frame,build?16:port_probe?9:output32?7:output01?9:event_probe?9:(reading || decoding)?7:4) || !bytes(prior_text,prior,6)) return 2;
        struct em8051 c={0};
        c.mCodeMem=code; c.mCodeMemMaxIdx=65535;
        c.except=exception; c.xread=xread; c.xwrite=xwrite;
        reset(&c,0);
        for (unsigned i=0;i<128;i++) c.sfrwrite[i]=sfr_write;
        /* Explicit local caller: RET reaches a sentinel before another tick. */
        c.mLowerData[initial_sp-1]=sentinel&255; c.mLowerData[initial_sp]=sentinel>>8; c.mSFR[REG_SP]=initial_sp;
        c.mPC=entry;
        c.mSFR[REG_P1]=initial_p1;
        if (!event_probe && !output_probe && !programming) memcpy(c.mLowerData+0x2a,prior,6);
        if (!reading && !port_probe && !decoding && !event_probe && !output_probe && !programming) memcpy(c.mLowerData+0x30,frame,4);
        if (port_probe) {
            port_value=frame[0]; c.mSFR[REG_P2]=frame[1]; c.mLowerData[0x17]=prior[0];
            memmove(frame,frame+2,7);
        }
        if (programming) {
            c.mLowerData[0]=frame[0]; c.mLowerData[3]=frame[1]; c.mLowerData[2]=frame[2];
            c.mSFR[REG_P2]=frame[3];
        } else if (output_probe) {
            c.mLowerData[0x34]=frame[0];
            if (build) {
                memcpy(c.mLowerData+0x30,frame+1,4);
                memcpy(c.mLowerData+0x2a,frame+5,6);
                c.mLowerData[0x49]=frame[11]; c.mLowerData[0x4a]=frame[12];
                c.mLowerData[0x65]=frame[13];
                c.mLowerData[0x3d]=frame[14]; c.mLowerData[0x3e]=frame[15];
            } else if (output32) {
                c.mLowerData[3]=frame[0]; c.mLowerData[2]=frame[6];
                c.mLowerData[0x32]=frame[1]; c.mLowerData[0x49]=frame[2];
                c.mLowerData[0x4a]=frame[3]; c.mLowerData[0x65]=frame[4];
                c.mLowerData[0x2c]=frame[5];
            } else if (output01) {
                c.mLowerData[3]=frame[0];
                c.mLowerData[0x30]=frame[1]; c.mLowerData[0x31]=frame[2];
                memcpy(c.mLowerData+0x2a,frame+3,6);
            } else {
                c.mLowerData[0x33]=frame[1];
                c.mLowerData[0x30]=frame[2]; c.mLowerData[0x2d]=frame[3];
            }
            memcpy(c.mLowerData+0x22,prior,6);
        } else if (event_probe) {
            c.mLowerData[0x12]=frame[0]; c.mLowerData[0x13]=frame[1];
            c.mLowerData[0x6e]=frame[2]; c.mLowerData[0x34]=frame[3];
            c.mLowerData[0x30]=frame[4]; c.mLowerData[0x31]=frame[5];
            c.mSFR[REG_PSW]=frame[6]; c.mSFR[REG_ACC]=frame[7];
            if (frame[8]&0x80) return 2; /* Local probes keep global interrupts disabled. */
            c.mSFR[REG_IE]=frame[8];
            memcpy(c.mLowerData+0x22,prior,6);
        } else if (decoding) {
            /* Six normalized inputs plus byte 6E; prior holds RAM 22-27. */
            memcpy(c.mLowerData+0x2a,frame,6);
            memcpy(c.mLowerData+0x22,prior,6);
            c.mLowerData[0x6e]=frame[6];
        } else c.mLowerData[0x22]=initial_changed;
        tx_due=errors=event_count=0;
        unsigned rx_due=0, received=0, completed=0;
        for (cycle=0;cycle<limit && c.mPC!=stop;cycle++) {
            tick(&c);
            if (reading && (c.mSFR[REG_SCON]&0x11)==0x10 && received<7 && received<completions) {
                if (!rx_due) rx_due=cycle+delay;
                if (cycle>=rx_due) {
                    c.mSFR[REG_SBUF]=frame[received++]; c.mSFR[REG_SCON]|=1;
                    event("rx",c.mPC,c.mSFR[REG_SBUF]); rx_due=0;
                }
            }
            if (!reading && tx_due && cycle>=tx_due && completed<completions) {
                c.mSFR[REG_SCON]|=2; tx_due=0; completed++;
                event("tx_complete",c.mPC,completed);
            }
        }
        printf("{\"returned\":%s,\"cycles\":%u,\"pc\":%u,\"sp\":%u,\"errors\":%u,\"changed\":%u,\"p1\":%u,\"scon\":%u,\"ram\":[",
            c.mPC==sentinel?"true":"false",cycle,c.mPC,c.mSFR[REG_SP],errors,c.mLowerData[0x22]&1,c.mSFR[REG_P1],c.mSFR[REG_SCON]);
        for (unsigned i=0;i<6;i++) printf("%s%u",i?",":"",c.mLowerData[0x2a+i]);
        printf("],\"events\":[");
        for (unsigned i=0;i<event_count;i++) printf("%s{\"cycle\":%u,\"pc\":%u,\"kind\":\"%s\",\"value\":%u}",i?",":"",events[i].cycle,events[i].pc,events[i].kind,events[i].value);
        printf("]");
        if (programming || port_probe || decoding || event_probe || output_probe) {
            printf(",\"reached_stop\":%s,\"acc\":%u,\"p2\":%u,\"iram\":[",c.mPC==stop?"true":"false",c.mSFR[REG_ACC],c.mSFR[REG_P2]);
            for (unsigned i=0;i<128;i++) printf("%s%u",i?",":"",c.mLowerData[i]);
            printf("],\"sfr\":[");
            for (unsigned i=0;i<128;i++) printf("%s%u",i?",":"",c.mSFR[i]);
            printf("]");
        }
        if (programming || decoding || event_probe || output_probe) {
            unsigned count=0; printf(",\"visited\":[");
            for (unsigned i=0;i<8192;i++) if (decode_seen[i]) printf("%s%u",count++?",":"",i);
            printf("]");
        }
        puts("}");
    }
    return 0;
}
