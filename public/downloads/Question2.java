public class Question2 {
    static void change(int[] values) {
        values[0] = 7;
        values = new int[] {9};
    }

    public static void main(String[] args) {
        int[] data = {2};
        change(data);
        System.out.println(data[0]);
    }
}
