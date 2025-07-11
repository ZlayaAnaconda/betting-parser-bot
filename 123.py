def f(x, h):
    if (h == 3 or h == 5) and x >= 70:
        return 1
    elif h == 5 and x < 70:
        return 0
    elif x >= 70 and h < 5:
        return 0
    else:
        if h % 2 == 0:
            return f(x + 1, h + 1) or f(x + 4, h + 1) or f(x * 5, h + 1)
            # стратегия победителя
        else:
            return f(x + 1, h + 1) and f(x + 4, h + 1) and f(x * 5, h + 1)
            # стратегия проигравшего
def f1(x, h):
    if h == 3 and x >= 70:
        return 1
    elif h == 3 and x < 70:
        return 0
    elif x >= 70 and h < 3:
        return 0
    else:
        if h % 2 == 0:
            return f1(x + 1, h + 1) or f1(x + 4, h + 1) or f1(x * 5, h + 1)
            # стратегия победителя
        else:
            return f1(x + 1, h + 1) and f1(x + 4, h + 1) and f1(x * 5, h + 1)
            # стратегия проигравшего(любой ход)
for x in range(1, 70):
    if f(x, 1) == 1:
        print(x)
print("====")
for x in range(1, 70):
    if f1(x, 1) == 1:
        print(x)