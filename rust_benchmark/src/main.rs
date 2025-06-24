use mimalloc::MiMalloc;
use ndarray::Array2;
use rand::{rngs::StdRng, Rng, SeedableRng};
use serde::Serialize;
use std::collections::BTreeMap;
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

const RUST_STATS_FILE: &str = "rust_stats.yaml";
const ALGORITHMS: &[(&str, fn(&mut StdRng))] = &[
    ("array_sort", array_sort),
    ("fibonacci", fibonacci),
    ("game_of_life", game_of_life),
    ("matrix_multiplication", matrix_multiplication),
    ("prime_factors", prime_factors),
    ("is_leap_year", is_leap_year),
];

#[derive(Debug, Serialize, Clone, Default)]
struct AlgorithmStats {
    runs: u64,
    total_time: f64,
    min_time: f64,
    max_time: f64,
}

type SharedStats = Arc<Mutex<BTreeMap<&'static str, AlgorithmStats>>>;

fn main() {
    println!("Starting Rust workers...");
    let stats: SharedStats = Arc::new(Mutex::new(BTreeMap::new()));
    let mut handles = Vec::with_capacity(ALGORITHMS.len() + 1);

    for &(name, algorithm_fn) in ALGORITHMS {
        let stats_clone = Arc::clone(&stats);
        handles.push(thread::spawn(move || {
            worker(name, algorithm_fn, stats_clone)
        }));
    }

    let stats_clone = Arc::clone(&stats);
    handles.push(thread::spawn(move || yaml_writer(stats_clone)));

    for handle in handles {
        handle.join().unwrap();
    }
}

fn worker(name: &'static str, algorithm: fn(&mut StdRng), stats: SharedStats) {
    let mut rng = StdRng::from_entropy();
    // The unused sleep_rng variable has been removed.
    
    loop {
        let start = Instant::now();
        algorithm(&mut rng);
        let duration = start.elapsed().as_secs_f64();
        
        {
            let mut locked_stats = stats.lock().unwrap();
            let entry = locked_stats.entry(name).or_default();
            entry.runs += 1;
            entry.total_time += duration;
            entry.min_time = entry.min_time.min(duration);
            entry.max_time = entry.max_time.max(duration);
        }
        // The sleep call is intentionally removed for the unthrottled test.
    }
}

fn yaml_writer(stats: SharedStats) {
    let tmp_path = PathBuf::from(format!("{}.tmp", RUST_STATS_FILE));
    let final_path = Path::new(RUST_STATS_FILE);
    loop {
        thread::sleep(Duration::from_secs(10));
        let mut stats_copy = BTreeMap::new();
        {
            let mut locked_stats = stats.lock().unwrap();
            for (&name, s) in locked_stats.iter_mut() {
                stats_copy.insert(name, s.clone());
                *s = AlgorithmStats::default();
            }
        }
        if stats_copy.is_empty() {
            continue;
        }
        let yaml_string = match serde_yaml::to_string(&stats_copy) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("[Rust YAML Writer] Warning: Failed to serialize stats: {}", e);
                continue;
            }
        };
        match File::create(&tmp_path).and_then(|mut f| f.write_all(yaml_string.as_bytes())) {
            Ok(_) => {
                if let Err(e) = std::fs::rename(&tmp_path, final_path) {
                    eprintln!("[Rust YAML Writer] Warning: Failed to write stats file (likely a temporary lock): {}", e);
                }
            }
            Err(e) => {
                eprintln!("[Rust YAML Writer] Warning: Failed to create or write to temp file: {}", e);
            }
        }
    }
}

// --- ALGORITHMS ---

fn array_sort(rng: &mut StdRng) {
    let mut arr = [0u32; 40];
    for item in arr.iter_mut() {
        *item = rng.gen_range(0..100);
    }
    arr.sort_unstable();
}

fn fibonacci(rng: &mut StdRng) {
    let mut a = 0u64;
    let mut b = 1u64;
    for _ in 0..rng.gen_range(20..=35) {
        let temp = a;
        a = b;
        b = temp.wrapping_add(b);
    }
}

fn game_of_life(rng: &mut StdRng) {
    let (w, h, g) = (35, 35, 5);
    let mut grid = [[0u8; 35]; 35];
    for x in 0..w {
        for y in 0..h {
            grid[x][y] = rng.gen_range(0..=1);
        }
    }
    let mut new_grid = grid;
    for _ in 0..g {
        for x in 0..w {
            for y in 0..h {
                let mut live_neighbors = 0;
                for i in -1..=1 {
                    for j in -1..=1 {
                        if i == 0 && j == 0 { continue; }
                        let nx = (x as isize + i + w as isize) as usize % w;
                        let ny = (y as isize + j + h as isize) as usize % h;
                        live_neighbors += grid[nx][ny];
                    }
                }
                new_grid[x][y] = ((grid[x][y] == 1 && (2..=3).contains(&live_neighbors)) || (grid[x][y] == 0 && live_neighbors == 3)) as u8;
            }
        }
        std::mem::swap(&mut grid, &mut new_grid);
    }
}

fn matrix_multiplication(rng: &mut StdRng) {
    let dim = 50;
    let a = Array2::from_shape_fn((dim, dim), |_| rng.gen_range(0..10));
    let b = Array2::from_shape_fn((dim, dim), |_| rng.gen_range(0..10));
    let _result = a.dot(&b);
}

fn prime_factors(rng: &mut StdRng) {
    let mut n = rng.gen_range(100_000..=500_000);
    let mut d = 2;
    while d * d <= n {
        while n % d == 0 { n /= d; }
        d += 1;
    }
}

fn is_leap_year(rng: &mut StdRng) {
    let y = rng.gen_range(1..=9999);
    let _ = y % 4 == 0 && (y % 100 != 0 || y % 400 == 0);
}