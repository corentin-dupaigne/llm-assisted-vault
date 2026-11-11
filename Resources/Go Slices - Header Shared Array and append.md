---
domain: golang
tags: [arrays-hashing, leetcode]
date: 2026-11-11
para: Resources
project: null
---
## 1. Array vs slice: two different things

**An array** (`[4]int`) has a fixed size that is part of its type. `[4]int` and `[5]int` are two incompatible types. An array is a **value**: assigning it or passing it to a function copies all its elements.

```go
a := [3]int{1, 2, 3}
b := a      // full copy
b[0] = 99
fmt.Println(a[0]) // 1: a is not affected
```

**A slice** (`[]int`) is not an array. It is a small 3-field struct, called the **header**, that describes a window onto an array:

```go
type slice struct {
	ptr *T  // address of the first visible element
	len int // number of visible elements
	cap int // number of slots available from ptr to the end of the array
}
```

```
s = {ptr, len 3, cap 5}
      │
      ▼
T: [ 1  2  3  _  _ ]
     └─len─┘
     └────cap────┘
```

> [!important] Key takeaway
> A slice = **header** (small, copied by value) + **underlying array** (shared).

______________________________________________________________________

## 2. `len` and `cap`

```go
s := make([]int, 3, 10)
// array of 10 slots, all zero
// s = {ptr→T[0], len 3, cap 10}

fmt.Println(len(s), cap(s)) // 3 10
fmt.Println(s[2])           // 0
fmt.Println(s[3])           // panic: index out of range
```

- **`len`**: the slots reachable with `s[i]`. Beyond it, `s[i]` panics, **even if the slot exists in the array**.
- **`cap`**: the room available to grow without reallocating.

You can still "see" beyond `len` by reslicing, as long as you stay within `cap`:

```go
fmt.Println(s[:5]) // [0 0 0 0 0]: allowed since 5 <= cap
```

______________________________________________________________________

## 3. Pass by value: the header is copied

Go passes **everything** by value. When you pass a slice to a function, the function receives a **copy of the header**. Both headers point to the **same array**.

```go
func modify(x []int) {
	x[0] = 99        // writes into the shared array: visible outside
	x = append(x, 4) // modifies the header COPY: invisible outside
}

s := []int{1, 2, 3}
modify(s)
fmt.Println(s) // [99 2 3]
```

This is exactly the same principle as with a pointer:

```go
func f(n *Node) {
	n.Val = 0 // modifies the shared Node: visible outside
	n = nil   // modifies the pointer copy: invisible outside
}
```

> [!important] General rule
> Modifying **what is pointed to** → visible to the caller.
> Modifying **the variable itself** (the pointer, the header) → invisible to the caller.

______________________________________________________________________

## 4. `append`: the capacity rule

`append(s, x)` does the following:

1. **If `len(s) < cap(s)`**: it writes `x` into slot `len(s)` of the **same array**, then returns a new header `{same ptr, len+1, same cap}`.
1. **If `len(s) == cap(s)`**: it allocates a **new, larger array**, copies the elements over, writes `x`, then returns a header pointing to that new array.

In both cases, **`append` does not modify the variable `s`**: it can't, since it received a copy. It returns a new header. Hence the mandatory form:

```go
s = append(s, x) // without the reassignment, s does not "see" x
```

> [!note] Growth factor
> On reallocation, capacity roughly doubles for small slices and grows less for large ones. The exact factor is a runtime implementation detail: never rely on it.

______________________________________________________________________

## 5. The trap: two slices on the same array

```go
s := make([]int, 3, 10)
t := append(s, 4)
s = append(s, 5)
fmt.Println(t[3]) // 5!
```

**Trace:**

| Line | Array T (slots 0–4) | `s` | `t` |
|---|---|---|---|
| `make` | `[0 0 0 _ _]` | len 3 | — |
| `t := append(s, 4)` | `[0 0 0 4 _]` | len 3 (unchanged) | len 4 |
| `s = append(s, 5)` | `[0 0 0 5 _]` | len 4 | len 4 |

The second `append` starts from `len(s) = 3`, so it writes at index 3, **over `t`'s 4**.

The array's **data** is shared, but the **headers** are independent: nothing updates `t` or `s` automatically. A header only changes when you reassign the variable.

### The counter-example: when capacity is exceeded

```go
a := make([]int, 3, 3)
b := append(a, 4) // len == cap → new array for b
b[0] = 99
fmt.Println(a[0]) // 0: a and b no longer share anything
```

> [!important] Key takeaway
> As long as capacity suffices, two slices built from the same array **overwrite each other**. As soon as an `append` reallocates, they become **independent**. That's what makes the behavior look unpredictable if you don't check `cap`.

______________________________________________________________________

## 6. Reslicing shares the array too

```go
a := []int{1, 2, 3, 4, 5}
b := a[1:3] // b = {ptr→a[1], len 2, cap 4}
b[0] = 99
fmt.Println(a) // [1 99 3 4 5]
```

Watch out: `cap(b)` is 4, not 2. Capacity extends to the end of the original array. So:

```go
b = append(b, 100)
fmt.Println(a) // [1 99 3 100 5]: append overwrote a[3]!
```

______________________________________________________________________

## 7. Protecting against sharing

### Option 1: `copy`

```go
dst := make([]int, len(src))
copy(dst, src) // dst has its own array
```

Or as a one-liner:

```go
dst := append([]int(nil), src...)
```

### Option 2: the full slice expression `s[low:high:max]`

It caps the new slice's capacity at `max - low`. An `append` on that slice is then **forced to reallocate** instead of overwriting the rest of the array.

```go
a := []int{1, 2, 3, 4, 5}
b := a[1:3:3] // len 2, cap 2
b = append(b, 100) // cap exceeded → new array
fmt.Println(a) // [1 2 3 4 5]: a is intact
```

______________________________________________________________________

## 8. In interviews: the backtracking case

This is where the trap does the most damage. Example: generating all subsets.

```go
// ❌ BUGGY
var res [][]int
var cur []int
var dfs func(i int)
dfs = func(i int) {
	if i == len(nums) {
		res = append(res, cur) // stores cur's HEADER, not its contents
		return
	}
	cur = append(cur, nums[i])
	dfs(i + 1)
	cur = cur[:len(cur)-1]
	dfs(i + 1)
}
```

Every element of `res` points to the same array, which `cur` keeps modifying. In the end, `res` holds corrupted results.

```go
// ✅ CORRECT: copy before storing
res = append(res, append([]int(nil), cur...))
```

> [!tip] Reflex
> Before **storing** a slice you're going to keep modifying, **copy it**.

______________________________________________________________________

## 9. Summary

1. A slice = header `{ptr, len, cap}` + shared array.
1. The header is copied by value: a function cannot change your slice's `len`.
1. Always write `s = append(s, x)`.
1. `append` writes into the same array if `len < cap`, otherwise it reallocates.
1. Two slices on the same array overwrite each other until a reallocation happens.
1. Reslicing keeps capacity up to the end of the original array.
1. To isolate a slice: `copy`, `append([]int(nil), s...)` or `s[a:b:b]`.
1. In backtracking: copy before storing.

______________________________________________________________________

## 10. Exercises

Answer in your head first, then check with `go run`.

**Exercise 1**

```go
s := make([]int, 3, 10)
t := append(s, 4)
s = append(s, 5)
s = append(s, 6)
fmt.Println(t[3], len(s), len(t))
```

> [!note]- Answer
> `5 5 4`. The last `append` writes at index 4 (`len(s)` was 4). `t` has `len 4`, so it doesn't see index 4: `t[3]` is still 5. `s` goes to `len 5`, `t` stays at `len 4`.

**Exercise 2**

```go
func add(s []int) { s = append(s, 42) }

s := make([]int, 0, 5)
add(s)
fmt.Println(len(s), s[:1])
```

> [!note]- Answer
> `0 [42]`. `add` receives a copy of the header: `len(s)` stays 0 outside. But `append` wrote 42 into the shared array (cap 5 was enough), so reslicing up to 1 reveals it.

**Exercise 3**

```go
a := []int{1, 2, 3}
b := append(a, 4)
b[0] = 99
fmt.Println(a[0])
```

> [!note]- Answer
> `1`. A literal `[]int{1, 2, 3}` has `len 3, cap 3`. The `append` exceeds capacity and allocates a new array for `b`. `a` and `b` are independent.

**Exercise 4**

```go
a := []int{1, 2, 3, 4, 5}
b := a[:2]
b = append(b, 100)
fmt.Println(a)
```

> [!note]- Answer
> `[1 2 100 4 5]`. `b` has `len 2, cap 5`. The `append` writes at index 2 of the shared array, overwriting `a[2]`. To avoid it: `b := a[:2:2]`.

**Exercise 5**

Why is the following line a bug inside a backtracking function? How do you fix it?

```go
res = append(res, cur)
```

> [!note]- Answer
> It stores `cur`'s header, which points to an array the rest of the algorithm will keep modifying. All stored results end up reflecting that array's final state. Fix: `res = append(res, append([]int(nil), cur...))`.

______________________________________________________________________

## Further reading

- [Go Slices: usage and internals](https://go.dev/blog/slices-intro), the official Go blog

## Links

- [[golang-slices]]
- [[golang-arrays]]
- [[golang-slice-expressions]]
- [[golang-maps]]
