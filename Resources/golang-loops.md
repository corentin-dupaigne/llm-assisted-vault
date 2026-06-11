---
domain: golang
tags: []
date: 2026-06-11
para: Resources
project: null
---
## Basic

```go
for i := 0; i < 5; i++ {
	fmt.Println(i)
}
```

## While-style

```go
i := 0
for i < 5 {
	fmt.Println(i)
	i++
}
```

## Infinite loop

```go
for {
	// runs forever
}
```

## Range (for each)

```go
// index only
for i := range nums { ... }

// value only
for _, v := range nums { ... }

// map — key and value (order is random)
m := map[string]int{"a": 1, "b": 2}
for k, v := range m {
    fmt.Println(k, v)
}

// string — iterates over runes
for i, r := range "héllo" {
    fmt.Printf("%d: %c\n", i, r)
}

## Links

- [[contains-duplicate|Contains Duplicate]]
```
