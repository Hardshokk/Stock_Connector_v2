from ts.ts_catch.ts_finder_signals import TsCatchPlayer
from ts.general_ts_thread import GeneralTsThread


class TsCatchTread(GeneralTsThread):
    """Класс поток от finder сигналов стратегии"""
    def __init__(self, main_self):
        GeneralTsThread.__init__(self, main_self)
        self.class_ts = TsCatchPlayer


if __name__ == '__main__':
    pass
