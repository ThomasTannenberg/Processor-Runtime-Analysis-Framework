package com.benchmark;

import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

// =========================
//   P-RAF: Java Benchmark Worker (Queue/Concurrent Version)
// =========================

public class Benchmark {
    // --- Configuration ---
    private static final String ORCHESTRATOR_HOST = "127.0.0.1";
    private static final int ORCHESTRATOR_PORT = 9000;
    private static final String LANGUAGE_NAME = "Java";
    private static final List<String> ALGORITHMS = List.of(
            "array_sort", "fibonacci", "game_of_life",
            "matrix_multiplication", "prime_factors", "is_leap_year"
    );

    private static final ObjectMapper jsonMapper = new ObjectMapper();
    private static final ThreadLocal<Random> threadLocalRandom = ThreadLocal.withInitial(Random::new);

    // Result class to store result data for queue
    private static class Result {
        final String lang;
        final String algo;
        final double duration;
        Result(String lang, String algo, double duration) {
            this.lang = lang;
            this.algo = algo;
            this.duration = duration;
        }
    }

    public static void main(String[] args) {
        System.out.println("✅ Starting P-RAF Java worker (queue version)...");
        int numThreads = ALGORITHMS.size();
        ExecutorService executor = Executors.newFixedThreadPool(numThreads);
        BlockingQueue<Result> resultQueue = new LinkedBlockingQueue<>(1000); // Prevents unbounded growth

        Map<String, Runnable> algorithmTasks = Map.of(
            "array_sort", () -> runAlgorithm("array_sort", Benchmark::array_sort, resultQueue),
            "fibonacci", () -> runAlgorithm("fibonacci", Benchmark::fibonacci, resultQueue),
            "game_of_life", () -> runAlgorithm("game_of_life", Benchmark::game_of_life, resultQueue),
            "matrix_multiplication", () -> runAlgorithm("matrix_multiplication", Benchmark::matrix_multiplication, resultQueue),
            "prime_factors", () -> runAlgorithm("prime_factors", Benchmark::prime_factors, resultQueue),
            "is_leap_year", () -> runAlgorithm("is_leap_year", Benchmark::is_leap_year, resultQueue)
        );

        // Launch worker threads
        for (String name : ALGORITHMS) {
            executor.submit(algorithmTasks.get(name));
        }

        // Sender thread: keep connection, send everything from queue
        Thread senderThread = new Thread(() -> senderLoop(resultQueue));
        senderThread.setDaemon(true);
        senderThread.start();

        // Add shutdown hook to clean up
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            executor.shutdownNow();
            senderThread.interrupt();
        }));
    }

    // Worker runner: run forever, put results into queue
    private static void runAlgorithm(String name, Runnable algorithm, BlockingQueue<Result> queue) {
        while (!Thread.currentThread().isInterrupted()) {
            long start = System.nanoTime();
            algorithm.run();
            double duration = (System.nanoTime() - start) / 1_000_000_000.0;
            try {
                queue.put(new Result(LANGUAGE_NAME, name, duration));
            } catch (InterruptedException e) {
                break;
            }
        }
    }

    // Sender thread: keep one connection, send JSON results from the queue
    private static void senderLoop(BlockingQueue<Result> queue) {
        while (!Thread.currentThread().isInterrupted()) {
            try (Socket socket = new Socket(ORCHESTRATOR_HOST, ORCHESTRATOR_PORT);
                 PrintWriter out = new PrintWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8), true)) {
                System.out.println("✅ Sender connected to orchestrator.");
                while (!Thread.currentThread().isInterrupted()) {
                    Result result = queue.take(); // blocks until result available
                    sendResult(out, result.lang, result.algo, result.duration);
                }
            } catch (Exception e) {
                System.err.println("⚠️  Sender connection lost. Retrying in 2s...");
                try { Thread.sleep(2000); } catch (InterruptedException ex) { break; }
            }
        }
    }

    private static void sendResult(PrintWriter out, String lang, String algo, double duration) {
        try {
            ObjectNode payload = jsonMapper.createObjectNode();
            payload.put("lang", lang);
            payload.put("algo", algo);
            payload.put("duration", duration);
            out.println(jsonMapper.writeValueAsString(payload));
        } catch (Exception ignored) {}
    }

    // --- Algorithms (same as before) ---
    private static void array_sort() {
        Random r = threadLocalRandom.get();
        int[] a = new int[40];
        for(int i=0; i<a.length; i++) a[i] = r.nextInt(100);
        Arrays.sort(a);
    }
    private static void fibonacci() {
        Random r = threadLocalRandom.get();
        long a=0, b=1;
        for(int i=0; i<r.nextInt(16)+20; i++) { long t=a; a=b; b=t+a; }
    }
    private static void game_of_life() {
        Random r = threadLocalRandom.get();
        int w=35, h=35, g=5;
        int[][] grid = new int[w][h];
        for(int i=0; i<w; i++) for(int j=0; j<h; j++) grid[i][j] = r.nextInt(2);
        for(int gen=0; gen<g; gen++) {
            int[][] nG = new int[w][h];
            for(int x=0; x<w; x++) for(int y=0; y<h; y++) {
                int lN=0;
                for(int i=-1; i<=1; i++) for(int j=-1; j<=1; j++) {
                    if(i==0 && j==0) continue;
                    lN += grid[(x+i+w)%w][(y+j+h)%h];
                }
                boolean iL = grid[x][y] == 1;
                nG[x][y] = (iL && (lN==2||lN==3)) || (!iL && lN==3) ? 1 : 0;
            }
            grid = nG;
        }
    }
    private static void matrix_multiplication() {
        Random r = threadLocalRandom.get();
        int d=50;
        int[][] a = new int[d][d], b = new int[d][d];
        for(int i=0; i<d; i++) for(int j=0; j<d; j++) { a[i][j]=r.nextInt(10); b[i][j]=r.nextInt(10); }
        int[][] res = new int[d][d];
        for(int i=0; i<d; i++) for(int j=0; j<d; j++) for(int k=0; k<d; k++) res[i][j] += a[i][k] * b[k][j];
    }
    private static void prime_factors() {
        Random r = threadLocalRandom.get();
        int n = 100000 + r.nextInt(400001);
        List<Integer> fac = new ArrayList<>();
        int d=2;
        while(d*d <= n) {
            if(n%d==0) { fac.add(d); n/=d; } else { d++; }
        }
        if(n > 1) fac.add(n);
    }
    private static void is_leap_year() {
        int y = threadLocalRandom.get().nextInt(9999)+1;
        boolean isLeap = (y%4==0 && (y%100!=0 || y%400==0));
    }
}
