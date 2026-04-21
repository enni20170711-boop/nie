from mis import mis2a,mis2b
from test1 import sum_up_to

mis2a()
mis2b()

x = int(input("請輸入一個整數:"))
if (x<=0):
	print(f"您輸入的值是{x},小於等於0")
else:
	sum = sum_up_to(x)
	print(f"1+2+...+{x} = {sum}")