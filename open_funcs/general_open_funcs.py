from common_files.common_functions import get_symbol_info
from common_files.common_functions import get_symbol_format_terminal
from common_files.trading_script import PositionsOrdersManager


class GeneralOpenFunc:
    def __init__(self, main_self, symbol):
        self.main_self = main_self
        self.symbol = symbol
        self.ts = PositionsOrdersManager(self.main_self.terminal)

    def control_availability_bid_ask_price(self):
        symbol_info = get_symbol_info(self.symbol, self.main_self.terminal)
        if (not symbol_info['bid']) and (not symbol_info['ask']):
            self.main_self.log_edit.append("Нет цен аск и бид, рынок вероятно закрыт")
            return True
        return False

    def control_availability_orders_in_terminal(self, only_pos=False):
        df_positions, df_orders = self.ts.get_positions_and_orders(symbol=self.symbol)
        if only_pos:
            if len(df_positions) > 0:
                return True
            return False
        if (len(df_orders) > 0) or (len(df_positions) > 0):
            self.main_self.log_edit.append(f"Невозможно открыть еще одну позицию на символе {self.symbol}")
            return True
        return False
