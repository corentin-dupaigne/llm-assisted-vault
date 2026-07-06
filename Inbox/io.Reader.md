
The fundamental streaming-input interface in Go. A single method; anything that implements it can be read from uniformly.

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

## Contract
- Copies **up to** `len(p)` bytes into `p`, returns `n` = bytes actually copied.
- May return `0 < n < len(p)` — never assume the buffer is filled.
- Can return `n > 0` **and** a non-nil `err` (incl. `io.EOF`) together → process `p[:n]` *first*, then check `err`.
- `io.EOF` signals the stream is exhausted.

## Why it matters
One tiny method → composability. Readers wrap readers, each layer still an `io.Reader`:

```go
gzip.NewReader(bufio.NewReader(file))
```

## Common usage
Rarely called directly — wrap it instead:

```go
data, _ := io.ReadAll(r)          // whole stream → []byte
scanner := bufio.NewScanner(r)    // line-oriented
io.Copy(dst, r)                   // stream to a writer
```

---

## Related concepts

### io.Writer
The symmetric output interface — same shape, opposite direction.

```go
type Writer interface {
    Write(p []byte) (n int, err error)
}
```

- `Write` sends `len(p)` bytes to the destination, returns `n` written.
- Contract is *stricter* than Reader's: a `Writer` **must** return `err != nil` if it wrote `n < len(p)`. A short write is always an error.
- Combine the two for bidirectional streams: `io.ReadWriter` (e.g. a `net.Conn`).

### os.Stdin
Standard input, declared as an `*os.File` wrapping file descriptor 0:

```go
var Stdin = NewFile(uintptr(syscall.Stdin), "/dev/stdin")
```

Because `*os.File` has a `Read` method, `os.Stdin` **is** an `io.Reader` — pass it anywhere a reader is expected. Its `Read` bottoms out in the `read(2)` syscall on fd 0; the runtime parks the goroutine (via the poller / `EAGAIN` retry) until data is available, so reads *block* from your code's view without wasting an OS thread.

```go
json.NewDecoder(os.Stdin).Decode(&conf)   // stream-parse straight off fd 0
```

> `os.Stdout` / `os.Stderr` are the `io.Writer` counterparts (fds 1 and 2).

### io.ReadAll
Reads an *entire* stream into one owned `[]byte`.

```go
func ReadAll(r io.Reader) ([]byte, error)
```

- Loops `Read` on its **own** growing buffer (starts cap 512, doubles) until EOF.
- Returns a slice sized exactly to the content — all of it valid, no `n` to track.
- **Swallows `io.EOF`**: a non-nil error back means a *real* failure, not stream end.
- Caveats: blocks until the source is **closed**, and holds everything in RAM. Guard untrusted input with `io.LimitReader(r, max)`.

### io.EOF
The sentinel error meaning "no more input."

```go
var EOF = errors.New("EOF")
```

- Returned by `Read` when the stream is exhausted; it's the normal loop terminator, **not** a failure.
- `io.ErrUnexpectedEOF` is the *distinct* error for hitting EOF mid-value (e.g. a truncated read that expected more).

## Mental model
`Read` = "give me the next chunk, once." `io.ReadAll` = "keep calling `Read` until `io.EOF`, give me everything." `io.Writer` = the same primitive in reverse. `os.Stdin` = a concrete `io.Reader` you get for free.