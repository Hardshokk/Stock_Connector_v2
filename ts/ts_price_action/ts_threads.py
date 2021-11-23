from ts.general_ts_thread import GeneralTsThread
from ts.ts_price_action.ts_finder_signals import TsPriceAction


class TsPriceActionThread(GeneralTsThread):
    """Основной поток Тс поглощающий бар"""
    def __init__(self, main_self):
        GeneralTsThread.__init__(self, main_self)
        self.class_ts = TsPriceAction
