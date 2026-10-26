#include <stdio.h>

int main(void) {
    int total = 0;
    int denominator = 0;
    for (int i = 0; i < 7; ++i) {
        if (i % 2 == 0) {
            continue;
        }
        total += i;
    }
    int safe = denominator != 0 && 10 / denominator > 1;
    printf("%d %d\n", total, safe);
    return 0;
}
