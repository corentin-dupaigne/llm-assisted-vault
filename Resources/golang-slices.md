---
domain: golang
tags: []
date: 2026-06-11
para: Resources
project: null
---
A slice is a dynamic view into an underlying array. It has three components: a **pointer** to the array, a **length**, and a **capacity**.

In practice, slices are what you use 95% of the time instead of arrays.

______________________________________________________________________

## Declaration & init

```go
// nil slice (zero value) — safe to append to
var s []int

// make(type, length, capacity)
s = make([]int, 3)      // [0 0 0] — len=3, cap=3
s = make([]int, 3, 10)  // [0 0 0] — len=3, cap=10

// literal
s := []int{1, 2, 3}

// partial init with specific indices
s := []int{0: 10, 4: 99}  // [10 0 0 0 99]

// from an array
a := [5]int{1, 2, 3, 4, 5}
s := a[1:4]  // [2 3 4]
```

______________________________________________________________________

## Length and capacity

```go
s := make([]int, 3, 10)

fmt.Println(len(s))  // 3 — number of elements you can access
fmt.Println(cap(s))  // 10 — total space in underlying array

// len > cap is impossible
// len <= cap always
```

______________________________________________________________________

## Access & update

```go
s := []int{10, 20, 30}

// read
fmt.Println(s[0])  // 10

// write
s[1] = 99  // [10 99 30]

// last element
fmt.Println(s[len(s)-1])  // 30
```

______________________________________________________________________

## append

```go
s := []int{1, 2, 3}

// append one element
s = append(s, 4)  // [1 2 3 4]

// append multiple
s = append(s, 5, 6, 7)  // [1 2 3 4 5 6 7]

// append another slice (note the ...)
other := []int{8, 9}
s = append(s, other...)  // [1 2 3 4 5 6 7 8 9]
```

When `append` exceeds capacity, Go allocates a new larger array and copies the data. The growth factor is roughly 2x for small slices.

______________________________________________________________________

## Slicing (sub-slices)

```go
s := []int{0, 1, 2, 3, 4}

s[1:3]   // [1 2]     — from index 1 (inclusive) to 3 (exclusive)
s[:3]    // [0 1 2]   — from start to 3
s[2:]    // [2 3 4]   — from 2 to end
s[:]     // [0 1 2 3 4] — full slice

// three-index slice — controls capacity of the result
s[1:3:4]  // len=2, cap=3 (limits how far append can reach into original)
```

______________________________________________________________________

## copy

`copy` copies elements between slices. It does NOT share the underlying array.

```go
src := []int{1, 2, 3}
dst := make([]int, len(src))

n := copy(dst, src)  // n = number of elements copied

dst[0] = 99
fmt.Println(src)  // [1 2 3] — unchanged
fmt.Println(dst)  // [99 2 3]
```

`copy` copies `min(len(dst), len(src))` elements — the shorter slice wins.

______________________________________________________________________

## delete an element

Go has no built-in delete for slices. Common approaches:

```go
s := []int{1, 2, 3, 4, 5}
i := 2  // index to delete

// preserving order — shift elements left (O(n))
s = append(s[:i], s[i+1:]...)  // [1 2 4 5]

// without preserving order — swap with last element (O(1))
s[i] = s[len(s)-1]
s = s[:len(s)-1]  // [1 2 5 4]
```

______________________________________________________________________

### Contains

```go
// no built-in — check manually
func contains(s []int, target int) bool {
    for _, v := range s {
        if v == target {
            return true
        }
    }
    return false
}

// Go 1.21+: use slices package
import "slices"
slices.Contains(s, target)
```

______________________________________________________________________

## Slices are reference types

```go
a := []int{1, 2, 3}
b := a        // b points to the same underlying array
b[0] = 99

fmt.Println(a)  // [99 2 3] — modified!
fmt.Println(b)  // [99 2 3]

// to get a real copy:
c := make([]int, len(a))
copy(c, a)
// or Go 1.21+:
c := slices.Clone(a)
```

## Links

- [[golang-arrays|Golang Array]]
- [[golang-maps|Golang Maps Cheatsheet]]
- [[golang-loops|Golang Loops And Range]]
