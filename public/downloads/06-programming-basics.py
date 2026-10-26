def bump(value):
    return value + 1


def main():
    denominator = 0
    number = 5
    total = 0
    values = [1, 2, 3]
    for value in values:
        if value == 2:
            continue
        total += value
    print("division:", -7 // 3, -7 % 3)
    print("guard:", denominator != 0 and 12 // denominator > 1)
    print("value:", number, bump(number))
    print("total:", total)


if __name__ == "__main__":
    main()
