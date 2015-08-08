from fractions import gcd


"""this is the functions of the rational number"""
""" returns the rational number with numerator n and denominator d."""
"""this will return the class as a whole"""

""" this is a constructor to rational number """
def rational(n, d):
	g = gcd(n, d)
	return [n // g, d // g]

""" numer and denom are selector of rational number """
def numer(x):
        return x[0]
def denom(x):
        return x[1]

def add_rationals(x, y):
        nx, dx = numer(x), denom(x)
        ny, dy = numer(y), denom(y)
        return rational(nx * dy + ny * dx, dx * dy)

def mul_rationals(x, y):
        return rational(numer(x) * numer(y), denom(x) * denom(y))

def print_rational(x):
        print(numer(x), '/', denom(x))

def rationals_are_equal(x, y):
        return numer(x) * denom(y) == numer(y) * denom(x)
        
def pair(x, y):
        """Return a function that represents a pair."""
        def get(index):
            if index == 0:
                return x
            elif index == 1:
                return y
        return get

def select(p, i):
        """Return the element at index i of pair p."""
        return p(i)