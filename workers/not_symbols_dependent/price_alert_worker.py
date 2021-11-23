if self.main_self.use_pricealert_main_checkbox.isChecked():
    "����� ��������"
    price_alert_func(self.main_self)


def _save_file_json(file, object):
    with open(file, "w") as f:
        json.dump(object, f)


def _price_alert_dict_create(self):
    """���������� � price_alert_func"""
    alert_dict = {}
    for instrument in self.symbols_fuchers_list:
        alert_dict[instrument] = {"out_channel": {"high_border": 0, "low_border": 0, "description": ""},
                                  "only_out_high": {"high_border": 0, "description": ""},
                                  "only_out_low": {"low_border": 0, "description": ""}}
    _save_file_json(self.alert_file_name, alert_dict)


def get_alert_file(self):
    """���������� � price_alert"""
    if not os.path.isfile(self.alert_file_name):
        print("������ ����� ����")
        _price_alert_dict_create(self)
    if os.stat(self.alert_file_name).st_size == 0:
        print("�������� ����")
        _price_alert_dict_create(self)
    with open(self.alert_file_name, "rb") as f:
        alert_dict = json.loads(f.read())
        return alert_dict


def show_alerts(self):
    alert_dict = get_alert_file(self)
    counter = 0
    for symbol in alert_dict.keys():
        for variant_alert in alert_dict[symbol].keys():
            description = alert_dict[symbol][variant_alert]["description"]
            if (("high_border" in alert_dict[symbol][variant_alert].keys()) and
                    ("low_border" in alert_dict[symbol][variant_alert].keys())):
                if alert_dict[symbol][variant_alert]["high_border"] != 0:
                    self.log_edit.append(f"--����� {symbol} ### {variant_alert} ### "
                                         f"{alert_dict[symbol][variant_alert]['high_border']} - "
                                         f"{alert_dict[symbol][variant_alert]['low_border']} - "
                                         f"### ��������: '{description}'\n")
                    counter += 1
            else:
                element_list = list(alert_dict[symbol][variant_alert].keys())
                del element_list[element_list.index("description")]
                value = alert_dict[symbol][variant_alert][element_list[0]]
                if value != 0:
                    self.log_edit.append(f"--����� {symbol} ### {variant_alert} ### {value} "
                                         f"### ��������: '{description}'\n")
                    counter += 1
    if counter == 0:
        self.log_edit.append(f"�������� ������� ���")


def update_alert_file(self, add_alert=False, delete_alert=False, clear_alerts=False):
    alert_only_high = self.use_pricealert_radio_high.isChecked()
    alert_only_low = self.use_pricealert_radio_low.isChecked()
    alert_out_channel = self.use_pricealert_radio_channel.isChecked()
    symbol = self.use_pricealert_combo_select_symbol.currentText()
    if sum([add_alert, delete_alert, clear_alerts]) != 1:
        self.log_edit.append("������, ������� ������ ��� �� ������ add/delete/clear alert")
        return
    if clear_alerts:
        _price_alert_dict_create(self)
        self.log_edit.append("������ ��� ������������ ������")
        return
    if sum([alert_only_high, alert_only_low, alert_out_channel]) != 1:
        self.log_edit.append("������, ������� ����� ������� ������")
        return
    alert_dict = get_alert_file(self)
    if alert_only_high:
        if add_alert:
            if self.use_pricealert_radio_high_spin_high.value() > 0:
                alert_dict[symbol]["only_out_high"]["high_border"] = self.use_pricealert_radio_high_spin_high.value()
                alert_dict[symbol]["only_out_high"]["description"] = self.use_pricealert_text_edit_description.toPlainText()
                self.log_edit.append(f"����� -������ ����- �� {symbol} ������� ��������.")
            else:
                self.log_edit.append("������, ������ �������� ����� ������ ����")
        elif delete_alert:
            alert_dict[symbol]["only_out_high"]["high_border"] = 0
            alert_dict[symbol]["only_out_high"]["description"] = ""
            self.log_edit.append(f"����� -������ ����- �� {symbol} ������� ������.")

    elif alert_only_low:
        if add_alert:
            if self.use_pricealert_radio_low_spin_low.value() > 0:
                alert_dict[symbol]["only_out_low"]["low_border"] = self.use_pricealert_radio_low_spin_low.value()
                alert_dict[symbol]["only_out_low"]["description"] = self.use_pricealert_text_edit_description.toPlainText()
                self.log_edit.append(f"����� -������ ����- �� {symbol} ������� ��������.")
            else:
                self.log_edit.append("������, ������ �������� ����� ������ ����")
        elif delete_alert:
            alert_dict[symbol]["only_out_low"]["low_border"] = 0
            alert_dict[symbol]["only_out_low"]["description"] = ""
            self.log_edit.append(f"����� -������ ����- �� {symbol} ������� ������.")

    elif alert_out_channel:
        if add_alert:
            if ((self.use_pricealert_radio_channel_spin_high.value() > 0) and
                    (self.use_pricealert_radio_channel_spin_low.value() > 0)):
                alert_dict[symbol]["out_channel"]["high_border"] = self.use_pricealert_radio_channel_spin_high.value()
                alert_dict[symbol]["out_channel"]["low_border"] = self.use_pricealert_radio_channel_spin_low.value()
                alert_dict[symbol]["out_channel"]["description"] = self.use_pricealert_text_edit_description.toPlainText()
                self.log_edit.append(f"����� -��� ������- �� {symbol} ������� ��������.")
            else:
                self.log_edit.append("������, ������ �������� ����� ������ ����")
        elif delete_alert:
            alert_dict[symbol]["out_channel"]["high_border"] = 0
            alert_dict[symbol]["out_channel"]["low_border"] = 0
            alert_dict[symbol]["out_channel"]["description"] = ""
            self.log_edit.append(f"����� -��� ������- �� {symbol} ������� ������.")
    else:
        self.log_edit.append("�������� � ������ ���� ������ ��������� update.")

    _save_file_json(self.alert_file_name, alert_dict)


def price_alert_func(self):
    """����� �������"""
    """�������� ������� ����� � ������ ��� ���� ��� ���"""
    if not os.path.isfile(self.alert_file_name):
        _price_alert_dict_create(self)

    """��������� ����"""
    alert_dict = get_alert_file(self)

    if (not isinstance(alert_dict, dict)) or (not alert_dict):
        self.log_edit.append("������ alert_dict, �� ���� ��� �� �� �������.")
        return 0
    """�������� ������� �������"""
    for symbol in alert_dict.keys():
        symbol_info = cf.get_symbol_info(symbol, self.terminal)
        if not (symbol_info['bid'] and symbol_info['ask']):
            t_now = dt.datetime.now().strftime("%H:%M")
            self.log_edit.append(f'��� � ��� ����� ����, ����� ������ ����� ������. {t_now}')
            tm.sleep(60)
            return

        value = alert_dict[symbol]['only_out_high']['high_border']
        description = alert_dict[symbol]['only_out_high']['description']
        if not (value <= 0):
            if symbol_info['bid'] >= value:
                message = f"�� {symbol} ���� ��������� {value}, ��������: {description}"
                self.alert_one_symbol(message, symbol)

        value = alert_dict[symbol]['only_out_low']['low_border']
        description = alert_dict[symbol]['only_out_low']['description']
        if not (value <= 0):
            if symbol_info['ask'] <= value:
                message = f"�� {symbol} ���� ���������� ���� ������� {value}, ��������: {description}"
                self.alert_one_symbol(message, symbol)

        value_high = alert_dict[symbol]['out_channel']['high_border']
        value_low = alert_dict[symbol]['out_channel']['low_border']
        description = alert_dict[symbol]['out_channel']['description']
        if not ((value_high <= 0) and (value_low <= 0)):
            if (symbol_info['bid'] >= value_high) or (symbol_info['ask'] <= value_low):
                message = f"�� {symbol} ���� ��� ��������� {value_low} - {value_high}, ��������: {description}"
                self.alert_one_symbol(message, symbol)