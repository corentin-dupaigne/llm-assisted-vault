---
domain: golang
tags: [hashmap]
date: 2026-06-11
para: Resources
project: null
---
## domain: golang

## Basic operations

```go
// declare
m := make(map[string]int)

// write
m["key] = 42

// read - returns zero value if key is missing
v := m["key"]

// existence check - preferred method
v, ok := m["key"]
if !ok {
	// key not present
}

// length
n := len(m)
```

## Iteration

```go
// order is random on every run
for k, v := range m {
	fmt.Println(k, v)
}

// keys only
for k := range m { ... }
```

## Compare

```go
import "maps"

// check if maps are equal
a := map[string]int{"a": 1, "b": 2}
b := map[string]int{"a": 1, "b": 2}
fmt.Println(maps.Equal(a, b))  // true
```

## Links

- [[Go Loops And Range Iteration]]
- [[Contains Duplicate]]
- [[Valid Anagram]]

## Links

- [[golang-loops|Golang Loops And Range]]
- [[contains-duplicate|Contains Duplicate]]
