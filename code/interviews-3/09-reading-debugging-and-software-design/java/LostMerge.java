import java.util.concurrent.ConcurrentHashMap;

public class LostMerge {
    static final ConcurrentHashMap<String, Long> position = new ConcurrentHashMap<>();

    static void add(String symbol, long qty) {
        Long old = position.get(symbol);
        position.put(symbol, (old == null ? 0L : old) + qty);
    }

    public static void main(String[] args) throws InterruptedException {
        Thread[] pool = new Thread[4];
        for (int i = 0; i < pool.length; i++) {
            pool[i] = new Thread(() -> {
                for (int j = 0; j < 100000; j++) add("AAA", 1);
            });
            pool[i].start();
        }
        for (Thread t : pool) t.join();
        System.out.println(position.get("AAA"));
    }
}
