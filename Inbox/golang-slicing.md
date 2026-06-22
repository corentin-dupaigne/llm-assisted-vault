
The `a[low:high]` expression is a **slice expression**; using it is called **slicing**.

## Forms

```go
a[low:high]      // elements low .. high-1
a[low:high:max]  // full slice expression, also sets capacity
```

- `low` defaults to `0`, `high` defaults to `len(a)`.
- Result is a **slice**, even when `a` is an array.
- `len = high - low`, `cap = (max or len(a)) - low`.

```go
arr := [5]int{10, 20, 30, 40, 50}
arr[1:4]   // [20 30 40]
arr[:3]    // [10 20 30]
arr[2:]    // [30 40 50]
arr[:]     // whole thing
```
