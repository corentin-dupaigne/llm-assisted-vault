## Primitive slices

```go
import "slices"

slices.Sort([]int{3, 1, 2})             // [1 2 3]
slices.Sort([]string{"b", "c", "a"})    // [a b c]
slices.Sort([]float64{3.14, 1.41})      // [1.41 3.14]
```

---

## Reverse

```go
slices.Sort(s)
slices.Reverse(s)
```

---

## Custom sort (structs)

```go
// Go 1.21+ — return negative if a before b, 0 if equal, positive if b before a
slices.SortFunc(people, func(a, b Person) int {
    return a.Age - b.Age
})

// pre-1.21
sort.Slice(people, func(i, j int) bool {
    return people[i].Age < people[j].Age
})
```
