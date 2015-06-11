"""generalization"""
def sum_naturals(n):
	"""sum of the first n naturals
	>>> sum_naturals(5)
	15
	"""
	return summation(n, identity)

def sum_cubes(n):
	"""sum of the cube of the first n naturals
	>>> sum_cubes(5)
	225
	"""
	return summation(n, cube)

def cube(k):
	return pow(k, 3)

dfsd
	return k

def summation(n, term):
	"""sum the first N items of a sequence
	>>> summation(5, cube)
	225
	>>> summation(5, identity)
	15
	"""
	total, k = 0, 1
	while k <= n:
		total, k = total + term(k), k + 1
	return total





