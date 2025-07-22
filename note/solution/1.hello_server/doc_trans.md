# 带缓存的并行 Web 服务器

## 预期结果

- 执行 .`cargo run --features="build-bin" hello_server`. 一个 Web 服务器应当会运行. 如果无法运行,请尝试更改在 [`hello_server.rs:6`](../src/bin/hello_server.rs).中使用的端口.
- 运行`curl http://localhost:7878/alice` . 它应该会等待几秒钟,然后返回一个网页.
- 再次运行`curl http://localhost:7878/alice` . 它应该会立即返回一个网页.
- 运行`curl http://localhost:7878/bob` . 它应该会等待几秒钟,然后返回一个网页.
- 按下`Ctrl-C` . Web 服务器应该在打印统计信息后平滑地关闭.

## 组织结构

- `../src/bin/hello_server.rs`:Web 服务器本身.
- `../src/hello_server/*.rs`:服务器的组件. 你需要填充这些文件中的`todo!()` .

## 评分

评分程序会在 `homework`目录下运行 . 该脚本会使用不同的选项来运行测试.`./scripts/grade-hello_server.sh `

对于 ` tcp`和 `thread_pool `模块,将**没有部分分**. 也就是说,只有当你的实现通过了某个模块的**所有**测试时,你才能获得该模块的分数.

另一方面,对于 模块`cache `,我们会给予部分分. 具体来说,即使你的`cache` 实现阻塞了对不同键的并发访问,只要基础功能正确,你仍然可以获得一些分数.

## 提交

```bash
cd cs431/homework
./scripts/submit.sh
ls ./target/hw-hello_server.zip
```

将 提交到 gg.`hw-hello_server.zip`

## 指南

### 阅读 Rust 官方文档

本次作业要求你对 [Rust 官方文档第 20 章](https://doc.rust-lang.org/book/ch20-00-final-project-a-web-server.html) 中涵盖的内容有很好的理解. 这是理解第 20 章的最小学习路径:第 1, 2, 3, 4, 5, 6, 8, 9, 10, 13.1, 13.2, **15**, **16**, **20** 章.

请务必确保你理解以下主题:

- [`Drop`](<https://www.google.com/search?q=[https://doc.rust-lang.org/std/ops/trait.Drop.html](https://doc.rust-lang.org/std/ops/trait.Drop.html)>) trait 和 [`drop`](<https://www.google.com/search?q=[https://doc.rust-lang.org/std/mem/fn.drop.html](https://doc.rust-lang.org/std/mem/fn.drop.html)>) 函数.
- [`std::thread::spawn`](<https://www.google.com/search?q=[https://doc.rust-lang.org/std/thread/fn.spawn.html](https://doc.rust-lang.org/std/thread/fn.spawn.html)>) 的类型签名以及 [`std::thread::JoinHandle`](<https://www.google.com/search?q=[https://doc.rust-lang.org/std/thread/struct.JoinHandle.html](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html)>) 的含义.
- [`Arc<`](<https://www.google.com/search?q=[https://doc.rust-lang.org/std/sync/struct.Arc.html](https://doc.rust-lang.org/std/sync/struct.Arc.html)>)[`Mutex>`](<https://www.google.com/search?q=[https://doc.rust-lang.org/std/sync/struct.Mutex.html](https://doc.rust-lang.org/std/sync/struct.Mutex.html)>) 的含义和用法.
- [Channels](https://doc.rust-lang.org/std/sync/mpsc/index.html) (信道). 另请参阅:带测验的 Rust 官方文档 https://rust-book.cs.brown.edu/

### 本次作业的线程池与 Rust 官方文档第 20 章线程池的主要区别

1. 我们使用 [`crossbeam_channel`](<https://www.google.com/search?q=[https://docs.rs/crossbeam-channel/](https://docs.rs/crossbeam-channel/)>) 而不是 [`std::sync::**mpsc**`](https://doc.rust-lang.org/std/sync/mpsc/index.html). 由于 crossbeam 的 channel 是**多生产者多消费者 (mpmc)** 的,你不需要将 包装在 中.` Receiver``Mutex `

2. 我们不为线程池使用显式的退出消息. 相反,我们通过 发送端/接收端来断开 channel.`drop`

   - 我们的消息类型就是 本身:`Job`

     ```rust
     struct Job(Box<dyn FnOnce() + Send + 'static>);
     ```

   - 如果 channel 断开连接,每个工作线程都会自动跳出循环.

3. 我们在 的析构函数中 每个线程,而不是在 的析构函数中. 因为 有一个字段 ,所以当线程池被 drop 时,worker 的析构函数就会被调用. 注意,channel 应该在 工作线程之前断开连接. (否则, 会阻塞. )这意味着 应该在 之前被 drop. 你可以通过多种方式来指定 drop 的顺序. 在本次作业中,我们使用类型为 的 ,其内容可以在 中被显式地 并 .` Worker``join()``ThreadPool``ThreadPool``workers: Vec<Worker>``join()``join``Sender``Vec<Worker>``Option<Sender<Job>>``ThreadPool::job_sender``<ThreadPool as Drop>::drop``take()``drop() `

### 提示

- **Cache (缓存)**: 从 开始. 为了完全实现规格要求,你需要一个更复杂的类型. 最简单的解决方案会用到 中导入的所有东西.` Mutex<HashMap<K, V>>``cache.rs `
- **Interrupt handler (中断处理器)**: 只需按照注释作即可.
- **Thread pool (线程池)**: 先忽略 (它用于 ),并实现上面讨论的变更.` ThreadPoolInner``ThreadPool::join `
- 如果你有任何问题,请尝试查看 [issue tracker](https://github.com/kaist-cp/cs431/issues). 这里有很多来自往届课程的问答,并且都按主题进行了标记. 例如,[“homework - cache” 标签](https://www.google.com/search?q=https://github.com/kaist-cp/cs431/issues%3Fq%3Dlabel%3A%22homework%2B-%2Bcache%22%2B)列出了关于 的问题. 以下是一些你可能会觉得有用的问答:`cache.rs`
  - https://github.com/kaist-cp/cs431/issues/339
  - https://github.com/kaist-cp/cs431/issues/85#issuecomment-696888546
  - https://github.com/kaist-cp/cs431/issues/81

### 测试

我们只会测试库本身.

```rust
cargo test --test cache
cargo test --test tcp
cargo test --test thread_pool
```

我们也会使用这些测试来进行评分. 我们可能会为评分增加一些额外的测试,但如果你的解决方案能通过所有给定的测试,你很可能会获得满分.

另外,请尝试在启用 [LLVM sanitizers](https://github.com/kaist-cp/cs431/tree/main/homework#using-llvm-sanitizers) 的情况下运行测试. 它们对本次作业不是那么有用,但对未来的作业会非常有帮助.
