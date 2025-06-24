// =========================
//   P-RAF: Rust Benchmark Worker (Queue/Concurrent Version)
// =========================

use rand::Rng;
use serde_json::json;
use std::io::{BufWriter, Write};
use std::net::TcpStream;
use std::thread;
use std::time::Duration;

use crossbeam::channel::{bounded, Receiver, Sender};

const ORCHESTRATOR_HOST: &str = "127.0.0.1";
const ORCHESTRATOR_PORT: u16 = 9000;
const LANGUAGE_NAME: &str = "Rust";
const ALGORITHMS: [&str; 6] = [
    "array_sort",
    "fibonacci",
    "game_of_life",
    "matrix_multiplication",
    "prime_factors",
    "is_leap_year",
];

// Result struct to pass through channel
struct ResultMsg {
    algo: &'static str,
    duration: f64,
}

fn main() {
    println!("✅ Starting P-RAF Rust worker (queue version)...");
    // Bounded channel, prevents unbounded memory growth
    let (tx, rx): (Sender<ResultMsg>, Receiver<ResultMsg>) = bounded(1000);

    let algo_fns: [fn(); 6] = [
        array_sort,
        fibonacci,
        game_of_life,
        matrix_multiplication,
        prime_factors,
        is_leap_year,
    ];

    // Spawn all worker threads
    for (i, &name) in ALGORITHMS.iter().enumerate() {
        let tx = tx.clone();
        let algo = algo_fns[i];
        thread::spawn(move || algo_worker(name, algo, tx));
    }

    // Only one sender thread!
    sender_loop(rx);
}

// Each algo thread: run forever, push result to queue
fn algo_worker(name: &'static str, algo: fn(), tx: Sender<ResultMsg>) {
    loop {
        let start = std::time::Instant::now();
        algo();
        let duration = start.elapsed().as_secs_f64();
        // If send fails, the main thread must have exited—just exit
        if tx
            .send(ResultMsg {
                algo: name,
                duration,
            })
            .is_err()
        {
            break;
        }
    }
}

// Sender thread: single connection, send results from queue, reconnect on fail
fn sender_loop(rx: Receiver<ResultMsg>) {
    loop {
        match TcpStream::connect((ORCHESTRATOR_HOST, ORCHESTRATOR_PORT)) {
            Ok(stream) => {
                println!("✅ Sender connected to orchestrator.");
                let mut writer = BufWriter::new(stream);

                loop {
                    match rx.recv() {
                        Ok(res) => {
                            let payload = json!({
                                "lang": LANGUAGE_NAME,
                                "algo": res.algo,
                                "duration": res.duration
                            })
                            .to_string();

                            if let Err(e) = writeln!(writer, "{}", payload) {
                                eprintln!("⚠️  Sender write failed: {}. Reconnecting...", e);
                                break;
                            }
                            let _ = writer.flush();
                        }
                        Err(_) => break, // channel closed, exit
                    }
                }
            }
            Err(e) => {
                eprintln!("⚠️  Sender could not connect: {}. Retrying in 2s...", e);
                thread::sleep(Duration::from_secs(2));
            }
        }
    }
}

// --- Algorithms ---
fn array_sort() {
    let mut rng = rand::thread_rng();
    let mut a: Vec<i32> = (0..40).map(|_| rng.gen_range(0..100)).collect();
    a.sort_unstable();
}
fn fibonacci() {
    let mut rng = rand::thread_rng();
    let mut a = 0u64;
    let mut b = 1u64;
    for _ in 0..rng.gen_range(20..=35) {
        let t = a;
        a = b;
        b = t + b;
    }
}
fn game_of_life() {
    let mut rng = rand::thread_rng();
    let w = 35;
    let h = 35;
    let g = 5;
    let mut grid: Vec<Vec<u8>> = (0..w)
        .map(|_| (0..h).map(|_| rng.gen_range(0..=1)).collect())
        .collect();
    for _ in 0..g {
        let mut next = vec![vec![0; h]; w];
        for x in 0..w {
            for y in 0..h {
                let mut ln = 0;
                for i in -1..=1 {
                    for j in -1..=1 {
                        if i == 0 && j == 0 {
                            continue;
                        }
                        let xi = ((x as isize + i + w as isize) % w as isize) as usize;
                        let yj = ((y as isize + j + h as isize) % h as isize) as usize;
                        ln += grid[xi][yj] as usize;
                    }
                }
                let il = grid[x][y] == 1;
                next[x][y] = if (il && (ln == 2 || ln == 3)) || (!il && ln == 3) {
                    1
                } else {
                    0
                };
            }
        }
        grid = next;
    }
}
fn matrix_multiplication() {
    let mut rng = rand::thread_rng();
    let d = 50;
    let a: Vec<Vec<i32>> = (0..d)
        .map(|_| (0..d).map(|_| rng.gen_range(0..10)).collect())
        .collect();
    let b: Vec<Vec<i32>> = (0..d)
        .map(|_| (0..d).map(|_| rng.gen_range(0..10)).collect())
        .collect();
    let mut res = vec![vec![0; d]; d];
    for i in 0..d {
        for j in 0..d {
            for k in 0..d {
                res[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}
fn prime_factors() {
    let mut rng = rand::thread_rng();
    let mut n = rng.gen_range(100_000..=500_000);
    let mut d = 2;
    let mut fac = Vec::new();
    while d * d <= n {
        if n % d == 0 {
            fac.push(d);
            n /= d;
        } else {
            d += 1;
        }
    }
    if n > 1 {
        fac.push(n);
    }
}
fn is_leap_year() {
    let mut rng = rand::thread_rng();
    let y = rng.gen_range(1..=9999);
    let _ = (y % 4 == 0) && ((y % 100 != 0) || (y % 400 == 0));
}
