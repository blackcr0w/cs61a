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

def identity(k):
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


def make_adder(n):
	"""Return a function that takes in a parameter K and return k + n

	>>> add_three = make_adder(3)
	>>> add_three(4)
	7
	"""
	def adder(k):
		return k + n
		"""remember, adder can use the parameter of itself and the formal parameter of make_adder"""
	return adder

from operator import add
def curry2(f):
	def g(x):
		def h(y):
			return f(x, y)
		return h
	return g


