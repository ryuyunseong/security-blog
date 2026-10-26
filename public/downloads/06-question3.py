items = [1, 2]
alias = items
copied = items[:]
alias.append(5)
copied[0] = 9
print(items)
print(copied)
