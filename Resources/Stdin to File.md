---
domain: cpp
tags: [stl]
date: 2026-11-11
para: Resources
project: null
---
> Exercise `stdin_to_file`, converted from `dump/stdin_to_file.pdf`. The PDF stays the reference.

## File tree

```text
stdin_to_file/
    stdin_to_file.cc     (to submit)
    stdin_to_file.hh
    stdin_to_file_example.cc
```

## Constraints

**Compilation:** Your code must compile with the following flags

- `-Wall -Wextra -Werror -pedantic -std=c++20 -Wold-style-cast`

**Main function:** None

**Authorized headers:** You are only allowed to use the functions defined in the following headers:

- `iostream`
- `fstream`
- `string`
- `stdin_to_file.hh`

## 1. Goal

Write a function with the following prototype:

```cpp
long int stdin_to_file(const std::string& filename);
```

This function should read the content written to standard input and write it to a file, one token per line. The name of the file is defined by the parameter filename. The function should also return the number of tokens written into that file.

```console
42sh$ g++ -Wall -Wextra -Werror -std=c++20 -pedantic -Wold-style-cast stdin_to_file_example.cc stdin_to_file.cc
42sh$ cat -e test.in
This is a test.$
42sh$ ./a.out < test.in
File has 4 words
42sh$ cat -e file.out
This$
is$
a$
test.$
```

## Links

- [[C++ Syntax]]
