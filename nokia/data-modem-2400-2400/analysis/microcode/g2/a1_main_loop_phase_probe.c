/* Observe output32 entry/exit during the existing uninterrupted main-loop fixture. */
#define main main_loop_original_main
#define sat_trace main_loop_original_trace
#include "main_loop_probe.c"
#undef main
#undef sat_trace

struct phase_row {
    unsigned state, prior32, prior49, prior4a, prior65;
    unsigned flag22, flag23, flag24, input2c;
    unsigned out32, out49, out4a, out65;
};
static struct phase_row phases[32];
static unsigned phase_count, pending;

void sat_trace(struct em8051 *c) {
    main_loop_original_trace(c);
    if (c->mPC==0x12f) {
        if (phase_count>=32 || pending) { errors++; return; }
        struct phase_row *r=&phases[phase_count];
        r->state=c->mLowerData[0x34];
        r->prior32=c->mLowerData[0x32];
        r->prior49=c->mLowerData[0x49];
        r->prior4a=c->mLowerData[0x4a];
        r->prior65=c->mLowerData[0x65];
        r->flag22=c->mLowerData[0x22];
        r->flag23=c->mLowerData[0x23];
        r->flag24=c->mLowerData[0x24];
        r->input2c=c->mLowerData[0x2c];
        pending=1;
    } else if (c->mPC==0x266 && pending) {
        struct phase_row *r=&phases[phase_count];
        r->out32=c->mLowerData[0x32];
        r->out49=c->mLowerData[0x49];
        r->out4a=c->mLowerData[0x4a];
        r->out65=c->mLowerData[0x65];
        phase_count++;
        pending=0;
    }
}

int main(int argc, char **argv) {
    int result=main_loop_original_main(argc,argv);
    if (pending || phase_count<12) return 6;
    fprintf(stderr,"{\"phases\":[");
    for (unsigned i=0;i<phase_count;i++) {
        struct phase_row *r=&phases[i];
        fprintf(stderr,"%s{\"state\":%u,\"prior32\":%u,\"prior49\":%u,\"prior4a\":%u,\"prior65\":%u,\"flag22\":%u,\"flag23\":%u,\"flag24\":%u,\"input2c\":%u,\"out32\":%u,\"out49\":%u,\"out4a\":%u,\"out65\":%u}",
                i?",":"",r->state,r->prior32,r->prior49,r->prior4a,
                r->prior65,r->flag22,r->flag23,r->flag24,r->input2c,
                r->out32,r->out49,r->out4a,r->out65);
    }
    fprintf(stderr,"]}\n");
    return result;
}
