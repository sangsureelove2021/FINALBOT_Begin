#!/usr/bin/env python3
"""
Calculate the first 10 numbers of the Fibonacci sequence.
"""

def fibonacci(n):
    """Generate the first n Fibonacci numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence


def main():
    # Calculate first 10 Fibonacci numbers
    first_10_fib = fibonacci(10)
    
    print("The first 10 numbers of the Fibonacci sequence are:")
    for i, num in enumerate(first_10_fib, start=1):
        print(f"F({i}) = {num}")


if __name__ == "__main__":
    main()
