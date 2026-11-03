public class Boxes {
    public static void main(String[] args) {
        Integer a = 127, b = 127;
        Integer c = 128, d = 128;
        String s = "AAA", t = "AAA", u = new String("AAA");
        System.out.println((a == b) + " " + (c == d) + " " + c.equals(d));
        System.out.println((s == t) + " " + (s == u) + " " + s.equals(u));
    }
}
