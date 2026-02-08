def get_max_sum(n):
    dp = [0, 1]
    for i in range(2, n + 1):
        dp.append(max(i, dp[int(i / 2)] + dp[int(i / 3)] + dp[int(i / 4)] + dp[int(i / 5)]))
    return dp[n]
