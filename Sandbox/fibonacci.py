if __name__ == "__main__":
    nums = [0,1]
    for x in range(1,50):
        nums.append(nums[x-1] + nums[x])
    print(nums)