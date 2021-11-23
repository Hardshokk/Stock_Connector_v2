from common_files.trading_script import PositionsOrdersManager


class GeneralWorker:
    """Класс основной родитель для всех workers"""
    def __init__(self, main_self):
        self.main_self = main_self
        self.ts = PositionsOrdersManager(self.main_self.terminal)

    def update_sl_and_tp(self, params, sl, tp):
        return self.ts.modify_sl_tp(params['symbol'], params['ticket'], params['order_type'], params['open_price'],
                                    sl_pips=sl, tp_pips=tp, tp_sl_is_price=True)
