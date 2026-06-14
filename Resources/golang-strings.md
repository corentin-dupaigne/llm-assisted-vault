---
domain: golang
tags: []
date: 2026-06-14
para: Resources
project: null
---
A string in Go is an **immutable** sequence of bytes — usually UTF-8 encoded text. You cannot modify a string in place; any "change" produces a new string.
The key gotcha: indexing gives you **bytes**, not characters. For Unicode-safe work you iterate over **runes** (`rune` = `int32` = one Unicode code point).

______________________________________________________________________

## Declaration & init

```go
// literal
s := "hello"
// zero value is "" (empty string), not nil
var s string  // ""
// raw string literal (backticks) — no escaping, keeps newlines
path := `C:\Users\foo`        // backslashes stay literal
multi := `line 1
line 2`                       // real newline included
// from bytes / runes
s := string([]byte{104, 105})  // "hi"
s := string([]rune{'h', 'i'})  // "hi"
s := string(rune(65))          // "A" — code point to string
```

______________________________________________________________________

## Length: bytes vs runes

```go
s := "héllo"
len(s)                          // 6 — BYTES (é is 2 bytes in UTF-8)
utf8.RuneCountInString(s)       // 5 — actual characters
len([]rune(s))                  // 5 — same, but allocates
```

`len` is always byte count. This trips people up with any non-ASCII text.

______________________________________________________________________

## Access & iteration

```go
s := "héllo"
// index → a BYTE (uint8), not a character
s[0]                 // 104 (the byte 'h')
fmt.Printf("%c", s[0]) // h
// range → iterates by RUNE, index is the byte offset
for i, r := range s {
    fmt.Printf("%d: %c\n", i, r)
}
// i jumps 0,1,3,4,5 — because é occupies 2 bytes
```

To iterate byte-by-byte instead, use a classic `for i := 0; i < len(s); i++`.

______________________________________________________________________

## Concatenation

```go
// + operator (fine for a few)
s := "foo" + "bar"
// in a loop, NEVER use + repeatedly (O(n²)) — use strings.Builder
var b strings.Builder
for i := 0; i < 3; i++ {
    b.WriteString("x")
}
result := b.String()  // "xxx"
// Sprintf — convenient, not the fastest
s := fmt.Sprintf("%s-%d", "id", 42)  // "id-42"
// join a slice with a separator
strings.Join([]string{"a", "b", "c"}, ", ")  // "a, b, c"
```

______________________________________________________________________

## strings package — the workhorses

```go
import "strings"
strings.Contains("seafood", "foo")     // true
strings.HasPrefix("golang", "go")      // true
strings.HasSuffix("file.go", ".go")    // true
strings.Index("chicken", "ken")        // 4 (-1 if not found)
strings.Count("cheese", "e")           // 3
strings.ToUpper("hi")                  // "HI"
strings.ToLower("HI")                  // "hi"
strings.Replace("oink oink", "k", "ky", 2)  // "oinky oinky" (2 = max replacements)
strings.ReplaceAll("oink oink", "k", "ky")  // replace all
strings.Repeat("ab", 3)                // "ababab"
```

______________________________________________________________________

## Trim & split

```go
strings.TrimSpace("  hi  ")            // "hi"
strings.Trim("xxhixx", "x")            // "hi" — trims any of the chars
strings.TrimPrefix("file.go", "file")  // ".go"
strings.TrimSuffix("file.go", ".go")   // "file"
strings.Split("a,b,c", ",")            // ["a" "b" "c"]
strings.SplitN("a,b,c", ",", 2)        // ["a" "b,c"]
strings.Fields("  foo   bar ")         // ["foo" "bar"] — splits on whitespace
```

______________________________________________________________________

## Conversions ([]byte / []rune)

```go
// string ↔ []byte — cheap-ish, used for mutation
b := []byte("hello")
b[0] = 'H'
s := string(b)         // "Hello"
// string ↔ []rune — for Unicode-correct indexing
r := []rune("héllo")
r[1]                   // 'é' (the actual character)
string(r[:2])          // "hé"
```

Convert to `[]rune` when you need real character positions; to `[]byte` for raw byte ops.

______________________________________________________________________

## strconv — strings ↔ numbers

```go
import "strconv"
n, err := strconv.Atoi("42")        // 42, string → int
s := strconv.Itoa(42)               // "42", int → string
f, err := strconv.ParseFloat("3.14", 64)  // 3.14
b, err := strconv.ParseBool("true")        // true
// don't use string(65) expecting "65" — it gives "A"!
```

______________________________________________________________________

## Building strings efficiently

`strings.Builder` avoids repeated allocations — use it in loops.

```go
var b strings.Builder
b.Grow(64)                 // optional: pre-allocate if size is known
b.WriteString("hello")
b.WriteByte(' ')
b.WriteRune('☺')
fmt.Println(b.String())    // "hello ☺"
```

______________________________________________________________________

## Common gotchas

```go
// strings are immutable — this does NOT compile:
s := "hi"
// s[0] = 'H'   ❌ cannot assign to s[0]
// indexing returns a byte, comparison must be a byte too
s := "abc"
s[0] == 'a'    // true ('a' is a rune/byte constant)
// comparing strings: ==, <, > work lexicographically by byte
"apple" < "banana"   // true
```

## Links

- [[golang-loops|Golang Loops And Range]]
- [[golang-maps|Golang Maps Cheatsheet]]
- [[golang-arrays|Golang Array]]
- [[golang-slices|Golang Slices]]
- [[golang-sorting|Golang Sorting]]
