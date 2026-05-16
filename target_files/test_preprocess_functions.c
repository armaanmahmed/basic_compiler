// relatively simple arithmetic examples but could expand
#define DOUBLE(x) x * 2
#define ADD(x, y) (x + y)
#define SQUARE(x) ((x) * (x))

int main() {
    int a = DOUBLE(5);
    int b = ADD(3, 4);
    int c = SQUARE(3);
    // multiple substitutions in one line
    int d = SQUARE(ADD(4, 5));

    // multiple of the same substitution in one line
    int manyDoubled = DOUBLE(DOUBLE(b));
    return 0;
}