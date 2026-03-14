class CostTracker:
    def __init__(self) -> None:
        self.total_cost = 0.0

    def add(self, amount: float) -> None:
        self.total_cost += amount

    def get_total(self) -> float:
        return round(self.total_cost, 6)