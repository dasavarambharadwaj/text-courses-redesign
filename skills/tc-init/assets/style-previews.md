# Style Voice Previews

Comparative samples illustrating how different pedagogical voices present the same concept.

## Sample Concept: Lock Contention & Mutexes

### [A] Direct Technical & Internals
A mutex protects shared memory via atomic compare-and-swap (CAS) instructions. Under high contention, threads spin or trigger kernel context switches via `futex`, causing CPU cache line bouncing and degrading execution throughput from $O(1)$ to $O(N)$.

### [B] Analogy & Intuition
Think of a mutex as a single physical key to a private conference room. When multiple workers rush the door at once, only one can enter; the rest must wait in the hallway, stalling the overall workflow until the key is returned.

### [C] Code & Case-First
```rust
// std::sync::Mutex blocks the caller thread when poisoned or locked
let counter = Arc::new(Mutex::new(0));
let c = Arc::clone(&counter);
thread::spawn(move || {
    let mut num = c.lock().unwrap();
    *num += 1;
});
```
In benchmarks with 16 threads mutating a shared counter, lock contention introduces a 4.2x latency penalty compared to lock-free atomic `fetch_add`.

### [D] First-Principles & Math
Let $P$ represent the critical section execution duration and $\lambda$ the request arrival rate. When $\lambda \cdot P \ge 1$, queue length diverges by Little's Law ($L = \lambda W$), transitioning memory latency from constant to linear time complexity.
