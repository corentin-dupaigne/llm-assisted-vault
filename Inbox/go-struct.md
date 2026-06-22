
## Declaration

```go
type User struct {
    Name string
    Age  int
}
```

## Instantiation

```go
u := User{Name: "Alice", Age: 30} // named fields
u := User{"Alice", 30}            // positional (avoid: brittle)
u := User{}                        // zero value: "", 0
p := &User{Name: "Bob"}            // pointer to struct
```

## Access

```go
u.Name = "Carol"   // works through value or pointer (auto-deref)
```

## Methods

```go
func (u User) Greet() string      { return "Hi " + u.Name } // value receiver: copy
func (u *User) SetAge(a int)       { u.Age = a }             // pointer receiver: mutates
```

> [!tip] Receiver rule
> Use a **pointer receiver** to mutate, or when the struct is large. Keep it consistent across all methods of a type.

## Embedding (composition)

```go
type Admin struct {
    User        // embedded: promotes Name, Age, Greet()
    Level int
}

a.Name      // accessed directly
a.Greet()   // promoted method
```

## Tags

```go
type User struct {
    Name string `json:"name"`
    Age  int    `json:"age,omitempty"`
}
```