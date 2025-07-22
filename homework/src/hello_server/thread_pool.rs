//! Thread pool that joins all thread when dropped.

// NOTE: Crossbeam channels are MPMC, which means that you don't need to wrap the receiver in
// Arc<Mutex<..>>. Just clone the receiver and give it to each worker thread.
use std::sync::{Arc, Condvar, Mutex};
use std::thread;

use crossbeam_channel::{Sender, unbounded};

struct Job(Box<dyn FnOnce() + Send + 'static>);

#[derive(Debug)]
struct Worker {
    _id: usize,
    thread: Option<thread::JoinHandle<()>>,
}
impl Worker {
    fn new(
        _id: usize,
        receiver: crossbeam_channel::Receiver<Job>,
        pool_inner: Arc<ThreadPoolInner>
    ) -> Self {
        let thread = thread::spawn(move || {
            loop {
                // 线程会在这里“暂停”执行
                match receiver.recv() {
                    Ok(job) => {
                        (job.0)();
                        pool_inner.finish_job();
                    }
                    Err(_) => {
                        break;
                    }
                }
            }
        });
        Worker {
            _id,
            thread: Some(thread),
        }
    }
}
impl Drop for Worker {
    /// When dropped, the thread's `JoinHandle` must be `join`ed.  If the worker panics, then this
    /// function should panic too.
    ///
    /// NOTE: The thread is detached if not `join`ed explicitly.
    fn drop(&mut self) {
        // 取出JoinHandle避免所有权问题
            // 阻塞等待线程结束, 若线程panic则传播panic
        if let Some(thread ) = self.thread.take(){
            let error_message = format!("Worker{} thread panicked during shutdown", self._id);
            thread.join().expect(&error_message);
        }
    }
}

/// Internal data structure for tracking the current job status. This is shared by worker closures
/// via `Arc` so that the workers can report to the pool that it started/finished a job.
#[derive(Debug, Default)]
struct ThreadPoolInner {
    job_count: Mutex<usize>,
    empty_condvar: Condvar,
}

impl ThreadPoolInner {
    /// Increment the job count.
    fn start_job(&self) {
        //todo!()
        let mut job_count = self.job_count.lock().unwrap();
        *job_count += 1;
    }

    /// Decrement the job count.
    fn finish_job(&self) {
        //todo!()
        let mut job_count = self.job_count.lock().unwrap();
        *job_count -= 1;
        // 任务计数为0后 唤醒所有的线程
        if *job_count == 0 {
            self.empty_condvar.notify_all();
        }
    }

    /// Wait until the job count becomes 0.
    ///
    /// NOTE: We can optimize this function by adding another field to `ThreadPoolInner`, but let's
    /// not care about that in this homework.
    fn wait_empty(&self) {
        //todo!()
        let mut job_count = self.job_count.lock().unwrap();
        while *job_count > 0 {
            // 当前任务未执行完成 会对调用wait_empty的线程进行睡眠
            // 释放上面获得的mutex锁 直到收到finish_job的notify_all的通知
            job_count = self.empty_condvar.wait(job_count).unwrap();
        }
    }
}

/// Thread pool.
#[derive(Debug)]
pub struct ThreadPool {
    _workers: Vec<Worker>,
    job_sender: Option<Sender<Job>>,
    pool_inner: Arc<ThreadPoolInner>,
}

impl ThreadPool {
    /// Create a new ThreadPool with `size` threads.
    ///
    /// # Panics
    ///
    /// Panics if `size` is 0.
    pub fn new(size: usize) -> Self {
    assert!(size > 0);
    //todo!()
    let (sender, receiver) = crossbeam_channel::unbounded();

    let pool_inner = Arc::new(ThreadPoolInner::default());
    let mut workers = Vec::with_capacity(size);

    for id in 0..size {
        let receiver_clone = receiver.clone();
        let pool_inner_clone = pool_inner.clone();
        workers.push(Worker::new(id, receiver_clone, pool_inner_clone));
    }
    ThreadPool {
        _workers: workers,
        job_sender: Some(sender),
        pool_inner,
    }
}

    /// Execute a new job in the thread pool.
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        //todo!()
        self.pool_inner.start_job();
        let job = Job(Box::new(f));

        self.job_sender
        .as_ref()
        .expect("ThreadPool is shutting down, cannot execute new jobs.")
        .send(job)
        .expect(
            "Failed to send job to worker thread. Receiver might have been dropped unexpectedly."
        );
        
    }

    /// Block the current thread until all jobs in the pool have been executed.
    ///
    /// NOTE: This method has nothing to do with `JoinHandle::join`.
    pub fn join(&self) {
        //todo!()
        self.pool_inner.wait_empty();
    }    
}

impl Drop for ThreadPool {
    /// When dropped, all worker threads' `JoinHandle` must be `join`ed. If the thread panicked,
    /// then this function should panic too.
    fn drop(&mut self) {
        // 关闭任务通道,停止接收新任务
        self.job_sender.take();
        
        // 工作线程将在执行完当前任务后退出
        // Worker的Drop实现会确保join线程
    }
}
