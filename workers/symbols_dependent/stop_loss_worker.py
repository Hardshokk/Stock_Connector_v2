from workers.symbols_dependent.general_symbol_dependent_workers import GeneralSymbolDependentWorker
import common_files.common_functions as cf


class StopLossWorker(GeneralSymbolDependentWorker):
    """Стоплосс"""
    def __init__(self, main_self, symbol):
        GeneralSymbolDependentWorker.__init__(self, main_self, symbol)
        self.symbol = symbol
        self.params = self.create_pos_params_dict()
        self.use_standard_sl = True
        self.use_auto_sl = False
        self.standard_sl = 25
        self.auto_sl = 0.3

    def _error_add_sl(self):
        self.main_self.log_edit.append(f"Увеличьте размер споп лосса {self.params['symbol']}. Невозможно установить.")

    def _check_condition_and_update(self, stop_loss):
        if stop_loss != self.params['stop_loss']:
            self.update_sl_and_tp(self.params, stop_loss, self.params['take_profit'])
        elif self.params['stop_loss'] == 0.0:
            self.update_sl_and_tp(self.params, stop_loss, self.params['take_profit'])

    def sl_func(self):
        self.params = self.create_pos_params_dict()
        symbol_info = cf.get_symbol_info(self.symbol, self.main_self.terminal)
        """стоп лосс будет выставляться автоматически при отсутствии стопа"""
        pips_for_sl = 0
        if self.use_standard_sl:
            pips_for_sl = self.use_auto_sl
        elif self.use_auto_sl:
            if self.params['take_profit'] != 0.0:
                pips_for_sl = round(
                    abs(self.params['open_price'] - self.params['take_profit']) * self.auto_sl, self.params['digits'])
        if not pips_for_sl:
            return

        if (self.params['order_type'] == 0) and (self.params['stop_loss'] < self.params['open_price']):
            stop_loss = round(self.params['open_price'] - pips_for_sl * self.params['point'], self.params['digits'])
            if symbol_info['bid'] > stop_loss:
                self._check_condition_and_update(stop_loss)
            else:
                self._error_add_sl()
        elif (self.params['order_type'] == 1) and ((self.params['stop_loss'] > self.params['open_price']) or
                                                   (self.params['stop_loss'] == 0.0)):
            stop_loss = round(self.params['open_price'] + pips_for_sl * self.params['point'], self.params['digits'])
            if symbol_info['ask'] < stop_loss:
                self._check_condition_and_update(stop_loss)
            else:
                self._error_add_sl()
