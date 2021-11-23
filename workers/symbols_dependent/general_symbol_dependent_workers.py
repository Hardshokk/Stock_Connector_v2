from workers.general_workers import GeneralWorker
import common_files.common_functions as cf


class GeneralSymbolDependentWorker(GeneralWorker):
    def __init__(self, main_self, symbol):
        GeneralWorker.__init__(self, main_self)
        self.main_self = main_self
        self.symbol = symbol

    def create_pos_params_dict(self):
        """получаю удобный словарик с параметрами"""
        position_df, order_df = self.ts.get_positions_and_orders(symbol=self.symbol)
        symbol_info = cf.get_symbol_info(self.symbol, self.main_self.terminal)
        pos_params_dict = {}
        for i_pos in position_df.index:
            "получаю все необходимые переменные"
            pos_params_dict['symbol'] = self.symbol
            pos_params_dict['profit'] = position_df.loc[i_pos, 'profit']
            pos_params_dict['volume'] = position_df.loc[i_pos, 'volume']
            pos_params_dict['points'] = \
                round(position_df.loc[i_pos, 'profit'] / position_df.loc[i_pos, 'volume'], 0)
            pos_params_dict['take_profit'] = position_df.loc[i_pos, 'tp']
            pos_params_dict['stop_loss'] = position_df.loc[i_pos, 'sl']
            pos_params_dict['open_price'] = position_df.loc[i_pos, 'price_open']
            pos_params_dict['order_type'] = position_df.loc[i_pos, 'type']
            pos_params_dict['ticket'] = position_df.loc[i_pos, 'ticket']
            pos_params_dict['digits'] = symbol_info['digits']
            pos_params_dict['point'] = symbol_info['point']
            pos_params_dict['terminal'] = self.main_self.terminal
        return pos_params_dict
