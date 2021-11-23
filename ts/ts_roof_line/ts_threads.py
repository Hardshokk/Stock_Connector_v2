from ts.general_ts_thread import GeneralTsThread
from ts.ts_roof_line.ts_finder_signals import TsRoofLine


class TsRoofLineThread(GeneralTsThread):
    """Основной поток Тс поглощающий бар"""
    def __init__(self, main_self):
        GeneralTsThread.__init__(self, main_self)
        self.class_ts = TsRoofLine

