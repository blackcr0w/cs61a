def trace1(fn):
	"""return a version of fn that is first printed when it is first called
	fn -- a function of one argument
	"""
	def traced(x):
		print('calling', fn, 'on an argument', x)
		return fn(x)
	return traced


@trace1
def square(x):
	return x * x
@trace1
def sum_square_up_to(n):
	total, k = 0, 1
	while(k <= n):
		total, k = total + square(k), k + 1
	return total

# when printing a function in python, 
# the address of this function is actually printed,
# and this is the reference address, the start point of this funcion

# decoration is just put "@ " at the begining of a function, 
# transforming the function into another function