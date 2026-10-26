public class ProgrammingBasics {
    static int bump(int value) {
        return value + 1;
    }

    public static void main(String[] args) {
        int denominator = 0;
        int number = 5;
        int total = 0;
        int[] values = {1, 2, 3};
        for (int value : values) {
            if (value == 2) {
                continue;
            }
            total += value;
        }
        System.out.println("division: " + (-7 / 3) + " " + (-7 % 3));
        System.out.println("guard: " + (denominator != 0 && 12 / denominator > 1));
        System.out.println("value: " + number + " " + bump(number));
        System.out.println("total: " + total);
    }
}
