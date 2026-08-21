# basic_compiler

[![ci](https://github.com/armaanmahmed/basic_compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/armaanmahmed/basic_compiler/actions/workflows/ci.yml)

A C compiler built from first principles in Python.

## Status

The preprocessor works, which encompasses removing comments and expanding
object and function macros.

Next steps: lexer → parser (AST) → code generation.
Potentially, a visualizer may be added as well.

## Usage

```sh
python preprocessor.py target_files/test_preprocess_basic.c
```

For instance, given:

```c
#define WIDTH 10
#define HEIGHT 20
#define AREA (WIDTH * HEIGHT)

int main() {
    // area of the rectangle
    int area = AREA;
    return 0;
}
```

it emits:

```c
int main() {
    int area = (10 * 20);
    return 0;
}
```
