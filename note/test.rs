use std::sync::Arc;
use std::rc::Rc;
use std::thread;
use std::time::Duration;
fn main() {
    let five = Arc::new(5);
    println!("初始引用计数: {}", Arc::strong_count(&five)); //
    for i in 0..10 {
        let five_clone = five.clone();
        println!("克隆 {} 次后引用计数: {}", i + 1, Arc::strong_count(&five));
        thread::spawn(move || {
            //println!("{five_clone}");
            println!(
                "线程 {} 内部 five_clone 的值: {}, 引用计数: {}",
                i,
                *five_clone,
                Arc::strong_count(&five_clone)
            );
        });
        //println!("克隆 {} 次后引用计数: {}", i + 1, Arc::strong_count(&five));
    }
    thread::sleep(Duration::new(1, 0));
    println!("主线程休眠后引用计数: {}", Arc::strong_count(&five)); // 输出可能会接近
}
