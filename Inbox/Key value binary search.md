---
difficulty: medium
neetcode_section: "Binary Search"
struggled: false
project: neetcode-150
date_solved: 2026-07-05
tags: [leetcode, neetcode-150, binary-search]
---
## Initial Intuition

<!-- Before coding: pattern recognized? Approach envisioned? Edge cases? -->


## My Solution

```go
type Entry struct {
	value string
	timestamp int
}

type TimeMap struct {
	m map[string][]Entry
}

func Constructor() TimeMap {
	return TimeMap{make(map[string][]Entry)}	
}

func (this *TimeMap) Set(key string, value string, timestamp int) {
	this.m[key] = append(this.m[key], Entry{value, timestamp})
}

func (this *TimeMap) Get(key string, timestamp int) string {
	if val, ok := this.m[key]; ok {
		i, j := 0, len(val) - 1
		mid := (i + j) / 2
		mostRecent := val[0]
		for i <= j {
			if val[mid].timestamp <= timestamp {
				mostRecent = val[mid]
				i = mid + 1
			} else {
				j = mid - 1
			}
			mid = (i + j) / 2
		}

		if mostRecent.timestamp <= timestamp {
			return mostRecent.value
		}
	}

	return ""
}



// Time: O(n)
// Space: O(log(n))

```

### Optimal Solution

```go
type Entry struct {
	value string
	timestamp int
}

type TimeMap struct {
	m map[string][]Entry
}

func Constructor() TimeMap {
	return TimeMap{make(map[string][]Entry)}	
}

func (this *TimeMap) Set(key string, value string, timestamp int) {
	this.m[key] = append(this.m[key], Entry{value, timestamp})
}

func (this *TimeMap) Get(key string, timestamp int) string {
	if val, ok := this.m[key]; ok {
		i, j := 0, len(val) - 1
		idx := -1
		for i <= j {
			mid := (i + j) / 2
			if val[mid].timestamp <= timestamp {
				idx = mid
				i = mid + 1
			} else {
				j = mid - 1
			}
		}

		if idx != -1 {
			return val[idx].value
		}
	}

	return ""
}


// Time: O(n)
// Space: O(log(n))

```

## Delta

My solution was optimal for complexity but could have been better in code quality.

## Review Log

- 2026-07-05 — first solve
