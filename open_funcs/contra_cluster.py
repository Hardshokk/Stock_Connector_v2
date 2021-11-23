from open_funcs.general_open_funcs import GeneralOpenFunc
import datetime as dt
import common_files.common_functions as cf
from common_files.trading_script import PositionsOrdersManager


class ContraCluster(GeneralOpenFunc):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralOpenFunc.__init__(self, main_self, symbol)
        self.symbol = symbol
        self.tf_sec = tf_sec
        self.tf = cf.full_sec_in_tfs_dict[self.tf_sec]
        self.pos_start_bars = 1
        self.qv_get_bars = 5
        self.timer_del_order = None  # при создании экземляра запустить функцию ниже в потоке

        self.tp_point = 75
        self.stop_point = 25
        self.offset_point = 2
        self.lot = 1

    def tp_correction(self):
        """коррекция размера тейкпрофита в зависимости от времени"""
        if dt.datetime.now().hour >= 10 and (dt.datetime.now().hour < 20):
            self.tp_point = 75
        else:
            self.tp_point = 50

    def get_rates_frame_and_symbol_info(self, pos_start, qv_get):
        rates_frame, symbol_info = cf.get_bars_one_tf(self.symbol, self.tf, pos_start, qv_get, self.main_self.terminal)
        return rates_frame, symbol_info

    @staticmethod
    def get_direct(index, rates_frame):
        if rates_frame.loc[index, 'bar_direct'] == "up_bar":
            return "up_bar"
        elif rates_frame.loc[index, 'bar_direct'] == "down_bar":
            return "down_bar"

    def common_open_pos(self, order_type: int, price_type: str, limit_order: bool, pending_order_price=0,
                        take=0.0, stop=0.0):
        """функция выбирает вариант открытия -по рынку лимитом, -по рынку рыночным, -отложенным лимитом"""
        symbol_info = cf.get_symbol_info(self.symbol, self.main_self.terminal)
        price_order = 0.0
        if price_type == "ask" or price_type == "bid":
            price_order = symbol_info[price_type]
        elif price_type == "pending_order_price":
            price_order = pending_order_price
        self.timer_del_order = dt.datetime.now() + dt.timedelta(seconds=self.tf_sec)
        if limit_order:
            self.ts.open_deferred_contract_fx(self.symbol, self.lot, order_type, price_order,
                                              stop_order=stop, take_price=take)
        else:
            self.ts.open_contract_fx(self.symbol, self.lot, order_type)

    def open_pos_buy(self, symbol_info, price_for_order, take_profit, stop_loss):
        if symbol_info['ask'] <= price_for_order:
            self.common_open_pos(0, 'ask', True)
        elif symbol_info['ask'] > price_for_order:
            self.common_open_pos(0, 'pending_order_price', True, pending_order_price=price_for_order,
                                 take=take_profit, stop=stop_loss)

    def open_pos_sell(self, symbol_info, price_for_order, take_profit, stop_loss):
        if symbol_info['bid'] >= price_for_order:
            self.common_open_pos(1, 'bid', True)
        elif symbol_info['bid'] < price_for_order:
            self.common_open_pos(1, 'pending_order_price', True, pending_order_price=price_for_order,
                                 take=take_profit, stop=stop_loss)

    def open_pos_contra_cluster(self, signal_info):
        """contra_cluster ТС, основная функция"""
        rates_frame, symbol_info = self.get_rates_frame_and_symbol_info(self.pos_start_bars, self.qv_get_bars)
        if self.control_availability_bid_ask_price():
            return
        if self.control_availability_orders_in_terminal():
            return
        index = len(rates_frame) - 1
        if self.get_direct(index, rates_frame) == "up_bar":
            price_for_order = round(rates_frame.loc[index, 'low'] +
                                    ((self.stop_point - self.offset_point) * symbol_info['point']),
                                    symbol_info['digits'])
            stop_loss = round(rates_frame.loc[index, 'low'] - self.offset_point * symbol_info['point'],
                              symbol_info['digits'])
            take_profit = round(price_for_order + self.tp_point * symbol_info['point'], symbol_info['digits'])
            self.open_pos_buy(symbol_info, price_for_order, take_profit, stop_loss)

        elif self.get_direct(index, rates_frame) == 'down_bar':
            price_for_order = round(rates_frame.loc[index, 'high'] -
                                    ((self.stop_point - self.offset_point) * symbol_info['point']),
                                    symbol_info['digits'])
            stop_loss = round(rates_frame.loc[index, 'high'] + self.offset_point * symbol_info['point'],
                              symbol_info['digits'])
            take_profit = round(price_for_order - self.tp_point * symbol_info['point'], symbol_info['digits'])
            self.open_pos_sell(symbol_info, price_for_order, take_profit, stop_loss)

    def del_order_on_timer(self):
        """принимает решение по удалению отложенного ордера по истечению времени с момента установки"""
        if self.timer_del_order:
            if dt.datetime.now() > self.timer_del_order:
                self.close_pos_or_delete_orders(False, True)
                df_positions, df_orders = self.ts.get_positions_and_orders(symbol=self.symbol)
                if df_orders.empty:
                    self.timer_del_order = None

    def close_pos_or_delete_orders(self, close_pos: bool, delete_orders: bool):
        """функция  собирает информацию необходимую для закрытия или удаления ордера"""
        if (close_pos and delete_orders) or (not close_pos and not delete_orders):
            raise AttributeError("Неверно переданы параметры")
        df_positions, df_orders = self.ts.get_positions_and_orders(symbol=self.symbol)
        if close_pos and (not df_positions.empty):
            for pos_ix in df_positions.index:
                ticket = df_positions.loc[pos_ix, "ticket"]
                lot = df_positions.loc[pos_ix, "volume"]
                order_type = df_positions.loc[pos_ix, "type"]
                self.ts.close_contract_fx(self.symbol, ticket, lot, order_type)
        elif close_pos and df_positions.empty:
            self.main_self.log_edit.append("Открытых позиций нет")

        if delete_orders and (not df_orders.empty):
            for ord_ix in df_orders.index:
                ticket = df_orders.loc[ord_ix, "ticket"]
                self.ts.del_deferred_contract(ticket)
        elif delete_orders and df_orders.empty:
            self.main_self.log_edit.append("Отложенных ордеров нет")
