import MetaTrader5 as mt5
import pandas as pd
from common_files.common_functions import terminal_create_connect, terminal_close_connect, \
    get_symbol_format_terminal, symbol_is_format_code
import datetime as dt
"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Функции торговли на форекс~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""


class PositionsOrdersManager:
    def __init__(self, terminal):
        self.terminal = terminal

    def get_qv_pos_and_orders_from_terminal(self):
        """Функция получает количество сделок из терминала возвращает числа"""
        terminal_create_connect(self.terminal)
        qv_positions = mt5.positions_total()
        qv_orders = mt5.orders_total()
        terminal_close_connect()
        return qv_positions, qv_orders

    def get_positions_and_orders(self, symbol=""):
        """функция получает датафреймы со всеми позициями и ордерами"""
        terminal_create_connect(self.terminal)
        if symbol:
            if symbol_is_format_code(symbol):
                positions = mt5.positions_get(symbol=get_symbol_format_terminal(symbol))
                orders = mt5.orders_get(symbol=get_symbol_format_terminal(symbol))
            else:
                positions = mt5.positions_get(symbol=symbol)
                orders = mt5.orders_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            orders = mt5.orders_get()
        terminal_close_connect()
        df_positions = pd.DataFrame()
        df_orders = pd.DataFrame()
        if positions:
            df_positions = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
            df_positions['time'] = pd.to_datetime(df_positions['time'], unit='s')
            # print(df_positions.loc[:, ['ticket', 'symbol', 'volume', 'type', 'price_open', 'profit']])
        if orders:
            df_orders = pd.DataFrame(orders, columns=orders[0]._asdict().keys())
            df_orders['time_setup'] = pd.to_datetime(df_orders['time_setup'], unit='s')
            # print(df_positions.loc[:, ['ticket', 'symbol', 'volume', 'type', 'price_open', 'profit']])
        return df_positions, df_orders

    def get_history_deals(self, date_start):
        """функция получает исторические данные"""
        date = dt.datetime(date_start.year, date_start.month, date_start.day)
        terminal_create_connect(self.terminal)
        hist_pos = mt5.history_deals_get(date, dt.datetime.now()+dt.timedelta(hours=3))
        terminal_close_connect()
        df_hist_pos = pd.DataFrame()
        if hist_pos:
            df_hist_pos = pd.DataFrame(hist_pos, columns=hist_pos[0]._asdict().keys())
            df_hist_pos['time'] = pd.to_datetime(df_hist_pos['time'], unit='s')
        print(date, dt.datetime.now())
        return df_hist_pos

    def open_contract_fx(self, symbol, lot, order_type, sl_pips=0.0, tp_pips=0.0):
        terminal_create_connect(self.terminal)
        symbol_info = mt5.symbol_info(symbol)
        while not symbol_info:
            symbol_info = mt5.symbol_info(symbol)
            print("Не могу получить информацию о символе trading_script open_contract_fx")
        point = symbol_info.point
        deviation = 20
        type_pos = int()
        price = 0.0
        tp = 0.0
        sl = 0.0
        if order_type == 0:
            type_pos = mt5.ORDER_TYPE_BUY
            price = symbol_info.ask
            if sl_pips > 0:
                sl = price - sl_pips * point
            if tp_pips > 0:
                tp = price + tp_pips * point
        elif order_type == 1:
            type_pos = mt5.ORDER_TYPE_SELL
            price = symbol_info.bid
            if sl_pips > 0:
                sl = price + sl_pips * point
            if tp_pips > 0:
                tp = price - tp_pips * point
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot),
            "type": int(type_pos),
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 0,
            "comment": "python script open",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        print(result._asdict())
        terminal_close_connect()
        return result._asdict()

    def modify_sl_tp(self, symbol, pos_id, order_type, price_open, sl_pips=0.0, tp_pips=0.0, tp_sl_is_price=False):
        """Функция обновляет стоп и/или тейк"""
        terminal_create_connect(self.terminal)
        point = mt5.symbol_info(symbol).point
        digits = mt5.symbol_info(symbol).digits
        tp = 0.0
        sl = 0.0
        if order_type == 0:
            if sl_pips > 0:
                if not tp_sl_is_price:
                    sl = round(price_open - sl_pips * point, digits)
                elif tp_sl_is_price:
                    sl = sl_pips
            if tp_pips > 0:
                if not tp_sl_is_price:
                    tp = round(price_open + tp_pips * point, digits)
                elif tp_sl_is_price:
                    tp = tp_pips
        elif order_type == 1:
            if sl_pips > 0:
                if not tp_sl_is_price:
                    sl = round(price_open + sl_pips * point, digits)
                elif tp_sl_is_price:
                    sl = sl_pips
            if tp_pips > 0:
                if not tp_sl_is_price:
                    tp = round(price_open - tp_pips * point, digits)
                elif tp_sl_is_price:
                    tp = tp_pips
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": int(pos_id),
            "sl": sl,
            "tp": tp,
            "magic": 0,
            "comment": "python script modify",
        }
        result = mt5.order_send(request)
        print(result._asdict())
        terminal_close_connect()
        return result._asdict()

    def close_contract_fx(self, symbol, pos_id, lot, order_type):
        """функция закрывает указанный контракт"""
        terminal_create_connect(self.terminal)
        price = 0.0
        deviation = 20
        type_pos = int()
        if order_type == 0:
            price = mt5.symbol_info_tick(symbol).bid
            type_pos = mt5.ORDER_TYPE_SELL
        if order_type == 1:
            price = mt5.symbol_info_tick(symbol).ask
            type_pos = mt5.ORDER_TYPE_BUY
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": type_pos,
            "position": int(pos_id),
            "position_by": int(pos_id),
            "price": price,
            "deviation": deviation,
            "magic": 0,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }
        result = mt5.order_send(request)
        print(result._asdict())
        terminal_close_connect()
        return result._asdict()

    def open_deferred_contract_fx(self, symbol, lot, order_type, price_order, stop_order=0.0, take_price=0.0):
        """функция выставляет отложенный ордер"""
        terminal_create_connect(self.terminal)
        deviation = 10
        if order_type == 0:
            type_pos = mt5.ORDER_TYPE_BUY_LIMIT
        elif order_type == 1:
            type_pos = mt5.ORDER_TYPE_SELL_LIMIT
        elif order_type == 3:
            type_pos = mt5.ORDER_TYPE_BUY_STOP
        elif order_type == 4:
            type_pos = mt5.ORDER_TYPE_SELL_STOP
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": str(symbol),
            "volume": float(lot),
            "price": float(price_order),
            "stoplimit": 0.0,
            "sl": stop_order,
            "tp": take_price,
            "type": int(type_pos),
            "magic": 0,
            "comment": "python open_deferred_contract",
            "deviation": deviation,
            "type_filling": mt5.ORDER_FILLING_RETURN,
            "type_time": mt5.ORDER_TIME_DAY,
            "expiration": 0
        }
        result = mt5.order_send(request)
        print(result)
        terminal_close_connect()
        if isinstance(result, tuple):
            return result._asdict()
        else:
            return {}

    def del_deferred_contract(self, ticket):
        """удаляет отложенный ордер"""
        terminal_create_connect(self.terminal)
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": int(ticket),
        }
        result = mt5.order_send(request)
        print(result)
        terminal_close_connect()
        if isinstance(result, tuple):
            return result._asdict()
        else:
            return {}

    def close_all_positions(self):
        """Функция от profit control, полностью закрывает все сделки"""
        df_positions, df_orders = self.get_positions_and_orders()
        while not df_positions.empty:
            df_positions, df_orders = self.get_positions_and_orders()
            for i in df_positions.index:
                symbol = df_positions.loc[i, 'symbol']
                ticket = df_positions.loc[i, 'ticket']
                lot = df_positions.loc[i, 'volume']
                type_order = df_positions.loc[i, 'type']
                self.close_contract_fx(symbol, ticket, lot, type_order)


if __name__ == '__main__':
    pass


