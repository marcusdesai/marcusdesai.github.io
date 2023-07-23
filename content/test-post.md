Title: Test Post
Date: 2023-07-21

This is a test.

    :::rust
    println!("The path-less shebang syntax *will* show line numbers.")

```rust
// test some code
fn nice_func() -> u32 {
    panic!("not so nice")
}
```

```rust
// some more complicated rust, to test highlighting
struct S<T: Copy + Clone> {
    tt: [T; 10],
}

impl<T> S<T>
    where T: Copy + Clone
{
    fn new(arr: [T; 10]) -> Self {
        S(arr)
    }
}
```

```python
def func(x: int) -> float:
    return float(x)
```
