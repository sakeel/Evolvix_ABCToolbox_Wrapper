class DataPoint:
    def __init__(self, time, amount):
        self.time = float(time)
        self.amount = float(amount)

    def __eq__(self, other):
        return (self.time == other.time) and (self.amount == other.amount)

