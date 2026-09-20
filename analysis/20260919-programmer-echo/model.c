/* Hypothesis model: readback sees the last data output routed onto the
   parallel bus, instead of a ROM. No hardware I/O. Uses the real core. */
#include <stdio.h>
#include <string.h>
#include "willem.h"
struct model { unsigned data, control, held, bit; };
static void data_write(void *ctx, int value) {
    struct model *m = ctx;
    m->data = (unsigned)value;
    if (!(m->control & WL_CTL_MUX)) m->held = m->data;
}
static void control_write(void *ctx, int raw) {
    struct model *m = ctx;
    m->control = (unsigned)raw ^ WL_CTL_XOR;
    if (!(m->control & WL_CTL_MUX)) m->held = m->data;
}
static wl_u8 status_read(void *ctx) {
    struct model *m = ctx;
    wl_u8 result = (m->held & m->bit) ? 0 : WL_ST_ACK;
    m->bit >>= 1;
    return result;
}
int main(int argc, char **argv) {
    struct model m;
    struct wl_io io;
    struct willem wl;
    unsigned address, size;
    if (argc != 2) return 2;
    memset(&m, 0, sizeof(m));
    memset(&io, 0, sizeof(io));
    io.ctx = &m;
    io.data_write = data_write;
    io.control_write = control_write;
    io.status_read = status_read;
    wl_init(&wl, &io);
    if (!strcmp(argv[1], "rf5")) { size = 2048; wl_begin_2716_read(&wl); }
    else if (!strcmp(argv[1], "27256")) { size = 32768; wl_begin_2764_read(&wl); }
    else if (!strcmp(argv[1], "28c64")) { size = 8192; wl_begin_28c64_read(&wl); }
    else return 2;
    for (address = 0; address < size; address++) {
        m.bit = 0x80;
        putchar(wl_read_byte(&wl, address));
    }
    wl_end_read(&wl);
    return ferror(stdout) ? 1 : 0;
}
