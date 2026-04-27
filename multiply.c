#include <stdio.h>
#include <stdlib.h>

int multiply(int x, int y){
    return x * y;
}

int main(void){
    for (int i = 1; i <= 10000000; i++) {
        int x = rand() % 10000 + 10000000;
        //printf("x = %d\n", x);
        int y = rand() % 10000 + 10000000;
        //printf("y = %d\n", y);
        int result = multiply(x, y);
    }
    return 0;
}

