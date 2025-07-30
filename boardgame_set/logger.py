from datetime import datetime


class DebugLogger:
    def __init__(self):
        self.logs = []

    def log(self, label, **kwargs):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] [{label}]")
        for key, value in kwargs.items():
            print(f"    {key}: {value}")
        self.logs.append((label, kwargs))

    def clear(self):
        self.logs.clear()


class GameLogger:
    log = []
    filepath = "game.log"
    color_map = {
        "START": (0, 120, 255),
        "END": (0, 180, 0),
        "ERROR": (255, 80, 80)
    }

    def add(self, message, tag=None, cards=None):
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f'[{tag}] {message}' if tag else message
        if cards:
            card_info = ' | 조합: ' + ", ".join(str(c) for c in cards)
            full_msg += card_info

        if self.log:
            recent_log = self.log[-1]
            if recent_log[1] != full_msg:
                self.log.append((time_str, full_msg))
        else:
            self.log.append((time_str, full_msg))

    def clear(self):
        self.log = []

    def save_to_file(self, filepath=None):
        if filepath is None:
            filepath = self.filepath
        last_saved_time = self.get_last_log_time(filepath)

        with open(filepath, 'a', encoding='utf-8') as f:
            for time_str, msg in self.log:
                current_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                if current_time > last_saved_time:
                    if msg.startswith('[START]'):
                        f.write('\n')
                    f.write(f'{time_str} | {msg}\n')

    @staticmethod
    def get_last_log_time(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                time_str = '1970-01-01 00:00:00'
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    time_str = last_line.split(" | ")[0]  # 예: "125430 | 세트 성공!"
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except FileNotFoundError:
            return datetime.strptime('1970-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
