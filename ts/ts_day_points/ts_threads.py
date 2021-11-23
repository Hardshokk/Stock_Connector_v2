from ts.general_ts_thread import GeneralTsThread
from ts.ts_day_points.ts_finder_signals import TsDayPoints


class TsDayPointsThread(GeneralTsThread):
    """Основной поток Тс поглощающий бар"""
    def __init__(self, main_self):
        GeneralTsThread.__init__(self, main_self)
        self.class_ts = TsDayPoints

