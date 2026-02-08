R = 3
C = 3

def min_cost(cost, m, n):
    # Initialize the cost matrix with zeros
    total_cost = [[0 for _ in range(C)] for _ in range(R)]

    # Base case: starting cell
    total_cost[0][0] = cost[0][0]

    # Fill first column (only moving down)
    for i in range(1, m + 1):
        total_cost[i][0] = total_cost[i - 1][0] + cost[i][0]

    # Fill first row (only moving right)
    for j in range(1, n + 1):
        total_cost[0][j] = total_cost[0][j - 1] + cost[0][j]

    # Fill the rest of the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            total_cost[i][j] = min(
                total_cost[i - 1][j - 1],  # diagonal
                total_cost[i - 1][j],      # up
                total_cost[i][j - 1]       # left
            ) + cost[i][j]

    return total_cost[m][n]
