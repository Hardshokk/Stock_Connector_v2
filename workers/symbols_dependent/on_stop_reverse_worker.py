def stop_reverse(self, params, mode=""):
    if mode == "update":
        print("only_update", params['symbol'])
        if not self.stop_reverse_dict.get(params['symbol']):
            self.stop_reverse_dict[params['symbol']] = {'params': params, 'price_reverse': params['stop_loss']}
        elif params['stop_loss'] != self.stop_reverse_dict.get(params['symbol'].get('price_reverse')):
            self.stop_reverse_dict[params['symbol']] = {'params': params, 'price_reverse': params['stop_loss']}
    elif mode == "clear":
        print("only_clear")
        symbol = self.self.use_deal_privod_combo_select_symbol.currentText()
        symbol_info = cf.get_symbol_info(params['symbol'], self.terminal)
        if params['order_type'] == 0:
            if symbol_info['bid'] <= self.stop_reverse_dict[symbol]['price_reverse']:
                open_market_pos(self, 1, 'bid', True)
                del self.stop_reverse_dict[symbol]
                self.use_deal_privod_checkbox_stop_reverse.setCheckState(False)
        elif params['order_type'] == 1:
            if symbol_info['ask'] >= self.stop_reverse_dict[symbol]['price_reverse']:
                open_market_pos(self, 0, 'ask', True)
                del self.stop_reverse_dict[symbol]
                self.use_deal_privod_checkbox_stop_reverse.setCheckState(False)