from workers.symbols_dependent.general_symbol_dependent_workers import GeneralSymbolDependentWorker
import common_files.common_functions as cf


class AntiRollbackWorker(GeneralSymbolDependentWorker):
    """Антиоткат"""
    def __init__(self, main_self, symbol):
        GeneralSymbolDependentWorker.__init__(self, main_self, symbol)
        self.symbol = symbol
        self.params = self.create_pos_params_dict()
        self.activate = 0.6
        self.triggering = 0.4
        self.activation = False

    def _anti_rollback_func(self, points_for_finish):
        if self.params['points'] <= points_for_finish:
            response = self.ts.close_contract_fx(self.params['symbol'], self.params['ticket'], self.params['volume'],
                                                 self.params['order_type'], self.params['terminal'])
            if response['retcode'] == 10009:
                self.main_self.log_edit.append(f"Закрыл {self.params['symbol']} позицию по антиоткату!")
                self.activation = False

    def anti_rollback_func(self):
        self.params = self.create_pos_params_dict()
        if not self.activation:
            points_for_start_control = round((abs(self.params['open_price'] - self.params['take_profit']) *
                                              cf.mx_dict_full_point[self.params['digits']]) * self.activate, 0)
            self.activation = True if self.params['points'] >= points_for_start_control else False

        elif self.activation:
            points_for_finish = round((abs(self.params['open_price'] - self.params['take_profit']) *
                                      cf.mx_dict_full_point[self.params['digits']]) * self.triggering, 0)
            self._anti_rollback_func(points_for_finish)
            self.main_self.log_edit.append(f"Антиоткат активирован, срабатывание на {points_for_finish} пунтках")

