"""generalization"""
def sum_naturals(n):
	"""sum of the first n naturals
	>>> sum_naturals(5)
	15
	"""
	total, k = 0, 1
	while k <= n:
		total, k = total + k, k + 1
	return total

def sum_cubes(n):
	"""sum of the cube of the first n naturals
	>>> sum_cubes(5)
	225
	"""
	total, k = 0, 1
	while k <= n:
		total, k = total + pow(k, 3), k + 1
	return total
	