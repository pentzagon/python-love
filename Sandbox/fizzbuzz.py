if __name__ == "__main__":
    for x in range(1,100):
        msg = ''
        if (x % 3) == 0:
            msg += 'Fizz'
        if (x % 5) == 0:
            msg += 'Buzz'
        if msg == '':
            msg = x
        print msg