## 代码翻译

### `cache.rs`

```rust
//! 线程安全的键/值缓存.

use std::collections::hash_map::{Entry, HashMap};
use std::hash::Hash;
use std::sync::{Arc, Mutex, RwLock}; // 注意:RwLock 在当前的实现中没有被使用,但在解决问题时可能会用到

/// 记住每个键的结果的缓存.
#[derive(Debug)]
pub struct Cache<K, V> {
    // todo! 这是一个示例缓存类型.你需要构建自己的缓存类型,以满足 `get_or_insert_with` 的规范.
    inner: Mutex<HashMap<K, V>>, // 内部使用一个由 Mutex 保护的 HashMap
}

impl<K, V> Default for Cache<K, V> {
    fn default() -> Self {
        Self {
            inner: Mutex::new(HashMap::new()),
        }
    }
}

impl<K: Eq + Hash + Clone, V: Clone> Cache<K, V> {
    /// 获取值,如果不存在则使用 `f` 创建并插入新值.
    ///
    /// 对此函数的调用不应阻塞对不同键的另一个调用.例如,如果一个线程并发调用
    /// `get_or_insert_with(key1, f1)`,而另一个线程并发调用 `get_or_insert_with(key2, f2)`
    /// (`key1≠key2`,`key1,key2` 都不在缓存中),那么 `f1` 和 `f2` 应该并发运行.
    ///
    /// 另一方面,由于 `f` 可能会消耗大量资源(例如:网络请求、复杂计算),因此不希望重复工作.
    /// 也就是说,对于每个键,`f` 应该只运行一次.具体来说,即使并发调用
    /// `get_or_insert_with(key, f)`,对于每个键,`f` 也只会被调用一次.
    ///
    /// 提示:[`Entry`] API 可能有助于实现此函数.
    ///
    /// [`Entry`]: https://doc.rust-lang.org/stable/std/collections/hash_map/struct.HashMap.html#method.entry
    pub fn get_or_insert_with<F: FnOnce(K) -> V>(&self, key: K, f: F) -> V {
        todo!()
    }
}
```

### `tcp.rs`

```rust
//! 可取消的 TcpListener.

use std::io; // 引入标准输入输出库,用于处理错误
use std::net::{TcpListener, TcpStream, ToSocketAddrs}; // 引入 TCP 监听器、TCP 流和地址转换
use std::sync::atomic::{AtomicBool, Ordering}; // 引入原子布尔类型和内存排序,用于线程间安全通信

/// 类似于 `std::net::tcp::TcpListener`,但可以被 `cancel`(取消).
#[derive(Debug)] // 允许使用 {:?} 格式化输出,方便调试
pub struct CancellableTcpListener {
    inner: TcpListener, // 内部封装了一个标准的 TcpListener

    /// 一个原子布尔标志,指示监听器是否已被 `cancel`(取消).
    ///
    /// 注意:这可以被多个线程同时安全地读取/写入(注意其方法接受 `&self` 而不是 `&mut self`).
    /// 要设置此标志,请使用 `store` 方法并指定 `Ordering::Release`.
    /// 要读取此标志,请使用 `load` 方法并指定 `Ordering::Acquire`.我们稍后将讨论它们的精确语义.
    is_canceled: AtomicBool,
}

/// 类似于 `std::net::tcp::Incoming`,但如果监听器被 `cancel`(取消),则停止 `accept`(接受)连接.
#[derive(Debug)]
pub struct Incoming<'a> {
    listener: &'a CancellableTcpListener, // 引用关联的 CancellableTcpListener
}

impl CancellableTcpListener {
    /// 封装了 `TcpListener::bind` 方法.
    pub fn bind<A: ToSocketAddrs>(addr: A) -> io::Result<CancellableTcpListener> {
        let listener = TcpListener::bind(addr)?; // 绑定到指定地址
        Ok(CancellableTcpListener {
            inner: listener,
            is_canceled: AtomicBool::new(false), // 初始化取消标志为 false
        })
    }

    /// 发出信号,通知监听器停止接受新的连接.
    pub fn cancel(&self) -> io::Result<()> {
        // 首先设置标志,然后向监听器自身建立一个“虚假”连接,以唤醒在 `accept` 中阻塞的监听器.
        // 使用 `TcpListener::local_addr` 获取本地地址,并使用 `TcpStream::connect` 建立连接.
        todo!() // 待办事项:需要实现这部分逻辑
    }

    /// 返回一个迭代器,用于遍历此监听器上接收到的连接.
    /// 如果监听器已被 `cancel`(取消),返回的迭代器将返回 `None`.
    pub fn incoming(&self) -> Incoming<'_> {
        Incoming { listener: self }
    }
}

impl Iterator for Incoming<'_> {
    type Item = io::Result<TcpStream>; // 迭代器返回的项是结果类型,包含 TcpStream 或错误
    /// 如果监听器被 `cancel()`(取消),则返回 `None`.
    fn next(&mut self) -> Option<Self::Item> {
        let stream = self.listener.inner.accept().map(|p| p.0); // 尝试接受一个连接,并只保留 TcpStream
        todo!() // 待办事项:需要实现这部分逻辑,检查取消状态并决定返回 None 还是实际连接
    }
}
```

### `thread_pool.rs`

```rust
//! 线程池,在被丢弃时会等待(join)所有线程完成.

// 注意:Crossbeam 通道是 MPMC (多生产者,多消费者),这意味着你不需要将接收端(receiver)封装在
// Arc<Mutex<..>> 中.只需克隆接收端并将其分发给每个工作线程即可.
use std::sync::{Arc, Condvar, Mutex}; // 引入 Arc(原子引用计数)、Condvar(条件变量)、Mutex(互斥锁)
use std::thread; // 引入线程模块

use crossbeam_channel::{Sender, unbounded}; // 引入 Crossbeam 的发送端和无界通道

// Job 结构体:表示一个待执行的任务.
struct Job(Box<dyn FnOnce() + Send + 'static>); // 一个封装了闭包的结构体,该闭包只执行一次,可跨线程发送,且生命周期是 'static

#[derive(Debug)]
struct Worker {
    _id: usize, // 工作线程的 ID
    thread: Option<thread::JoinHandle<()>>, // 线程的 JoinHandle,用于在 Worker 被丢弃时等待线程结束
}

impl Drop for Worker {
    /// 当 Worker 被丢弃时,其内部线程的 `JoinHandle` 必须被 `join`.
    /// 如果工作线程发生了 panic,那么此函数也应该 panic.
    ///
    /// 注意:如果线程没有被显式地 `join`,它将变为分离状态(detached).
    fn drop(&mut self) {
        todo!() // 待办事项:实现当 Worker 被丢弃时,等待其关联线程完成
    }
}

/// 用于跟踪当前任务状态的内部数据结构.通过 `Arc` 在工作线程闭包之间共享,
/// 以便工作线程可以向线程池报告任务的开始/完成情况.
#[derive(Debug, Default)]
struct ThreadPoolInner {
    job_count: Mutex<usize>, // 当前正在执行的任务数量,由 Mutex 保护
    empty_condvar: Condvar,  // 条件变量,用于在任务数量变为 0 时通知等待者
}

impl ThreadPoolInner {
    /// 增加任务计数.
    fn start_job(&self) {
        todo!() // 待办事项:实现增加 job_count
    }

    /// 减少任务计数.
    fn finish_job(&self) {
        todo!() // 待办事项:实现减少 job_count,并在 job_count 变为 0 时通知等待者
    }

    /// 等待直到任务计数变为 0.
    ///
    /// 注意:我们可以通过向 `ThreadPoolInner` 添加另一个字段来优化此函数,但在此次作业中无需考虑.
    fn wait_empty(&self) {
        todo!() // 待办事项:实现等待直到 job_count 变为 0
    }
}

/// 线程池.
#[derive(Debug)]
pub struct ThreadPool {
    _workers: Vec<Worker>, // 线程池中的所有工作线程
    job_sender: Option<Sender<Job>>, // 向工作线程发送任务的发送端.使用 Option 是为了在 Drop 时可以取出并关闭通道.
    pool_inner: Arc<ThreadPoolInner>, // 共享的内部数据,用于跟踪任务状态
}

impl ThreadPool {
    /// 创建一个包含 `size` 个线程的新线程池.
    ///
    /// # Panics
    ///
    /// 如果 `size` 为 0,则此函数会 panic.
    pub fn new(size: usize) -> Self {
        assert!(size > 0); // 确保线程池大小大于 0

        todo!() // 待办事项:实现线程池的创建逻辑
    }

    /// 在线程池中执行一个新任务.
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static, // 任务闭包必须满足这些约束
    {
        todo!() // 待办事项:实现任务的发送
    }

    /// 阻塞当前线程,直到池中所有任务都被执行完毕.
    ///
    /// 注意:此方法与 `JoinHandle::join` 无关.
    pub fn join(&self) {
        todo!() // 待办事项:实现等待所有任务完成的逻辑
    }
}

impl Drop for ThreadPool {
    /// 当 ThreadPool 被丢弃时,所有工作线程的 `JoinHandle` 必须被 `join`.
    /// 如果工作线程发生了 panic,那么此函数也应该 panic.
    fn drop(&mut self) {
        todo!() // 待办事项:实现当 ThreadPool 被丢弃时,优雅地关闭线程池并等待所有工作线程完成
    }
}
```

### `hello_server.rs`

```rust
use std::io; // 引入标准 I/O 模块,用于处理输入输出和错误
use std::sync::Arc; // 引入 Arc(原子引用计数),用于在多线程间共享所有权
use std::sync::mpsc::{channel, sync_channel}; // 引入 mpsc 通道(多生产者单消费者)和同步通道

// 从 cs431_homework 库中引入自定义的模块和结构体
use cs431_homework::hello_server::{CancellableTcpListener, Handler, Statistics, ThreadPool};

const ADDR: &str = "localhost:7878"; // 定义服务器监听的地址和端口

fn main() -> io::Result<()> {
    // 提示用户如何与服务器交互
    // 鼓励使用 Firefox 或 curl 进行测试,并提到可能需要更改端口以在实验室服务器上运行.
    println!("运行 `curl http://{ADDR}/KEY` 来用 KEY 查询服务器");

    // 线程池.
    //
    // 在这个线程池中,我们将执行:
    //
    // - 一个监听器:它接受传入连接,并为每个连接创建一个新的工作者.
    //
    // - 工作者(每个传入连接一个):一个工作者处理一个传入连接,并向报告者发送相应的报告.
    //
    // - 一个报告者:它聚合来自工作者的报告并处理统计信息.当它结束时,它将统计信息发送给主线程.
    // 创建一个包含 7 个线程的线程池,并用 Arc 包装使其可以在多线程间共享
    let pool = Arc::new(ThreadPool::new(7));

    // 工作者和报告者之间的报告通道(多生产者,单消费者 MPSC).
    // 用于工作者向报告者发送连接处理结果(报告).
    let (report_sender, report_receiver) = channel(); // channel() 创建一个无界 MPSC 通道

    // 报告者和主线程之间的统计信息通道(单生产者,单消费者 SPSC,同步).
    // 用于报告者向主线程发送最终的统计结果. sync_channel(0) 创建一个容量为 0 的通道,
    // 意味着发送方在接收方准备好接收之前会一直阻塞(同步行为).
    let (stat_sender, stat_receiver) = sync_channel(0);

    // 监听指定地址.
    // 创建一个可取消的 TCP 监听器,并用 Arc 包装以便多线程访问(特别是用于 Ctrl-C 处理).
    let listener = Arc::new(CancellableTcpListener::bind(ADDR)?);

    // 安装 Ctrl-C 处理器.
    // 克隆 listener 的 Arc 引用,以便 Ctrl-C 处理器可以访问它.
    let ctrlc_listener_handle = listener.clone();
    // 设置 Ctrl-C 信号处理函数
    ctrlc::set_handler(move || {
        // 当收到 Ctrl-C 信号时,调用监听器的 cancel 方法来停止接受新连接.
        ctrlc_listener_handle.cancel().unwrap();
    })
    .expect("设置 Ctrl-C 处理器时出错"); // 如果设置失败则 panic

    // 执行监听器任务.
    // 克隆线程池的 Arc 引用,以便监听器任务可以使用它来提交新的工作者任务.
    let listener_pool = pool.clone();
    // 将监听器任务提交到线程池执行
    pool.execute(move || {
        // 创建请求处理器实例,用于处理每个传入连接.
        let handler = Handler::default();

        // 遍历监听器传入的连接
        // `listener.incoming()` 返回一个迭代器,每次循环获取一个新连接.
        for (id, stream) in listener.incoming().enumerate() {
            // 为每个传入连接向线程池发送一个任务.
            let report_sender = report_sender.clone(); // 克隆报告发送端,因为每个工作者都需要发送报告
            let handler = handler.clone(); // 克隆处理器,因为每个工作者都需要它来处理连接
            // 将处理单个连接的任务提交到线程池
            listener_pool.execute(move || {
                // 处理连接并获取报告
                let report = handler.handle_conn(id, stream.unwrap());
                // 将报告发送给报告者
                report_sender.send(report).unwrap();
            });
        }
    });

    // 执行报告者任务.
    // 将报告者任务提交到线程池执行
    pool.execute(move || {
        let mut stats = Statistics::default(); // 创建一个默认的统计信息实例
        // 从报告通道接收所有报告,直到通道关闭
        for report in report_receiver {
            println!("[报告] {report:?}"); // 打印接收到的每个报告
            stats.add_report(report); // 将报告添加到统计信息中
        }

        println!("[发送统计数据]");
        stat_sender.send(stats).unwrap(); // 当所有报告处理完毕(通道关闭)后,将最终统计信息发送给主线程
        println!("[已发送统计数据]");
    });

    // 阻塞当前主线程,直到报告者发送统计信息.
    let stat = stat_receiver.recv().unwrap(); // 主线程阻塞在这里,等待从统计信息通道接收最终统计数据
    println!("[统计数据] {stat:?}"); // 打印最终的统计数据

    Ok(()) // 返回成功结果
    // 当 `pool`(线程池)变量超出作用域被丢弃时,其 `Drop` 实现会被调用,
    // 这将确保所有工作线程都正确地被 `join`,即等待它们完成.
}
```
