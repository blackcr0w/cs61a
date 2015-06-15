from ucb import trace

def cascade(n):
	if n < 10:
		print(n)
		return None
	else:
		print(n)
		cascade(n // 10)
		print(n)
		return None 
# if there is no return statement, it just return None

def inverse_cascade(n):
	grow(n)
	print(n)
	shirink(n)

def f_then_g(f, g, n):
	if n:
		f(n)
		g(n)

grow = lambda n: f_then_g(grow, print, n // 10)
shirink = lambda n: f_then_g(print, shirink, n // 10)

@trace
def fib(n):
	if n == 0:
		return 0
	elif n == 1:
		return 1
	else:
		return fib(n - 1) + fib(n - 2)
