import random

def shuffle(deck):
    # oldDeck = deck
    shuffledDeck = []
    for card in range(0,len(deck)):
        pos = random.randint(0,len(deck)-1)
        shuffledDeck.append(deck[pos])
        deck.remove(deck[pos])
    return shuffledDeck

if __name__ == "__main__":
    deck = range(52)
    shuffledDeck = shuffle(deck)
    print deck
    print shuffledDeck



