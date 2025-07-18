# 基于锁的并发在 Rust 中的基本用法

在 Rust 中，理解**所有权（Ownership）**和**借用（Borrowing）**是掌握并发和内存安全的关键。Rust 的编译器通过其独特的借用检查器（Borrow Checker）在编译时强制执行一系列规则，以防止数据竞争（Data Races）等并发问题。

---

## 借用规则：Rust 的核心安全机制

Rust 对借用有着严格的规则，这是其内存安全保证的基石。核心规则可以概括为：

在任何给定时间，你只能拥有以下两种借用之一，但不能同时拥有：

1. **一个或多个不可变借用（Immutable Borrows）**：你可以有任意数量的指向同一数据的不可变引用。这意味着你可以读取数据，但不能修改它。
2. **一个可变借用（Mutable Borrow）**：你只能有一个指向同一数据的可变引用。这意味着你可以读取和修改数据。

违反这些规则会导致编译错误。以下是一些具体的不允许情况：

- **多个可变借用**：例如，`let var1 = &mut x; let var2 = &mut x;` 是不允许的，因为这可能导致数据不一致。
- **不可变借用和可变借用同时存在**：例如，`let var1 = &x; let var2 = &mut x;` 是不允许的，因为可变借用可能在不可变借用活跃期间修改数据，使得不可变借用指向的数据变得无效。

**示例：不可变借用与可变借用冲突**

考虑以下代码片段：

```rust
fn main() {
    let mut v = vec![1, 2, 3]; // v 是可变的向量

    let p = &v[1]; // 获取 v 的第二个元素的不可变借用
    // 此时，v 上存在一个活跃的不可变借用 `p`

    v.push(4); // 尝试修改 v，这是一个可变操作
    // 这里会报错，因为在 `p` (不可变借用) 活跃期间，
    // `v.push(4)` 尝试获取 `v` 的可变借用。
    // `push` 操作可能会重新分配内存，从而使 `p` 指向的地址无效。

    println!("v[1]: {}", *p); // 尝试使用 `p`，但它可能已失效
}
```

编译这段代码会得到类似以下的错误：

```bash
4 |       let p = &v[1];
  |               - immutable borrow occurs here
5 |       v.push(4);
  |       ^^^^^^^^^ mutable borrow occurs here
6 |       println!("v[1]: {}", *p);
  |                               -- immutable borrow later used here
```

这个错误清楚地表明，Rust 的**借用检查器**通过检测**生命周期（Lifetime）**来判断行为的安全性。在 `p` 的生命周期内（从声明到最后一次使用 `println!`），`v.push(4)` 尝试对 `v` 进行可变借用，这违反了“不可变借用和可变借用不能同时存在”的规则。

---

### 所有权（Ownership）的核心概念

在 Rust 中，**所有权**是管理内存和资源的核心概念。它定义了变量如何与它们持有的数据进行交互。

- **独占性**：每个值都有一个被称为其“所有者”的变量。在任何给定时间，一个值只能有一个所有者。当所有者超出作用域时，值会被自动丢弃（drop），释放其占用的资源。
- **转移（Move）**：所有权可以在赋值、函数参数传递和函数返回值等操作中转移。一旦所有权转移，原始变量就不能再访问该数据。
- **借用（Borrowing）**：所有者可以将数据的访问权限“借给”其他代码，而无需转移所有权。这通过引用（`&` 和 `&mut`）实现，并受上述借用规则的约束。
- **每个线程都是一个 `agent`**：在并发环境中，可以把每个线程看作一个独立的“代理人”（agent）。每个代理人可能需要访问共享资源，但 Rust 的所有权和借用规则确保了即使在多线程环境下，对资源的访问也是安全的。

---

### 编译期检查与运行时检查：`RefCell` 的作用

Rust 的借用检查器在**编译期**执行严格的检查，这意味着很多潜在的并发问题和内存安全问题在代码运行之前就能被发现。然而，有时在编译期无法确定借用是否安全，因为安全性取决于运行时的某些条件。

**看一个关于实际上能运行但是编译期不通过的例子**

以下代码是一个经典例子，它在逻辑上是安全的（因为可变借用不会真正发生），但由于编译器的保守判断，它无法通过编译：

```rust
fn f1() -> bool { true }
fn f2() -> bool { !f1() } // f2 依赖 f1，所以 f2() 总是返回 !true，即 false

fn main() {
    let mut v1 = 42;
    let mut v2 = 666;

    // p1 根据 f1() 的结果借用 v1 或 v2
    let p1 = if f1() { &v1 } else { &v2 }; // f1() 为 true，所以 p1 借用 v1 的不可变引用

    // 这个 if 块的条件 f2() 为 false，所以里面的代码不会被执行
    if f2() {
        let p2 = &mut v1; // 如果此处执行，会尝试获取 v1 的可变借用
        *p2 = 37;
        println!("p2: {}", *p2);
    }

    println!("p1: {}", *p1);
}
```

尽管我们知道 `if f2()` 中的代码块永远不会执行，因此 `p1` (不可变借用 `v1`) 和 `p2` (可变借用 `v1`) 不会同时存在，但 Rust 编译器无法在编译时确定 `f2()` 的确切返回值（它只知道 `f2()` 是一个函数调用）。因此，编译器会保守地认为在 `p1` 的生命周期内（从声明到最后一次使用），`v1` 可能会被可变借用，从而导致编译错误：

```bash
6  |       let p1 = if f1() { &v1 } else { &v2 };
   |                       --- immutable borrow occurs here
7  |       if f2() {
8  |           let p2 = &mut v1;
   |                   ^^^^^^^ mutable borrow occurs here
...
13 |       println!("p1: {}", *p1);
   |                               --- immutable borrow later used here
```

**使用 `RefCell` 进行运行时借用检查**

为了解决这种编译期无法判断的运行时情况，Rust 提供了**内部可变性（Interior Mutability）**模式，其中 `std::cell::RefCell` 是一个关键类型。`RefCell` 允许你在运行时借用检查规则，而不是在编译时。

当使用 `RefCell` 时，借用规则的强制执行从编译时推迟到运行时。如果违反了规则（例如，同时存在多个可变借用或一个可变借用与不可变借用），`RefCell` 会在运行时 panic。

```rust
use std::cell::RefCell;

fn f1() -> bool { true }
fn f2() -> bool { !f1() }

fn main() {
    // 1. 初始化 RefCell 包装的整数
    let v1 = RefCell::new(42);  // v1 是一个包含 42 的 RefCell
    let v2 = RefCell::new(666); // v2 是一个包含 666 的 RefCell

    // 2. 获取 p1 的不可变借用
    // try_borrow() 在运行时获取 RefCell 的不可变引用。
    // 如果此时有活跃的可变借用，它会返回 Err，unwrap() 会导致 panic。
    // 但在这个例子中，v1 还没有任何借用，所以会成功。
    let p1 = (if f1() { &v1 } else { &v2 }) // f1() 为 true，所以选择 &v1
        .try_borrow().unwrap(); // 对 v1 调用 try_borrow()，成功获取不可变引用，p1 此时指向 v1 内部的 42

    // 此时，v1 内部有一个活跃的不可变借用计数。

    // 3. 条件判断块
    if f2() { // f2() 返回 false，所以这个 if 块的代码不会执行。
        // 这意味着以下对 v1 的可变借用尝试和修改操作都不会发生。
        let mut p2 = v1 // 如果此处执行，会尝试对 v1
            .try_borrow_mut().unwrap(); // 获取可变借用。
                                       // 此时 v1 已经有一个不可变借用 (p1)，
                                       // 如果这条路径执行，这里会发生运行时 panic，因为 RefCell 不允许同时有不可变借用和可变借用。
        *p2 = 37; // (如果执行) 改变 v1 的内部值
        println!("p2: {}", *p2); // (如果执行) 打印改变后的值
    }

    // 4. 打印 p1 所引用的值
    println!("p1: {}", *p1);
    // 因为 if f2() 块没有执行，v1 内部的值没有被改变。
    // p1 仍然引用着 v1 最初的 42。
    // 所以，这里会打印 "p1: 42"。
}
```

通过 `RefCell`，我们成功地将借用检查从编译期推迟到运行时，从而允许这种在逻辑上安全但在编译时无法验证的代码通过编译。

---

### 锁（Locks）在 Rust 中的实现与并发

在并发编程中，锁（如互斥锁 `Mutex`）是同步原语，用于控制对共享资源的访问，防止多个线程同时修改数据导致数据损坏或不一致。

Rust 标准库提供了 `std::sync::Mutex` 来实现互斥锁。当一个线程需要访问受保护的数据时，它必须先获取锁。一旦获取到锁，它就可以独占访问数据。完成操作后，它必须释放锁，以便其他线程可以获取它。

**锁的自动释放：`LockGuard` 和 `Drop` trait**

Rust 的 `Mutex` 通过返回一个称为 `MutexGuard` (在你的笔记中称为 `LockGuard`) 的智能指针来实现 RAII（Resource Acquisition Is Initialization）模式。当 `MutexGuard` 超出作用域时，它的 `Drop` 实现会被调用，自动释放底层的锁。

```rust
impl<L: RawLock, T> Drop for LockGuard<'_, L, T> {
    fn drop(&mut self) {
        // 在 LockGuard 被销毁时，自动调用底层锁的 `unlock` 方法
        // `unsafe` 块表示这里执行了可能不安全的操作，需要确保其正确性
        unsafe { self.lock.inner.unlock(token) }
    }
}
```

这意味着你通常不需要手动释放锁，因为 Rust 会为你处理。

**锁使用示例与注意事项**

下面是一个使用锁的简化流程和常见的错误：

```rust
// data: Mutex<i32>，其中 Mutex 保护一个 i32 类型的数据
let data_mutex = Mutex::new(0); // 假设 data_mutex 是一个 Mutex 实例

// 1. 获取锁，得到一个 MutexGuard
let data_guard = data_mutex.lock().unwrap(); // lock() 方法会阻塞直到获取到锁

// 2. 通过 MutexGuard 访问受保护的数据
// data_guard 实现了 Deref 和 DerefMut trait，所以可以直接像操作原始数据一样操作它
let data_ref = &*data_guard; // 这是一个对 MutexGuard 内部数据的不可变引用
// 或者直接修改：*data_guard = 10;

// ... 在这里执行对数据的操作 ...

// 3. MutexGuard 超出作用域，锁被自动释放
// drop(data_guard); // 手动调用 drop，或者等待 data_guard 超出作用域

// 4. 常见错误：在锁释放后尝试访问数据
// *data_ref = 666; // 编译错误！因为 data_guard 已经失效，data_ref 也不再有效
```

在 `drop(data_guard);` 或 `data_guard` 超出作用域后，锁就会被释放。此时，任何通过 `data_guard` 派生出来的引用（如 `data_ref`）都将失效。如果尝试在锁释放后通过这些失效的引用访问数据，Rust 的借用检查器会捕获这个错误，因为它发现 `data_ref` 在其借用的生命周期结束后被使用（`immutable borrow later used here`），从而防止**用后释放（use-after-free）**的错误。

**总结**

Rust 通过所有权、借用和生命周期的严格编译时检查，以及像 `RefCell` 这样的运行时检查机制，提供了强大的内存安全和并发安全保证。理解这些核心概念对于编写高效且无数据竞争的 Rust 并发代码至关重要。
