def split(n):
	return n // 10, n % 10

def sum_digits(n):
	if n < 10:
		return n;
	else:
		allbutlast, last = split(n)
		return sum_digits(allbutlast) + last

# def sum_digits(n):
# 	if n < 10:
# 		return n
# 	else:
# 		allbutlast, last = split(n)
# 		return sum_digits(allbutlast) + last

def luhn_sum(n):
	if n < 10:
		return n
	else:
		allbutlast, last = split(n)
		return luhn_sum_double(allbutlast) + last

def luhn_sum_double(n):
	allbutlast, last = split(n)
	luhn_digit = sum_digits(2 * last)
	if n < 10:
		return luhn_digit
	else:
		return luhn_sum(allbutlast) + luhn_digit
