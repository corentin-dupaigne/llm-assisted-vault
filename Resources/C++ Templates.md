---
domain: cpp
tags: [stl]
date: 2026-11-11
para: Resources
project: null
---
> [!goal] Objective
> Turn a class that works for **one** type (`IntStack`) into a class that works for **any** type (`GenericStack<T>`), split across a `.hh` and a `.hxx`, and still correct for move-only types like `std::unique_ptr<int>`.

______________________________________________________________________

## 1. Why templates?

Without templates you'd write `IntStack`, `StringStack`, `DoubleStack`… with identical code. A template is a **recipe**: you write the class once with a placeholder type `T`, and the compiler **generates** a real class for each type you use.

```cpp
GenericStack<int>         // the compiler writes a version where T = int
GenericStack<std::string> // and another one where T = std::string
```

Each generated version is called an **instantiation**. It happens at compile time, so there's no runtime cost.

______________________________________________________________________

## 2. Template syntax

### A template function

```cpp
template <typename T>
T max_of(T a, T b)
{
    return a > b ? a : b;
}

max_of(3, 7);        // T deduced = int
max_of<double>(3, 7) // T forced  = double
```

`template <typename T>` goes **right before** the thing it applies to. `typename` and `class` mean exactly the same thing here.

### A template class

```cpp
template <typename T>
class Box
{
public:
    Box(T value);
    const T& get() const;

private:
    T value_;
};

Box<int> b{ 42 };   // you MUST write <int> for the class... (or let C++17 deduce it)
```

Inside the class, `T` is used like any normal type: attribute types, parameters, return types.

______________________________________________________________________

## 3. The file layout: `.hh` + `.hxx`

> [!warning] Key rule
> **Template code must be visible wherever it's used.** The compiler can only generate `GenericStack<std::string>` if it sees the **full method bodies** at that point, not just the declarations.

That's why you **can't** put template method bodies in a `.cc` compiled separately: the `.cc` would never know which `T` to generate, and you'd get `undefined reference` at link time.

The EPITA convention:

- **`.hh`** — the class declaration
- **`.hxx`** — the method definitions
- the `.hh` **includes the `.hxx` at the very end**

```cpp
// box.hh
#pragma once

template <typename T>
class Box
{
public:
    Box(T value);
    const T& get() const;

private:
    T value_;
};

#include "box.hxx"   // ← last line of the header
```

```cpp
// box.hxx
#pragma once
#include "box.hh"

template <typename T>
Box<T>::Box(T value)
    : value_(std::move(value))
{}

template <typename T>
const T& Box<T>::get() const
{
    return value_;
}
```

The user only does `#include "box.hh"`, and gets everything. There's **no `.cc`** for a template class, which is why `main_generic.cc` compiles alone, without your stack in the command.

______________________________________________________________________

## 4. Defining methods outside the class

Each definition in the `.hxx` needs **two things** compared to a normal class:

```cpp
template <typename T>          // 1. repeat the template line
void Box<T>::set(T value)      // 2. the class name is Box<T>, not Box
{
    value_ = std::move(value);
}
```

> [!tip] Pattern to memorize
> `template <typename T>` + `ReturnType ClassName<T>::method(params) const`

Forgetting `<T>` after the class name is the most common compile error.

______________________________________________________________________

## 5. The `typename` trap: nested types

This is **the** trap for `GenericStack<T>::GenericNode`.

Say `Tree<T>` has a nested struct `Leaf`, and a method returns a pointer to it:

```cpp
template <typename T>
class Tree
{
public:
    struct Leaf
    {
        T data;
    };

    Leaf* first() const;
};
```

Inside the class, `Leaf` is enough. But **outside**, in the `.hxx`, the return type comes **before** `Tree<T>::`, so the compiler doesn't know yet that you're inside `Tree<T>`:

```cpp
// ❌ doesn't compile
template <typename T>
Tree<T>::Leaf* Tree<T>::first() const { ... }
```

Why: `Tree<T>::Leaf` depends on `T`. Until `T` is known, the compiler can't tell if `Leaf` is a **type** or a **static variable**. By default it assumes "not a type". You must tell it with `typename`:

```cpp
// ✅ option 1: typename
template <typename T>
typename Tree<T>::Leaf* Tree<T>::first() const { ... }

// ✅ option 2: trailing return type — after Tree<T>:: the compiler knows the scope
template <typename T>
auto Tree<T>::first() const -> Leaf* { ... }
```

> [!warning] Rule
> A type written as `Something<T>::Name` **outside** the class needs `typename` in front. Inside the class, or after the `Class<T>::method(` part, it doesn't.

______________________________________________________________________

## 6. Requirements on `T`

A template compiles only if `T` supports everything you **do** with it. The compiler checks this when it instantiates.

| You write in the template | `T` must support | `std::string` | `std::unique_ptr<int>` |
|---|---|---|---|
| `os << value` | `operator<<` | ✅ | ❌ |
| `T copy = value;` | copy | ✅ | ❌ |
| `T moved = std::move(value);` | move | ✅ | ✅ |
| `a < b` | `operator<` | ✅ | ✅ (compares addresses) |

> [!info] Good news
> A method is only generated **if it's called**. So `GenericStack<std::unique_ptr<int>>` compiles even if `print` uses `<<`, **as long as the test never calls `print` on it**.

______________________________________________________________________

## 7. Move semantics: supporting move-only types

`std::unique_ptr<int>` **can't be copied**, only moved. To make your template work with it (the 1-point "Advanced" part), **never copy a `T`**. Move it instead.

### Passing a `T` into the function

```cpp
void push(T value);          // by value: the caller copies OR moves in
```

- Called with a variable: `s.push(x)` → `x` is **copied** into `value` (fine for strings).
- Called with a temporary: `s.push(std::make_unique<int>(12))` → it's **moved** into `value`. ✅

Then, inside, **move** `value` to its final place:

```cpp
node->value = std::move(value);   // ✅ works for any T
node->value = value;              // ❌ copy → fails for unique_ptr
```

### Taking a `T` out of the container

When you remove an element and return it, move it out before the node is destroyed:

```cpp
T result = std::move(node->value);   // ✅
T result = node->value;              // ❌ copy
return result;                        // returning a local is fine: automatic move
```

> [!tip] What `std::move` really does
> `std::move(x)` doesn't move anything by itself. It says "you may steal from `x`". The actual move happens in the constructor or `=` that receives it. After that, `x` is in an empty but valid state, so don't read it again.

### Constructing the node

```cpp
auto node = std::make_unique<Node>();
```

That requires `T` to be **default-constructible** (`T{}` must work). `int`, `std::string` and `std::unique_ptr` all are. Fine for this exercise.

______________________________________________________________________

## 8. Common errors and what they mean

| Error message (roughly) | Probable cause |
|---|---|
| `undefined reference to GenericStack<...>::push` | bodies in a `.cc`, or the `.hxx` isn't included at the end of the `.hh` |
| `need 'typename' before 'X<T>::Node' because ... is a dependent scope` | §5: add `typename` |
| `invalid use of template-name 'X' without an argument list` | wrote `X::method` instead of `X<T>::method` |
| `use of deleted function unique_ptr(const unique_ptr&)` | a `T` is copied somewhere → use `std::move` (§7) |
| `no match for 'operator<<'` | `print` was called with a `T` that has no `<<` |

> [!warning] Template error messages are long
> Read the **first** error line that points into **your** file. Everything after it is usually the compiler explaining where it was instantiated from.

______________________________________________________________________

## 9. Checklist: IntStack → GenericStack

- [ ] `template <typename T>` before the class
- [ ] every `int` that means "the element" → `T` (but `length()` stays `std::size_t`)
- [ ] `IntNode` → `GenericNode`, with `T value;`
- [ ] declaration in `generic_stack.hh`, bodies in `generic_stack.hxx`
- [ ] `#include "generic_stack.hxx"` as the **last line** of the `.hh`
- [ ] every definition: `template <typename T>` + `GenericStack<T>::`
- [ ] `typename GenericStack<T>::GenericNode*` for `top()`'s return type (or trailing return)
- [ ] `push` takes `T` by value, then `std::move`
- [ ] `pop` moves the value **out** before the node is freed
- [ ] `print` writes `value` with `<<` into `os`
- [ ] same `const` methods as `IntStack`

______________________________________________________________________

## 10. Check yourself

1. Why can't `GenericStack`'s method bodies go in a `generic_stack.cc`?
1. What does the compiler need `typename` for in `typename GenericStack<T>::GenericNode*`?
1. In `push(T value)`, what happens when the caller passes `std::make_unique<int>(12)`? What about a named `std::string` variable?
1. Why does `pop` have to `std::move` the value out **before** `top_` is reassigned?
1. `GenericStack<std::unique_ptr<int>>` has a `print` that uses `<<`. Why does it still compile?

#cpp #templates

## Links

- [[C++ Syntax]]
- [[C++ Lambdas, Closures & Functions Returning Functions]]
- [[C++ Functors]]
