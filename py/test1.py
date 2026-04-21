def square(y):
	print(f"{y}的三次方是{y**3}")

def sum_up_to(n):
	total = 0
	for i in range(1, n + 1):
		total += i
	return total

# 只有「直接執行 test1.py」時，以下程式才會執行
# 如果是被 import，以下代碼會被忽略
if __name__ == "__main__":
	x = int(input("請輸入一個整數:"))
	#x += 10

	if (x<=0):
		print(f"您輸入的值是{x},小於等於0")
	else:
		print(f"您輸入的值是{x},大於0")
		for i in range(1, x+1):
			#print(i, end=";")
			square(i)

