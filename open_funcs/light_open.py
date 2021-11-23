import common_files.common_functions as cf
from common_files.trading_script import PositionsOrdersManager


class LightOpen:
    def __init__(self, main_self):
        self.main_self = main_self
        self.ts = PositionsOrdersManager(self.main_self.terminal)

    def open_market_pos(self, order_type: int, price_type: str, limit_order: bool, pending_order_price=0, take=0.0,
                        stop=0.0):
        """функция от get_deal, собирает информацию необходимую для передачи на открытие ордера"""
        symbol = self.main_self.use_deal_privod_combo_select_symbol.currentText()
        symbol_info = cf.get_symbol_info(symbol, self.main_self.terminal)
        lot = self.main_self.use_deal_privod_spin_volume.value()
        if price_type == "ask" or price_type == "bid":
            price_order = symbol_info[price_type]
        elif price_type == "pending_order_price":
            price_order = pending_order_price
        if limit_order:
            self.ts.open_deferred_contract_fx(symbol, lot, order_type, price_order, stop_order=stop, take_price=take)
        else:
            self.ts.open_contract_fx(symbol, lot, order_type, self.main_self.terminal)

    def close_pos_or_delete_orders(self, close_pos: bool, delete_orders: bool):
        """функция от get_deal, собирает информацию необходимую для закрытия или удаления ордера"""
        if (close_pos and delete_orders) or (not close_pos and not delete_orders):
            raise AttributeError("Неверно переданы параметры")
        symbol = self.main_self.use_deal_privod_combo_select_symbol.currentText()
        df_positions, df_orders = self.ts.get_positions_and_orders(symbol=symbol)
        if close_pos and (not df_positions.empty):
            for pos_ix in df_positions.index:
                ticket = df_positions.loc[pos_ix, "ticket"]
                lot = df_positions.loc[pos_ix, "volume"]
                order_type = df_positions.loc[pos_ix, "type"]
                response = self.ts.close_contract_fx(symbol, ticket, lot, order_type)
        elif close_pos and df_positions.empty:
            self.main_self.log_edit.append("Открытых позиций нет")

        if delete_orders and (not df_orders.empty):
            for ord_ix in df_orders.index:
                ticket = df_orders.loc[ord_ix, "ticket"]
                response = self.ts.del_deferred_contract(ticket)
        elif delete_orders and df_orders.empty:
            self.main_self.log_edit.append("Отложенных ордеров нет")
    # def auto_liquidation(self):
    #     """автоликвидация всех ордеров после 23:45"""
    #     if (dt.datetime.now().hour == 23) and (dt.datetime.now().minute >= 45):
    #         close_pos_or_delete_orders(self, True, False)
    #         close_pos_or_delete_orders(self, False, True)
    # def stop_reverse(self, params, mode=""):
    #     if mode == "update":
    #         print("only_update", params['symbol'])
    #         if not self.stop_reverse_dict.get(params['symbol']):
    #             self.stop_reverse_dict[params['symbol']] = {'params': params, 'price_reverse': params['stop_loss']}
    #         elif params['stop_loss'] != self.stop_reverse_dict.get(params['symbol'].get('price_reverse')):
    #             self.stop_reverse_dict[params['symbol']] = {'params': params, 'price_reverse': params['stop_loss']}
    #     elif mode == "clear":
    #         print("only_clear")
    #         symbol = self.self.use_deal_privod_combo_select_symbol.currentText()
    #         symbol_info = cf.get_symbol_info(params['symbol'], self.terminal)
    #         if params['order_type'] == 0:
    #             if symbol_info['bid'] <= self.stop_reverse_dict[symbol]['price_reverse']:
    #                 open_market_pos(self, 1, 'bid', True)
    #                 del self.stop_reverse_dict[symbol]
    #                 self.use_deal_privod_checkbox_stop_reverse.setCheckState(False)
    #         elif params['order_type'] == 1:
    #             if symbol_info['ask'] >= self.stop_reverse_dict[symbol]['price_reverse']:
    #                 open_market_pos(self, 0, 'ask', True)
    #                 del self.stop_reverse_dict[symbol]
    #                 self.use_deal_privod_checkbox_stop_reverse.setCheckState(False)
    #
    #
    # def _contra_cluster_synchronization(self):
    #     """функция от open_pos_contra_cluster"""
    #     if self.use_sl_main_checkbox.isChecked():
    #         self.use_sl_standart_spin_size.setValue(self.use_deal_privod_contra_cluster_spin_stop.value())
    #         self.use_sl_radio_standart.setChecked(True)
    #     if self.use_tp_main_checkbox.isChecked():
    #         if dt.datetime.now().hour >= 10 and (dt.datetime.now().hour < 20):
    #             self.use_deal_privod_contra_cluster_spin_tp.setValue(75)
    #         else:
    #             self.use_deal_privod_contra_cluster_spin_tp.setValue(50)
    #         self.use_tp_spin_size.setValue(self.use_deal_privod_contra_cluster_spin_tp.value())
    #         self.use_tp_checkbox_auto_pips_for_take.setChecked(False)
    #
    #
    # def open_pos_contra_cluster(self):
    #     """contra_cluster ТС, основная функция"""
    #     _contra_cluster_synchronization(self)
    #     offset = self.use_deal_privod_contra_cluster_spin_offset.value()
    #     stop_pips = self.use_deal_privod_contra_cluster_spin_stop.value()
    #     symbol = self.use_deal_privod_combo_select_symbol.currentText()
    #     rates_frame, symbol_info = cf.get_bars_one_tf(symbol, mt5.TIMEFRAME_M1, 1, 5, self.terminal)
    #     if (not symbol_info['bid']) and (not symbol_info['ask']):
    #         self.log_edit.append("Нет цен аск и бид, рынок вероятно закрыт")
    #         return
    #     df_positions, df_orders = ts.get_positions_and_orders(self.terminal, symbol=symbol)
    #     if (len(df_orders) > 0) or (len(df_positions) > 0):
    #         self.log_edit.append(f"Невозможно открыть еще одну позицию на символе {symbol}")
    #         return
    #     index = len(rates_frame) - 1
    #     if rates_frame.loc[index, 'bar_direct'] == "up_bar":
    #         price_for_order = round(rates_frame.loc[index, 'low'] + ((stop_pips - offset) * symbol_info['point']),
    #                                 symbol_info['digits'])
    #         stop_loss = round(rates_frame.loc[index, 'low'] - offset * symbol_info['point'], symbol_info['digits'])
    #         take_profit = round(price_for_order + self.use_tp_spin_size.value() * symbol_info['point'], symbol_info['digits'])
    #         if symbol_info['ask'] <= price_for_order:
    #             open_market_pos(self, 0, 'ask', True)
    #         elif symbol_info['ask'] > price_for_order:
    #             open_market_pos(self, 0, 'pending_order_price', True, pending_order_price=price_for_order,
    #                             take=take_profit, stop=stop_loss)
    #         else:
    #             self.log_edit.append("Неизвестная ошибка, вероятно неправильная ask цена")
    #
    #     elif rates_frame.loc[index, 'bar_direct'] == 'down_bar':
    #         price_for_order = round(rates_frame.loc[index, 'high'] - ((stop_pips - offset) * symbol_info['point']),
    #                                 symbol_info['digits'])
    #         stop_loss = round(rates_frame.loc[index, 'high'] + offset * symbol_info['point'], symbol_info['digits'])
    #         take_profit = round(price_for_order - self.use_tp_spin_size.value() * symbol_info['point'], symbol_info['digits'])
    #         if symbol_info['bid'] >= price_for_order:
    #             open_market_pos(self, 1, 'bid', True)
    #         elif symbol_info['bid'] < price_for_order:
    #             open_market_pos(self, 1, 'pending_order_price', True, pending_order_price=price_for_order,
    #                             take=take_profit, stop=stop_loss)
    #         else:
    #             self.log_edit.append("Неизвестная ошибка, вероятно неправильная bid цена")

    def get_deal(self, deal_var):
        """основная функция, менеджер"""
        if not self.main_self.use_deal_privod_main_checkbox.isChecked():
            self.main_self.log_edit.append("Функция торговли через привод отключена. "
                                           "Чтобы начать торговать нужно ее включить.")
            return
        if deal_var == "buy_market_lim":
            self.open_market_pos(0, 'ask', True)
        elif deal_var == "sell_market_lim":
            self.open_market_pos(1, 'bid', True)
        elif deal_var == "buy_market":
            self.open_market_pos(0, 'ask', False)
        elif deal_var == "sell_market":
            self.open_market_pos(1, 'bid', False)
        elif deal_var == "close_position":
            self.close_pos_or_delete_orders(True, False)
        elif deal_var == "delete_order":
            self.close_pos_or_delete_orders(False, True)
        # elif deal_var == "open_pos_contra_cluster":
        #     self.open_pos_contra_cluster(self)