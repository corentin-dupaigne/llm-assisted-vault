---
difficulty: medium
neetcode_section: "Stack"
struggled: true
project: neetcode-150
date_solved: 2026-06-22
tags: [leetcode, neetcode-150, stack]
---
## Initial Intuition

Je n'ai eu aucune intuition sur la solution, j'ai effectue l'exercice en visualisant la solution de l'algorithme.


## My Solution

```go
import "slices"

type Car struct {
	Pos int
	Speed int
}

func carFleet(target int, position []int, speed []int) int {

	var cars []Car

	for i := range position {
		cars = append(cars, Car{position[i], speed[i]})
	}

	slices.SortFunc(cars, func(a, b Car) int {
		return b.Pos - a.Pos
	})

	var s []float64

	for i, car := range cars {
		if i == 0 {
			time := (float64(target - car.Pos)) / float64(car.Speed)
			s = append(s, time)
			continue
		}

		oldTime := s[len(s) - 1]
		time := (float64(target - car.Pos)) / float64(car.Speed)
		fmt.Println(time)
		s = append(s, time)

		if time <= oldTime {
			s = s[:len(s) - 1]
		}
	}

	return len(s)
}

// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
import "slices"

type Car struct {
	Pos int
	Speed int
}

func carFleet(target int, position []int, speed []int) int {

	var cars []Car

	for i := range position {
		cars = append(cars, Car{position[i], speed[i]})
	}

	slices.SortFunc(cars, func(a, b Car) int {
		return b.Pos - a.Pos
	})

	var s []float64

	for i, car := range cars {

		time := (float64(target - car.Pos)) / float64(car.Speed)

		if i == 0 || time > s[len(s) - 1] {
			s = append(s, time)
		}
	}

	return len(s)
}


// Time: O(n)
// Space: O(n)

```

## Delta

Ma solution est optimale en complexite mais pourrait etre plus propre. Je fais beaucoup d'operations ou je push puis pop juste apres.

## Review Log

- 2026-06-22 — first solve
