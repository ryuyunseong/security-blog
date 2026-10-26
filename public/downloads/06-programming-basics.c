#include <stdio.h>

static int bump(int value) {
    return value + 1;
}

int main(void) {
    int denominator = 0;
    int number = 5;
    int total = 0;
    int values[] = {1, 2, 3};
    for (int i = 0; i < 3; ++i) {
        if (values[i] == 2) {
            continue;
        }
        total += values[i];
    }
    printf("division: %d %d\n", -7 / 3, -7 % 3);
    printf("guard: %d\n", denominator != 0 && 12 / denominator > 1);
    printf("value: %d %d\n", number, bump(number));
    printf("total: %d\n", total);
    return 0;
}
