if self.main_self.use_deal_privod_liquidation_checkbox.isChecked():
    "автоликвидация всех позиций и ордеров после 23:45"
    auto_liquidation(self.main_self)


def auto_liquidation(self):
    """автоликвидация всех ордеров после 23:45"""
    if (dt.datetime.now().hour == 23) and (dt.datetime.now().minute >= 45):
        close_pos_or_delete_orders(self, True, False)
        close_pos_or_delete_orders(self, False, True)