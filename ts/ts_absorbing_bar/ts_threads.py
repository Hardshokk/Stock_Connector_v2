from ts.general_ts_thread import GeneralTsThread
from ts.ts_absorbing_bar.ts_finder_signals import TsAbsorbingBar


class TsAbsorbingBarThread(GeneralTsThread):
    """Основной поток Тс поглощающий бар"""
    def __init__(self, main_self):
        GeneralTsThread.__init__(self, main_self)
        self.class_ts = TsAbsorbingBar

