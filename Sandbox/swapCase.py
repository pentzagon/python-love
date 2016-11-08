if __name__ == "__main__":
    string = "Hello World"
    for letter in string:
        if string[letter].isupper():
            string[letter].lower()
        if string[letter].islower():
            string[letter].upper()
    print string
