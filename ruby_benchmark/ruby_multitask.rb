require 'benchmark'
require 'thread'
require 'yaml'
require 'matrix' 
# --- Configuration ---
PYTHON_STATS_FILE = 'python_stats.yaml'
RUBY_STATS_FILE = 'ruby_stats.yaml'
ALGORITHMS = %w[array_sort fibonacci game_of_life matrix_multiplication prime_factors is_leap_year].freeze
STATS = ALGORITHMS.to_h { |name| [name, { runs: 0, total_time: 0.0, min_time: Float::INFINITY, max_time: 0.0 }] }
STATS_MUTEX = Mutex.new

# Seed for reproducibility
srand(123)



def array_sort

  40.times.map { rand(100) }.sort!
end

def fibonacci
  a, b = 0, 1
  rand(20..35).times { a, b = b, a + b }
end

def game_of_life
  w, h, g = 35, 35, 5
  grid = Array.new(w) { Array.new(h) { rand(2) } }
  
  g.times do
    new_grid = Array.new(w) { Array.new(h) }
    (0...w).each do |x|
      (0...h).each do |y|
        live_neighbors = 0
        (-1..1).each do |i|
          (-1..1).each do |j|
            next if i == 0 && j == 0
            live_neighbors += grid[(x + i) % w][(y + j) % h]
          end
        end
        
 
        new_grid[x][y] = (live_neighbors == 3 || (grid[x][y] == 1 && live_neighbors == 2)) ? 1 : 0
      end
    end
    grid = new_grid
  end
end

def matrix_multiplication
  dim = 50
  a = Matrix.build(dim, dim) { rand(10) }
  b = Matrix.build(dim, dim) { rand(10) }
  a * b 
end

def prime_factors
  num = rand(100_000..500_000)
  factors = []
  d = 2

  while d * d <= num
    while num % d == 0
      factors << d
      num /= d
    end
    d += 1
  end
  factors << num if num > 1
end

def is_leap_year
  # This function is already extremely fast.
  y = rand(1..9999)
  y % 4 == 0 && (y % 100 != 0 || y % 400 == 0)
end

# --- Core Application Logic ---

ALGO_FUNCTIONS = ALGORITHMS.to_h do |name|
  [name, method(name.to_sym)]
end

def worker(name, func)
  loop do
    duration = Benchmark.realtime { func.call }
    STATS_MUTEX.synchronize do
      s = STATS[name]
      s[:runs] += 1
      s[:total_time] += duration
      # Slightly cleaner min/max update
      s[:min_time] = [s[:min_time], duration].min
      s[:max_time] = [s[:max_time], duration].max
    end
    #sleep(0.05)
  end
end

def yaml_writer
  tmp_file = RUBY_STATS_FILE + '.tmp'
  loop do
    sleep(10)
    stats_copy = nil
    STATS_MUTEX.synchronize do
      # Deep copy and reset stats atomically
      stats_copy = STATS.transform_values(&:dup)
      STATS.each_value do |v|
        v[:runs], v[:total_time], v[:min_time], v[:max_time] = 0, 0.0, Float::INFINITY, 0.0
      end
    end
    File.write(tmp_file, stats_copy.to_yaml)
    File.rename(tmp_file, RUBY_STATS_FILE)
  end
end

def main
  # Cleanup previous run files
  [PYTHON_STATS_FILE, RUBY_STATS_FILE, PYTHON_STATS_FILE + '.tmp', RUBY_STATS_FILE + '.tmp'].each do |f|
    File.delete(f) if File.exist?(f)
  end
  
  # The Python script is now responsible for reporting
  threads = [Thread.new { yaml_writer }]
  threads += ALGO_FUNCTIONS.map do |name, func|
    Thread.new { worker(name, func) }
  end

  puts "starting ruby multitask benchmark v0.1"
  puts "written by: Thomas Tannenberg"
  puts "Starting Ruby multitask worker threads..."
  puts "Ruby multitask workers initialized for algorithms: #{ALGORITHMS.join(', ')}"


  
  threads.each(&:join)
end

main