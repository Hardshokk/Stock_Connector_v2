import numpy as np
import MetaTrader5
from workers.symbols_dependent.general_symbol_dependent_workers import GeneralSymbolDependentWorker
import common_files.common_functions as cf


class TakeProfitWorker(GeneralSymbolDependentWorker):
    """Тейкпрофит"""
    def __init__(self, main_self, symbol):
        GeneralSymbolDependentWorker.__init__(self, main_self, symbol)
        self.symbol = symbol
        self.params = self.create_pos_params_dict()
        self.use_auto_tp = True
        self.standard_tp = 200

    def _error_add_tp(self):
        self.main_self.log_edit.append("Увеличьте размер тейк профита")

    def _get_auto_pips_for_tp(self):
        """функция от tp_func, обеспечивает автоподбор тейка"""
        rates_frame, symbol_info = cf.get_bars_one_tf(self.symbol, MetaTrader5.TIMEFRAME_D1, 1, 15,
                                                      self.main_self.terminal)
        rates_frame['atr_mean'] = 0.
        rates_frame['atr_mean_correct'] = 0.
        period_mean = 6
        qv_bar_on_diff = 3
        for index in rates_frame.index:
            if index < period_mean:
                continue
            rates_frame.loc[index, 'atr_mean'] = \
                round(rates_frame.loc[index - period_mean: index, "atr_bar"].mean() / 4, 0)
            if rates_frame.loc[index - qv_bar_on_diff, 'atr_mean'] == 0:
                continue
            "получаю разность атр на последовательных барах и имитацию дифференцирования"
            diff_list = []
            for i in range(qv_bar_on_diff, 0, -1):
                diff_list.append(rates_frame.loc[index - i, 'atr_mean'] - rates_frame.loc[index - i + 1, 'atr_mean'])
            rates_frame.loc[index, 'atr_mean_correct'] = round(
                rates_frame.loc[index, 'atr_mean'] - np.array(diff_list).mean(), 0)
        return rates_frame.iloc[-1].at['atr_mean_correct']

    def tp_func(self):
        self.params = self.create_pos_params_dict()
        if self.use_auto_tp:
            self.standard_tp = self._get_auto_pips_for_tp()

        symbol_info = cf.get_symbol_info(self.symbol, self.main_self.terminal)
        plan_tp = 0.0
        if self.params['order_type'] == 0:
            plan_tp = round(self.params['open_price'] + self.standard_tp * self.params['point'], self.params['digits'])
            if plan_tp < round(symbol_info['ask'] + 15 * self.params['point'], self.params['digits']):
                self._error_add_tp()
                return None
        elif self.params['order_type'] == 1:
            plan_tp = round(self.params['open_price'] - self.standard_tp * self.params['point'], self.params['digits'])
            if plan_tp > round(symbol_info['bid'] - 15 * self.params['point'], self.params['digits']):
                self._error_add_tp()
                return None

        if self.params['take_profit'] != plan_tp:
            self.update_sl_and_tp(self.params, self.params['stop_loss'], plan_tp)
        elif not self.params['take_profit']:
            self.update_sl_and_tp(self.params, self.params['stop_loss'], plan_tp)
