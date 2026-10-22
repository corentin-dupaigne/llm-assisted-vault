---
domain: cpp
tags: [stl, lambdas, operator-overloading]
date: 2026-10-22
para: Resources
project: null
---
## Program structure

```cpp
#include <iostream>   // header include (preprocessor)
#include <string>

int main() {
    std::cout << "Hello, world!" << std::endl;
    return 0;         // 0 = success
}
```

- Every statement ends with `;`
- Blocks use `{ }`
- `std::` = standard library namespace (`using namespace std;` exists but avoid it in headers)
- Comments: `// line` and `/* block */`

**Compile & run**

```bash
g++ -std=c++20 -Wall -Wextra -o main main.cpp && ./main
```

______________________________________________________________________

## Variables & types

```cpp
int     a = 42;
double  pi = 3.14;
float   f = 1.5f;
char    c = 'x';
bool    ok = true;
std::string s = "text";

auto x = 10;          // type inferred (int)
const int MAX = 100;  // immutable
constexpr int SIZE = 16; // evaluated at compile time
```

| Type | Typical size | Notes |
|---|---|---|
| `char` | 1 byte | |
| `short` | 2 bytes | |
| `int` | 4 bytes | |
| `long long` | 8 bytes | |
| `float` / `double` | 4 / 8 bytes | |
| `size_t` | 8 bytes (64-bit) | unsigned, used for sizes/indices |
| `int32_t`, `uint64_t`… | exact | from `<cstdint>` |

**Initialization styles**

```cpp
int a = 5;    // copy init
int b(5);     // direct init
int c{5};     // brace (uniform) init — prevents narrowing
int d{};      // zero-initialized
```

> [!tip] Prefer `{}` initialization: `int x{3.7};` is a compile error instead of a silent truncation.

______________________________________________________________________

## Operators

- Arithmetic: `+ - * / %`
- Comparison: `== != < > <= >=` (C++20: `<=>` "spaceship")
- Logical: `&& || !`
- Bitwise: `& | ^ ~ << >>`
- Increment: `++i` (pre), `i++` (post)
- Ternary: `cond ? a : b`
- Scope: `::` · Member: `.` · Pointer member: `->`

______________________________________________________________________

## Control flow

```cpp
if (x > 0) {
    // ...
} else if (x == 0) {
    // ...
} else {
    // ...
}

// if with initializer (C++17)
if (auto it = m.find(k); it != m.end()) { /* use it */ }

switch (n) {
    case 1:  /* ... */ break;
    case 2:
    case 3:  /* ... */ break;
    default: /* ... */
}

for (int i = 0; i < 10; ++i) { }
for (const auto& item : vec) { }   // range-based for
while (cond) { }
do { } while (cond);
```

`break` exits the loop, `continue` skips to the next iteration.

______________________________________________________________________

## Functions

```cpp
int add(int a, int b) {
    return a + b;
}

void greet(const std::string& name = "you"); // default arg (declaration)

auto mul(int a, int b) -> int { return a * b; } // trailing return type
```

**Parameter passing**
| Syntax | Meaning | Use when |
|---|---|---|
| `T x` | by value (copy) | small/cheap types (`int`, `double`) |
| `T& x` | by reference | function must modify the argument |
| `const T& x` | const reference | large read-only objects (`std::string`, `std::vector`) |
| `T* x` | pointer | optional / nullable argument |
| `T&& x` | rvalue reference | move semantics |

**Overloading** — same name, different parameters:

```cpp
int  area(int side);
int  area(int w, int h);
```

**Declaration vs definition** — declare in `.h`, define in `.cpp`:

```cpp
// math.h
#pragma once
int add(int a, int b);
```

______________________________________________________________________

## Pointers & references

```cpp
int  x = 10;
int* p = &x;   // p holds the address of x
*p = 20;       // dereference → x is now 20

int& r = x;    // r is an alias for x (must be initialized, can't be reseated)
r = 30;        // x is now 30

int* n = nullptr; // null pointer (never use NULL or 0)
```

- `&` in a declaration → reference; `&` in an expression → address-of
- `*` in a declaration → pointer; `*` in an expression → dereference

### Pass by pointer vs by reference

Both let a function modify the caller's variable without copying it.

```cpp
// By pointer: caller passes the address with &
void incPtr(int* p) {
    if (p) (*p)++;    // must check for null, must dereference
}

// By reference: caller passes the variable directly
void incRef(int& r) {
    r++;              // used like a normal variable
}

int a = 5;
incPtr(&a);   // a == 6 — & at the call site = address-of
incRef(a);    // a == 7 — no & at the call site
incPtr(nullptr); // allowed (does nothing here)
// incRef(nullptr); // compile error: a reference can't be null
```

| | Pointer `T*` | Reference `T&` |
| ---------------------------------------- | ----------------- | ----------------------------- |
| Call syntax | `f(&a)` | `f(a)` |
| Access inside | `*p`, `p->member` | `r`, `r.member` |
| Can be null | Yes (`nullptr`) | No |
| Can be reseated (point elsewhere) | Yes (`p = &b;`) | No, bound once at init |
| Must be initialized | No | Yes |
| Pointer arithmetic | Yes (`p + 1`) | No |
| Visible at call site that arg may change | Yes (`&a`) | No (looks like pass-by-value) |

**When to use which**

- `const T&` → large read-only input (default for strings, vectors, objects)
- `T&` → required argument the function modifies
- `T*` → optional argument (can be `nullptr`), C APIs (`scanf("%d", &a)`), or when you need pointer arithmetic or reseating

> [!note] A reference is usually implemented as a pointer under the hood, but at the language level it behaves as an alias: once bound, any operation on it acts on the original variable.

**Smart pointers** (`<memory>`) — prefer over raw `new`/`delete`:

```cpp
auto u = std::make_unique<Foo>(args);   // single owner
auto s = std::make_shared<Foo>(args);   // shared ownership (ref counted)
std::weak_ptr<Foo> w = s;               // non-owning observer of a shared_ptr
```

______________________________________________________________________

## Arrays & containers

```cpp
int arr[5] = {1, 2, 3, 4, 5};         // C array (fixed, no bounds check)
std::array<int, 5> a = {1, 2, 3, 4, 5}; // fixed size, safer

std::vector<int> v = {1, 2, 3};       // dynamic array
v.push_back(4);
v.size();
v[0];       // no bounds check
v.at(0);    // bounds-checked (throws)

std::map<std::string, int> m;         // ordered (red-black tree)
m["a"] = 1;
std::unordered_map<std::string, int> um; // hash map

std::set<int> st;
std::pair<int, std::string> pr{1, "x"};
auto [id, name] = pr;                 // structured binding (C++17)
```

______________________________________________________________________

## Classes & structs

```cpp
class Dog {
public:
    Dog(std::string name, int age)          // constructor
        : name_(std::move(name)), age_(age) {} // member initializer list

    ~Dog() = default;                      // destructor

    void bark() const;                     // const method: doesn't modify object
    int  age() const { return age_; }

    static int count;                      // shared by all instances

private:
    std::string name_;
    int age_;
};

void Dog::bark() const {                   // out-of-class definition
    std::cout << name_ << " says woof\n";
}

Dog d("Rex", 3);
d.bark();
```

- `struct` = `class` with members **public** by default
- Access: `public`, `protected`, `private`
- `this` is a pointer to the current object

**Inheritance & polymorphism**

```cpp
class Animal {
public:
    virtual ~Animal() = default;      // always virtual dtor in a base class
    virtual void speak() const = 0;   // pure virtual → abstract class
};

class Cat : public Animal {
public:
    void speak() const override { std::cout << "meow\n"; }
};

std::unique_ptr<Animal> a = std::make_unique<Cat>();
a->speak();   // dynamic dispatch → "meow"
```

**Rule of 5** — if you define one of these, think about all of them:
destructor, copy constructor, copy assignment, move constructor, move assignment.
Prefer the **Rule of 0**: use RAII members (`std::string`, `std::vector`, smart pointers) and define none.

______________________________________________________________________

## Templates

```cpp
template <typename T>
T maxOf(T a, T b) {
    return (a > b) ? a : b;
}
maxOf(3, 7);         // T deduced as int
maxOf<double>(3, 7.5);

template <typename T>
class Box {
    T value;
public:
    explicit Box(T v) : value(v) {}
    T get() const { return value; }
};

// C++20 concepts: constrain T
template <std::integral T>
T square(T x) { return x * x; }
```

______________________________________________________________________

## Lambdas

```cpp
auto add = [](int a, int b) { return a + b; };

int factor = 3;
auto mul  = [factor](int x) { return x * factor; }; // capture by value
auto inc  = [&factor]() { ++factor; };              // capture by reference
auto all  = [=]() { /* everything by value */ };
auto allr = [&]() { /* everything by reference */ };

std::sort(v.begin(), v.end(), [](int a, int b) { return a > b; });
```

Syntax: `[capture](params) -> return_type { body }`

______________________________________________________________________

## Namespaces

```cpp
namespace net::http {       // nested namespace (C++17)
    void get();
}
net::http::get();

using std::string;          // import a single name
namespace fs = std::filesystem; // alias
```

______________________________________________________________________

## Error handling

```cpp
try {
    if (bad) throw std::runtime_error("something failed");
} catch (const std::runtime_error& e) {
    std::cerr << e.what() << '\n';
} catch (...) {
    // catch-all
}

void f() noexcept; // promises not to throw
```

Alternatives: `std::optional<T>` (value or nothing), `std::expected<T, E>` (C++23, value or error).

______________________________________________________________________

## Casting

```cpp
static_cast<double>(i);        // normal, checked at compile time
dynamic_cast<Cat*>(animalPtr); // safe downcast (nullptr on failure), needs virtual
const_cast<int*>(cp);          // remove const (rarely legit)
reinterpret_cast<char*>(p);    // raw bit reinterpretation (dangerous)
```

> [!warning] Avoid C-style casts `(int)x` — they silently pick any of the above.

______________________________________________________________________

## Move semantics

```cpp
std::vector<int> a = {1, 2, 3};
std::vector<int> b = std::move(a); // steals a's buffer, a is now valid but unspecified
```

- **lvalue**: has a name/address (`x`)
- **rvalue**: temporary (`x + 1`, `std::move(x)`)
- `std::move` doesn't move anything — it just casts to an rvalue so the move constructor gets picked

______________________________________________________________________

## Preprocessor

```cpp
#include <vector>      // system header
#include "mine.h"      // local header
#define DEBUG 1        // macro (prefer constexpr)
#ifdef DEBUG
  // ...
#endif
#pragma once           // include guard
```

______________________________________________________________________

## Common gotchas

- Uninitialized local variables hold garbage → always initialize
- `=` vs `==` in conditions
- Integer division: `5 / 2 == 2` → use `5 / 2.0`
- Signed/unsigned comparison: `v.size()` is unsigned, `for (int i = 0; i < v.size(); ...)` warns
- Dangling references: returning a reference/pointer to a local variable
- Forgetting `virtual` destructor in a polymorphic base class → leaks
- Missing `break` in a `switch` → fallthrough
- Iterator invalidation: modifying a `vector` while iterating over it

## Links

- [[C++ Functors]]
