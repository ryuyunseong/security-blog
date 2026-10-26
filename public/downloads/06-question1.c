#include <stdio.h>

int main(void) {
    int value = 4;
    int before = value++;
    printf("%d %d\n", before, value);
    return 0;
}
