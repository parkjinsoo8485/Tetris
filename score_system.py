# score_system.py
print("### score_system.py LOADED ###")

class TetrisScore:
    LINE_CLEAR_SCORES = {
        1: 100,
        2: 300,
        3: 500,
        4: 800
    }

    def __init__(self):
        self.score = 0
        self.level = 1
        self.total_lines = 0
        self.combo = -1

    def _update_level(self):
        self.level = (self.total_lines // 10) + 1

    def clear_lines(self, lines):
        """
        lines: 한 번에 지운 줄 수 (0~4)
        반환값: 이번에 추가된 점수
        """
        if lines == 0:
            self.combo = -1
            return 0

        self.combo += 1

        base = self.LINE_CLEAR_SCORES.get(lines, 0)
        gained = base * self.level

        combo_bonus = 0
        if self.combo > 0:
            combo_bonus = 50 * self.combo * self.level

        gained += combo_bonus

        self.score += gained
        self.total_lines += lines
        self._update_level()

        return gained

    def soft_drop(self, cells):
        self.score += cells

    def hard_drop(self, cells):
        self.score += cells * 2
