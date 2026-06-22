---
domain: golang
tags: []
date: 2026-06-22
para: Resources
project: null
---
An **interface** is a set of method signatures. A type satisfies it **implicitly** — just by having those methods, no `implements` keyword.

## Declaration

```go
type Stringer interface {
    String() string
}
```

## Satisfaction (implicit)

```go
type User struct {
	Name string 
}

func (u User) String() string { 
	return u.Name
}

var s Stringer = User{"Alice"} // satisfied automatically
```

## The empty interface

```go
var x any          // any = interface{}, holds any value
x = 42
x = "hello"
```

## Type assertion & switch

```go
s, ok := x.(string)        // comma-ok: ok=false instead of panic

switch v := x.(type) {     // type switch
case int:    // v is int
case string: // v is string
default:
}
```

> [!tip] Accept interfaces, return structs
> Take interfaces as parameters for flexibility; return concrete types so callers keep full information.

## Composition

```go
type ReadWriter interface {
    Reader
    Writer
}
```

> [!note] Key facts
>
> - An interface value is a pair: **(type, value)**.
> - A nil interface (`type=nil, value=nil`) differs from an interface holding a nil pointer — the classic `err != nil` trap.
> - Keep interfaces **small**: `io.Reader` is one method. Big interfaces are a smell.
> - Define interfaces on the **consumer** side, not the producer.

## See also

- [[Go Struct]]
- [[Go Errors]]
- [[Go Generics]]

## Links

- [[golang-maps|Golang Maps Cheatsheet]]
- [[golang-slices|Golang Slices]]
- [[golang-strings|String Manipulation Golang]]
