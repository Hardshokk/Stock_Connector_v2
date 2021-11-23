from ts.general_ts_thread import GeneralTsThread
from ts.ts_zones_finder.ts_finder_signals import TsZonesFinder


class TsZonesFinderThread(GeneralTsThread):
    """Основной поток Тс поглощающий бар"""
    def __init__(self, main_self):
        GeneralTsThread.__init__(self, main_self)
        self.class_ts = TsZonesFinder

