# =========================
#   P-RAF: Ruby Benchmark Worker (Queue/Concurrent Version)
# =========================

require 'socket'
require 'json'
require 'thread'

ORCHESTRATOR_HOST = '127.0.0.1'
ORCHESTRATOR_PORT = 9000
LANGUAGE_NAME = 'Ruby'
ALGORITHMS = %w[array_sort fibonacci game_of_life matrix_multiplication prime_factors is_leap_year]

def array_sort
  a = Array.new(40) { rand(100) }
  a.sort!
end

def fibonacci
  a, b = 0, 1
  (rand(20..35)).times { a, b = b, a + b }
end

def game_of_life
  w, h, g = 35, 35, 5
  grid = Array.new(w) { Array.new(h) { rand(2) } }
  g.times do
    new_grid = Array.new(w) { Array.new(h, 0) }
    w.times do |x|
      h.times do |y|
        ln = 0
        (-1..1).each do |i|
          (-1..1).each do |j|
            next if i.zero? && j.zero?
            xi, yj = (x + i) % w, (y + j) % h
            ln += grid[xi][yj]
          end
        end
        il = grid[x][y] == 1
        new_grid[x][y] = (il && (ln == 2 || ln == 3)) || (!il && ln == 3) ? 1 : 0
      end
    end
    grid = new_grid
  end
end

def matrix_multiplication
  d = 50
  a = Array.new(d) { Array.new(d) { rand(10) } }
  b = Array.new(d) { Array.new(d) { rand(10) } }
  res = Array.new(d) { Array.new(d, 0) }
  d.times do |i|
    d.times do |j|
      d.times { |k| res[i][j] += a[i][k] * b[k][j] }
    end
  end
end

def prime_factors
  n = rand(100_000..500_000)
  f = []
  d = 2
  while d * d <= n
    if n % d == 0
      f << d
      n /= d
    else
      d += 1
    end
  end
  f << n if n > 1
end

def is_leap_year
  y = rand(1..9999)
  leap = (y % 4 == 0 && (y % 100 != 0 || y % 400 == 0))
end

ALGO_FUNCTIONS = {
  "array_sort" => method(:array_sort),
  "fibonacci" => method(:fibonacci),
  "game_of_life" => method(:game_of_life),
  "matrix_multiplication" => method(:matrix_multiplication),
  "prime_factors" => method(:prime_factors),
  "is_leap_year" => method(:is_leap_year)
}

# Shared thread-safe queue for results
RESULT_QUEUE = Queue.new

def algo_worker(name, algo_proc)
  loop do
    start = Process.clock_gettime(Process::CLOCK_MONOTONIC)
    algo_proc.call
    duration = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start
    RESULT_QUEUE << { lang: LANGUAGE_NAME, algo: name, duration: duration }
  end
end

def sender
  loop do
    begin
      puts "🔄 Ruby sender connecting to orchestrator..."
      TCPSocket.open(ORCHESTRATOR_HOST, ORCHESTRATOR_PORT) do |sock|
        puts "✅ Ruby sender connected."
        while true
          payload = RESULT_QUEUE.pop
          begin
            sock.puts(payload.to_json)
          rescue => e
            puts "⚠️  Ruby sender write error: #{e}. Reconnecting..."
            break # Outer loop will reconnect
          end
        end
      end
    rescue => e
      puts "⚠️  Ruby sender connect error: #{e}. Retrying in 2s..."
      sleep 2
    end
  end
end

puts "✅ Starting P-RAF Ruby worker (queue version)..."

threads = []
ALGORITHMS.each do |name|
  threads << Thread.new { algo_worker(name, ALGO_FUNCTIONS[name]) }
end

# Start the sender thread
sender_thread = Thread.new { sender }

threads.each(&:join)
sender_thread.join
