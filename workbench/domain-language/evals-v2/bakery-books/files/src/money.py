from dataclasses import dataclass

@dataclass
class LogLine:
    date: str
    amount: float
    direction: str  # "in" or "out"
    pot: str

class MoneyLog:
    def __init__(self):
        self.lines: list[LogLine] = []

    def add(self, line: LogLine):
        self.lines.append(line)

    def pot_totals(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for l in self.lines:
            sign = 1 if l.direction == "in" else -1
            totals[l.pot] = totals.get(l.pot, 0) + sign * l.amount
        return totals
