Arrays in Go have a **fixed size** defined at compile time. The size is part of the type — `[3]int` and `[5]int` are two different types.

In practice, arrays are rarely used directly — slices are preferred. But understanding arrays is necessary to understand slices.

---

## Declaration & init

```go
// zero-valued (all elements = 0)
var a [3]int  // [0 0 0]

// literal
a := [3]int{1, 2, 3}

// let the compiler count the size
a := [...]int{1, 2, 3}  // equivalent to [3]int

// partial init — rest is zero-valued
a := [5]int{1, 2}  // [1 2 0 0 0]

// init specific indices
a := [5]int{0: 10, 4: 99}  // [10 0 0 0 99]
```

---

## Access & update

```go
a := [3]int{10, 20, 30}

// read
fmt.Println(a[0])  // 10

// write
a[1] = 99  // [10 99 30]

// length — always fixed, known at compile time
fmt.Println(len(a))  // 3
```

---

## Iteration

```go
a := [3]int{10, 20, 30}

// classic for
for i := 0; i < len(a); i++ {
    fmt.Println(a[i])
}

// range — index and value
for i, v := range a {
    fmt.Println(i, v)
}

// range — value only
for _, v := range a {
    fmt.Println(v)
}
```

---

## Arrays are value types

Unlike slices and maps, assigning an array copies the entire data.

```go
a := [3]int{1, 2, 3}
b := a        // full copy
b[0] = 99

fmt.Println(a)  // [1 2 3] — unchanged
fmt.Println(b)  // [99 2 3]
```

To avoid copying (e.g. large arrays), pass a pointer:

```go
func double(a *[3]int) {
    for i := range a {
        a[i] *= 2
    }
}

double(&a)
```

---

## Comparison

```go
a := [3]int{1, 2, 3}
b := [3]int{1, 2, 3}
c := [3]int{1, 2, 4}

fmt.Println(a == b)  // true
fmt.Println(a == c)  // false

// does not compile — different types
// fmt.Println(a == [5]int{1, 2, 3})
```

---

## Multi-dimensional arrays

```go
// 2D array (3 rows, 4 cols)
var grid [3][4]int

// literal
matrix := [2][3]int{
    {1, 2, 3},
    {4, 5, 6},
}

fmt.Println(matrix[1][2])  // 6

// iterate
for _, row := range matrix {
    for _, v := range row {
        fmt.Print(v, " ")
    }
    fmt.Println()
}
```

---
## From array to slice

A slice is just a window into an array. You can create a slice from an array:

```go
a := [5]int{1, 2, 3, 4, 5}

s := a[1:4]     // [2 3 4] — slice of a
s[0] = 99       // modifies a too!

fmt.Println(a)  // [1 99 3 4 5]
fmt.Println(s)  // [99 3 4]
```
