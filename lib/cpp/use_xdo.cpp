// #ifndef CPP_ROXDO_H
// #define CPP_ROXDO_H

// void k(const char *key_sequence);

// #endif //CPP_ROXDO_H

extern "C" {
#include "xdo.h"
}
#include <cstdio>
#include <cstdlib>

void k(const char *key_sequence) {
    xdo_t *xdo = xdo_new(NULL);
    xdo_send_keysequence_window(xdo, CURRENTWINDOW, key_sequence, 0.012);
}


int main(int argc, char **argv) {
    k("a");
    return (0);
};