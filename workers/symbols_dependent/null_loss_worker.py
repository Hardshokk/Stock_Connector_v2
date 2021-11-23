from workers.symbols_dependent.general_symbol_dependent_workers import GeneralSymbolDependentWorker
import common_files.common_functions as cf


class NullLossWorker(GeneralSymbolDependentWorker):
    """Безубыток"""
    def __init__(self, main_self, symbol):
        GeneralSymbolDependentWorker.__init__(self, main_self, symbol)
        self.symbol = symbol
        self.params = self.create_pos_params_dict()
        self.use_fix_null_loss = True
        self.use_auto_null_loss = False
        self.fix_null_loss = 25

    def null_loss_func(self):
        self.params = self.create_pos_params_dict()
        if self.params['open_price'] == self.params['stop_loss']:
            return
        if self.use_fix_null_loss:
            price_anti_loss = self.fix_null_loss * self.params['point']
        else:
            price_anti_loss = abs(self.params['take_profit'] - self.params['open_price']) / 2

        symbol_info = cf.get_symbol_info(self.params['symbol'], self.params['terminal'])
        if (self.params['order_type'] == 0) and (self.params['stop_loss'] < self.params['open_price']):
            price_anti_loss = self.params['open_price'] + price_anti_loss
            if (symbol_info['bid'] >= price_anti_loss) and (self.params['open_price'] != self.params['stop_loss']):
                self.update_sl_and_tp(self.params, self.params['open_price'], self.params['take_profit'])
        elif self.params['order_type'] == 1 and ((self.params['stop_loss'] > self.params['open_price']) or
                                                 (self.params['stop_loss'] == 0.0)):
            price_anti_loss = self.params['open_price'] - price_anti_loss
            if (symbol_info['ask'] <= price_anti_loss) and (self.params['open_price'] != self.params['stop_loss']):
                self.update_sl_and_tp(self.params, self.params['open_price'], self.params['take_profit'])
