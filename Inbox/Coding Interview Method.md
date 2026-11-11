
> [!summary] The one rule
> **List the cases before coding. Trace by hand before running.**
> My mock 1 bugs (infinite `continue`, space leaking into the next word, missing last word, `r > 0`) would all have been caught by these two steps.

Time budget for an easy problem: **~3 min understand → ~2 min plan → ~7 min code → ~3 min test**

---

## 1. Understand (2–3 min) — before touching the keyboard

- [ ] Restate the problem in one sentence, out loud.
- [ ] Check input and output: types, return value when there is no answer.
- [ ] Ask at least one clarifying question:
  - Characters: ASCII only? Upper/lowercase? (ASCII means bytes are fine, no runes needed)
  - Empty input? Duplicates? Negative numbers?
  - Repeated separators? Leading or trailing spaces?
  - **"May I use the standard library?"** (`strings.Fields`, `sort`…). This shows I know it exists, even if the answer is no.
- [ ] **Read the constraints as hints:**

| Hint in the statement | Think of |
|---|---|
| Sorted | two pointers, binary search |
| Contiguous subarray or substring | sliding window |
| One pass on a list | two pointers (fixed gap or different speeds) |
| O(1) memory | pointers, in-place |
| Parentheses, nearest element to the left | stack |
| By level, shortest path | BFS |
| BST, k-th, order | in-order traversal |
| Count, seen before? | map |
| Missing number in 1..n | sum or XOR (O(n)), binary search if sorted |

## 2. Examples (1 min)

- [ ] Write **one normal case and two edge cases** as comments.
- [ ] Solve them **by hand**. How I do it by hand is often the algorithm.
- [ ] **Check my idea against the expected output** before going further. (Mock 1: reversing the characters gives "eulb", not "blue".)

Standard edge cases:
- empty / a single element / everything identical
- strings: spaces at the start, end and middle; only spaces; a single word
- lists: `nil`, one node, the target is the head
- trees: `nil`, a single node, a degenerate tree (one long branch)

## 3. Brute force, then optimise (2 min)

- [ ] State the brute force and its complexity, even if it's bad. **I always have something to say.**
- [ ] What does it recompute? What could I remember (a map, a counter)? Which constraint am I not using yet?
- [ ] Give the time **and** space complexity of the final approach. Space for recursion = depth of the call stack.
- [ ] Ask: "Does this approach sound good before I code it?"

## 4. Plan — write the cases as comments (1 min)

```go
// for each char:
//   space + empty cur   -> skip
//   space + word in cur -> save cur, reset
//   other               -> append to cur
// after loop: save cur if not empty
```

- [ ] Every branch is listed **before** any code.
- [ ] **Too many `if`s?** Look for a single rule instead: a neutral value for anything missing (0, `""`, a dummy node), or **compute first, then split** (`sum % 10`, `sum / 10`).

## 5. Code (~7 min) — narrate while typing

- [ ] Code the plan. If I drift away from it, stop and update the plan.
- [ ] **If I announce an optimisation, implement it**, or say out loud why I'm dropping it.
- [ ] Pointer reflexes:
  - Before changing `.Next`, ask whether I still need the old value. If so, save it first (`next := cur.Next`).
  - If the head can change, use a dummy node or return the new head.
  - Go passes everything **by value**, pointers included: `n = nil` inside a function changes nothing for the caller.
- [ ] Sliding window: **whatever I add on the right, I remove on the left.**
- [ ] `continue` inside a `for` restarts **that** loop. To skip an element, use `if`, not `for`.

## 6. Trace by hand (1–2 min) — BEFORE `go run`

- [ ] Run the normal example line by line and write down the variables at each step.
- [ ] Check the **boundaries**: the first and last iteration, `>` vs `>=`, `len-1`.
- [ ] Check what happens **after the loop** (the last element is often forgotten).
- [ ] Read the code as if someone else had written it.

## 7. Test (2–3 min)

- [ ] Use `fmt.Printf("%q\n", got)` to **see the spaces**. (`Println("%q", x)` does not format anything!)
- [ ] Run the normal case plus the edge cases from step 2.
- [ ] Give the final complexity again, unprompted.

---

## If I get stuck

| Stuck for | Do this |
|---|---|
| 1 min | Go back to the brute force and the by-hand examples |
| 3 min | Say out loud what's blocking me: "I'm not sure how to handle X" |
| 5 min | Ask the interviewer for a hint. It's better than a silent loop |

Saying "I'm thinking about whether a stack helps here" is better than silence.

---

## Go idioms to type without thinking

```go
var sb strings.Builder        // O(1) amortised append; += is O(n) each time
sb.WriteString(w); sb.WriteByte(' ')
res := sb.String()

fmt.Printf("%q\n", s)         // shows leading/trailing spaces
words := strings.Fields(s)    // splits on any run of spaces
strings.Join(words, " ")

b := []byte(s); s = string(b) // mutable copy of a string
sort.Slice(b, func(i, j int) bool { return b[i] < b[j] })

var words []string            // nil slice: fine for append
// words := nil              -> does NOT compile
```

```go
// List helpers to retype from memory
type Node struct{ Val int; Next *Node }
func build(v []int) *Node { d := &Node{}; c := d
    for _, x := range v { c.Next = &Node{Val: x}; c = c.Next }; return d.Next }
func show(n *Node) { for ; n != nil; n = n.Next { fmt.Print(n.Val, " ") }; fmt.Println() }
```

## Environment (Arista)

- Plain `vi`/`vim` over SSH, so practise with `nvim --clean`. **No LSP to catch typos.**
- A single file is enough: `go run main.go`, no `go mod init` needed.
- Expect 2–4 questions in 1h30, so keep each easy one around 12 minutes.

## After each practice problem

- [ ] Write one line: **"The hint that should have pointed me to the solution was ___."**
- [ ] Note where I got stuck in the LeetCode note (the "Where I got stuck" field).