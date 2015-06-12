def split(n):
	return n // 10, n % 10

def sum_digits(n):
	if n < 10:
		return n;
	else:
		allbutlast, last = split(n)
		return sum_digits(allbutlast) + last