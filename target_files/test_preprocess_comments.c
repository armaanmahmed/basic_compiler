int main() {
    /* multiline // with single-line comment sign in middle */
    int v = 3;
    // commented out line

    int x = 2; // partially commented out line

    char c = /* some comment here */ 'c'; /* another in the same line!*/
    /**
      and of course
      we have our standard multiline comment
     */
    v += x;
    return 0;
}