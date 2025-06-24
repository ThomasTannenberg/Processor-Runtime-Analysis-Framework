package com.benchmark;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

public class JavaMultitask {

    private static final String JAVA_STATS_FILE = "java_stats.yaml";
    private static final List<String> ALGORITHMS = List.of(
            "array_sort", "fibonacci", "game_of_life", "matrix_multiplication", "prime_factors", "is_leap_year"
    );

    private static final Map<String, AlgorithmStats> STATS = new ConcurrentHashMap<>();
    private static final Random RAND = new Random(123);

    static class AlgorithmStats {
        private long runs = 0;
        private double totalTime = 0.0;
        private double minTime = Double.POSITIVE_INFINITY;
        private double maxTime = 0.0;

        public synchronized void update(double durationSeconds) {
            this.runs++;
            this.totalTime += durationSeconds;
            this.minTime = Math.min(this.minTime, durationSeconds);
            this.maxTime = Math.max(this.maxTime, durationSeconds);
        }

        public synchronized Map<String, Object> copyAndReset() {
            Map<String, Object> copy = new LinkedHashMap<>();
            copy.put("runs", this.runs);
            copy.put("total_time", this.totalTime);
            copy.put("min_time", this.minTime);
            copy.put("max_time", this.maxTime);

            this.runs = 0;
            this.totalTime = 0.0;
            this.minTime = Double.POSITIVE_INFINITY;
            this.maxTime = 0.0;
            return copy;
        }
    }

    public static void main(String[] args) {
        System.out.println("starting java multitask benchmark v0.1");
        System.out.println("written by Thomas@Tannenberg.online");
        System.out.println("Starting Java workers...");
        System.err.println("Java  multitask workers initialized for algorithms: " + ALGORITHMS);

        for (String name : ALGORITHMS) {
            STATS.put(name, new AlgorithmStats());
        }

        ScheduledExecutorService executor = Executors.newScheduledThreadPool(ALGORITHMS.size() + 1);

        Map<String, Runnable> algorithmTasks = Map.of(
            "array_sort", JavaMultitask::array_sort,
            "fibonacci", JavaMultitask::fibonacci,
            "game_of_life", JavaMultitask::game_of_life,
            "matrix_multiplication", JavaMultitask::matrix_multiplication,
            "prime_factors", JavaMultitask::prime_factors,
            "is_leap_year", JavaMultitask::is_leap_year
        );

        for (String name : ALGORITHMS) {
            Runnable task = algorithmTasks.get(name);
            executor.execute(() -> worker(name, task));
        }

        executor.scheduleAtFixedRate(JavaMultitask::yamlWriter, 10, 10, TimeUnit.SECONDS);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutting down Java workers...");
            executor.shutdown();
        }));
    }

    private static void worker(String name, Runnable algorithm) {
        while (true) {
            long start = System.nanoTime();
            algorithm.run();
            long end = System.nanoTime();
            double durationSeconds = (end - start) / 1_000_000_000.0;

            STATS.get(name).update(durationSeconds);

            try {
               Thread.sleep(0);
            } catch (InterruptedException e) {
                // This is fine for our simple app. A more robust app would log this.
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private static void yamlWriter() {
        File tmpFile = new File(JAVA_STATS_FILE + ".tmp");
        File finalFile = new File(JAVA_STATS_FILE);

        Map<String, Map<String, Object>> statsCopy = new LinkedHashMap<>();
        for (String name : ALGORITHMS) {
            statsCopy.put(name, STATS.get(name).copyAndReset());
        }

        try {
            ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());
            yamlMapper.writeValue(tmpFile, statsCopy);
            Files.move(tmpFile.toPath(), finalFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            // This is also fine for our app. In a real app, you'd use a logger.
            e.printStackTrace();
        }
    }

    // --- ALGORITHM IMPLEMENTATIONS ---

    private static void array_sort() {
        int[] arr = new int[40];
        for (int i = 0; i < arr.length; i++) {
            arr[i] = RAND.nextInt(100);
        }
        Arrays.sort(arr);
    }

    private static void fibonacci() {
        long a = 0, b = 1;
        int count = 20 + RAND.nextInt(16);
        for (int i = 0; i < count; i++) {
            long temp = a;
            a = b;
            b = temp + b;
        }
    }

    private static void game_of_life() {
        int w = 35, h = 35, g = 5;
        int[][] grid = new int[w][h];
        for (int i = 0; i < w; i++) for (int j = 0; j < h; j++) grid[i][j] = RAND.nextInt(2);

        for (int gen = 0; gen < g; gen++) {
            int[][] newGrid = new int[w][h];
            for (int x = 0; x < w; x++) {
                for (int y = 0; y < h; y++) {
                    int liveNeighbors = 0;
                    for (int i = -1; i <= 1; i++) {
                        for (int j = -1; j <= 1; j++) {
                            if (i == 0 && j == 0) continue;
                            liveNeighbors += grid[(x + i + w) % w][(y + j + h) % h];
                        }
                    }
                    boolean isLive = grid[x][y] == 1;
                    if (isLive && (liveNeighbors == 2 || liveNeighbors == 3)) newGrid[x][y] = 1;
                    else if (!isLive && liveNeighbors == 3) newGrid[x][y] = 1;
                    else newGrid[x][y] = 0;
                }
            }
            grid = newGrid;
        }
    }

    private static void matrix_multiplication() {
        int dim = 50;
        int[][] a = new int[dim][dim];
        int[][] b = new int[dim][dim];
        for(int i=0; i<dim; i++) for(int j=0; j<dim; j++) {
            a[i][j] = RAND.nextInt(10);
            b[i][j] = RAND.nextInt(10);
        }
        int[][] result = new int[dim][dim];
        for (int i = 0; i < dim; i++) {
            for (int j = 0; j < dim; j++) {
                for (int k = 0; k < dim; k++) {
                    result[i][j] += a[i][k] * b[k][j];
                }
            }
        }
    }

    private static void prime_factors() {
        int n = 100000 + RAND.nextInt(400001);
        // Using the modern "diamond operator" <>
        List<Integer> factors = new ArrayList<>();
        int d = 2;
        while (d * d <= n) {
            if (n % d == 0) {
                factors.add(d);
                n /= d;
            } else {
                d++;
            }
        }
        if (n > 1) {
            factors.add(n);
        }
    }

    // This method was a void, but it should return a boolean to match the other languages
    private static boolean is_leap_year_boolean() {
        int y = RAND.nextInt(9999) + 1;
        // The result of the expression is returned directly, avoiding the "unused variable" warning.
        return (y % 4 == 0 && (y % 100 != 0 || y % 400 == 0));
    }

    // We need a void-returning method to match the `Runnable` signature in the map
    private static void is_leap_year() {
        is_leap_year_boolean();
    }
}