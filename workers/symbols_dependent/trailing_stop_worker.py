if self.main_self.use_trailing_main_checkbox.isChecked():
    "4. трейлинг стоп"
    trailing_func(self.main_self, self.positions_params_dict[symbol])


def trailing_func(self, params):
    if not self.use_trailing_main_checkbox.isChecked():
        return
    trailing_step = self.use_trailing_spin.value()
    symbol_info = cf.get_symbol_info(params['symbol'], params['terminal'])
    if params['order_type'] == 0:
        step_now = int(((symbol_info['bid'] - params['open_price']) / trailing_step) - 1)
        if step_now > 0:
            stop_loss = round(params['open_price'] + step_now * trailing_step, params['digits'])
            if stop_loss < params['stop_loss']:
                response = update_sl_and_tp(params, stop_loss, params['take_profit'])
    elif params['order_type'] == 1:
        step_now = int(((params['open_price'] - symbol_info['ask']) / trailing_step) - 1)
        if step_now > 0:
            stop_loss = round(params['open_price'] - step_now * trailing_step, params['digits'])
            if stop_loss > params['stop_loss']:
                response = update_sl_and_tp(params, stop_loss, params['take_profit'])