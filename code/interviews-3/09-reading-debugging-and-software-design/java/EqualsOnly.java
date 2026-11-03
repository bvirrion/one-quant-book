import java.util.HashMap;
import java.util.Map;

public class EqualsOnly {
    static final class Key {
        final String symbol;

        Key(String symbol) { this.symbol = symbol; }

        @Override public boolean equals(Object o) {
            return o instanceof Key && ((Key) o).symbol.equals(symbol);
        }
    }

    public static void main(String[] args) {
        Map<Key, Long> limits = new HashMap<>();
        limits.put(new Key("AAA"), 1000L);
        System.out.println(new Key("AAA").equals(new Key("AAA")));
        System.out.println(limits.get(new Key("AAA")));
    }
}
