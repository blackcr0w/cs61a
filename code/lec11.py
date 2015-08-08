def counting(s, value):
	total, index = 0, 0
	while(index < len(s)):
		if s[index] == value:
			total = total + 1
		index = index + 1
	return total

def counting2(s, value):
	total = 0
	for k in s:
		if k == value:
			total = total + 1
	"""print(k) Python会把return value直接打印出来
	如果想打印某个value 直接return就行
	而且可以一次return多个值
	k会bound到s的最后一个值"""
	return total, k

def coutning3(s, value1, value2):
	total = 0
	for e1, e2 in s:
		if e1 == value1 and e2 == value2:
			total = total + 1
	return total
