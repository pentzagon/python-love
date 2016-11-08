def printFib(index):
    if index == 0:
        #seed = [0]
        print 0
    elif index > 0:
        #seed = [0,1]
        oldseed = 0
        print oldseed
        newseed = 1
        print newseed
        for num in range(1,index):
            #seed.append(seed[num]+seed[num-1])
            nextseed = newseed + oldseed
            print nextseed
            oldseed = newseed
            newseed = nextseed
    #print seed

if __name__ == "__main__":
    #printFib(0)
    #printFib(1)
    printFib(10)