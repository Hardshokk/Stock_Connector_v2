from ts.general_ts_finder import GeneralTsFinder


class TsPriceAction(GeneralTsFinder):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_price_action'
        self.qv_bars = 60
        self.chart_slice = []
        self.center_range_percent = 45
        self.edge_range_percent = 10

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        self.chart_slice = self.mongo.get_qv_last_bars(self.symbol, self.tf_sec, self.qv_bars)
        if len(self.chart_slice) == self.qv_bars:
            signals_dict = {
                'contra_bar': self.check_contra_bar(),
                'lag_bar': self.check_lag_bar(),
                'pin_bar': self.check_pin_bar(),
                'micro_bar': self.check_micro_bar(),
                'check_mini_vol': self.check_min_max_vol(),
                'check_divergent_direct_delta': self.check_divergent_direct_delta(),
                'check_crown_delta': self.check_crown_delta()
            }
            return self.form_signal_list(signals_dict)
        else:
            print("Размер чарт слайс и необходимого количества баров не соответствует.")

    def common_variables(self):
        """Повторяющиеся метрики"""
        work_bar = self.chart_slice[-1]
        one_percent = (work_bar['high'] - work_bar['low']) / 100
        center_low = work_bar['low'] + one_percent * self.center_range_percent
        center_high = work_bar['high'] - one_percent * self.center_range_percent
        return work_bar, one_percent, center_low, center_high

    def get_qv_bars_one_direct(self, qv_bars):
        """Отвечает на вопрос сколько предыдущих баров одного направления"""
        offset = 2
        last_direct = self.chart_slice[-offset]['bar_metrics']['bar_direct']
        counter = 0
        for n in range(-offset - 1, -qv_bars - offset - 1, -1):
            bar_direct = self.chart_slice[n]['bar_metrics']['bar_direct']
            if last_direct == bar_direct:
                counter += 1
        if counter == qv_bars:
            return True

    def check_contra_bar(self):
        """Ищет совпадение на вариант контрабар"""
        if not self.get_qv_bars_one_direct(2):
            return False
        work_bar, one_percent, center_low, center_high = self.common_variables()
        # определения метрик
        if (work_bar['close'] >= center_low) and (work_bar['close'] <= center_high):
            pass
        else:
            return False
        if work_bar['bar_metrics']['bar_direct'] == 'up_bar':
            open_range = work_bar['low'] + one_percent * self.edge_range_percent
            if work_bar['open'] <= open_range:
                return True
        elif work_bar['bar_metrics']['bar_direct'] == 'down_bar':
            open_range = work_bar['high'] - one_percent * self.edge_range_percent
            if work_bar['open'] >= open_range:
                return True
        return False

    def check_lag_bar(self):
        """Ищет совпадение на вариант лагобар"""
        if not self.get_qv_bars_one_direct(2):
            return False
        work_bar, one_percent, center_low, center_high = self.common_variables()
        # определения метрик
        if (work_bar['open'] >= center_low) and (work_bar['open'] <= center_high):
            pass
        else:
            return False
        if work_bar['bar_metrics']['bar_direct'] == 'down_bar':
            open_range = work_bar['low'] + one_percent * self.edge_range_percent
            if work_bar['close'] <= open_range:
                return True
        elif work_bar['bar_metrics']['bar_direct'] == 'up_bar':
            open_range = work_bar['high'] - one_percent * self.edge_range_percent
            if work_bar['close'] >= open_range:
                return True
        return False

    def check_pin_bar(self):
        """Ищет совпадение на вариант пинбар"""
        if not self.get_qv_bars_one_direct(3):
            return ""
        work_bar = self.chart_slice[-1]
        # рассчет первой метрики
        oc = work_bar['open'] - work_bar['close']
        hl = work_bar['high'] - work_bar['low']
        ratio = hl * 25 / 100
        if abs(oc) <= ratio:
            metric_1 = True
        else:
            return ""
        # рассчет второй метрики
        metric_2 = ""
        is_pin = ""
        price_more = work_bar['close'] if work_bar['close'] >= work_bar['open'] else work_bar['open']
        price_less = work_bar['close'] if work_bar['close'] <= work_bar['open'] else work_bar['open']
        one_percent = work_bar['bar_metrics']['hl'] / 100
        if price_more < work_bar['low'] + one_percent * 35:
            metric_2 = "u_low"
        elif price_less > work_bar['high'] - one_percent * 35:
            metric_2 = "u_high"
        # компановка метрик
        if metric_1 and (metric_2 == "u_low"):
            is_pin = "up_pin"
        elif metric_1 and (metric_2 == "u_high"):
            is_pin = "down_pin"
        # определение конкретного вида пинбара
        pre_bar = self.chart_slice[-2]
        if is_pin == "up_pin":
            if pre_bar['high'] < work_bar['high']:
                return "extra_up_pin_bar"
            else:
                return "intra_up_pin_bar"
        elif is_pin == "down_pin":
            if pre_bar['low'] > work_bar['low']:
                return "extra_down_pin_bar"
            else:
                return "intra_down_pin_bar"
        return ""

    def check_micro_bar(self):
        """Микробар"""
        hl_last_bar = self.chart_slice[-1]['high'] - self.chart_slice[-1]['low']
        counter = 0
        for bar in self.chart_slice:
            hl_bar = bar['high'] - bar['low']
            if hl_last_bar <= hl_bar:
                counter += 1
        if counter == len(self.chart_slice):
            return True
        return False

    def check_crown_delta(self):
        """Проверяет дельту на варант отношения к толпе"""
        kf = 2
        ask_vol = self.chart_slice[-1]['bar_vol_metrics']['summary_ask_quantity']
        bid_vol = self.chart_slice[-1]['bar_vol_metrics']['summary_bid_quantity']
        delta = ask_vol - bid_vol
        if delta > 0:
            if bid_vol == 0:
                bid_vol = 1
            if abs(ask_vol / bid_vol) >= kf:
                return "crown_delta_up"
        elif delta < 0:
            if ask_vol == 0:
                ask_vol = 1
            if abs(ask_vol / bid_vol) >= kf:
                return "crown_delta_down"

    def check_min_max_vol(self):
        """проверяет текущий бар на самый низкий/высокий объем по отношению к х предыдущим
        (сейчас это длина среза графика)"""
        vol_last_bar = self.chart_slice[-1]['bar_vol_metrics']['summary_bid_ask_quantity']
        counter_max_vol = 0
        counter_min_vol = 0
        for bar in self.chart_slice:
            vol_bar = bar['bar_vol_metrics']['summary_bid_ask_quantity']
            if vol_last_bar <= vol_bar:
                counter_min_vol += 1
            elif vol_last_bar >= vol_last_bar:
                counter_max_vol += 1
        if counter_min_vol == len(self.chart_slice):
            return "min_vol_bar"
        elif counter_max_vol == len(self.chart_slice):
            return "max_vol_bar"
        return False

    def check_divergent_direct_delta(self):
        """определяет бары с разнонаправленными направлением бара и направлением дельты"""
        bar = self.chart_slice[-1]
        if ((bar['bar_metrics']['bar_direct'] == 'down_bar') and
                (bar['bar_vol_metrics']['difference_bid_ask_quantity'] > 0) and
                (bar['bar_vol_metrics']['summary_bid_ask_quantity'] >= 5000)):
            return "divergent_direct_down_delta_up"
        elif ((bar['bar_metrics']['bar_direct'] == 'up_bar') and
                (bar['bar_vol_metrics']['difference_bid_ask_quantity'] < 0) and
                (bar['bar_vol_metrics']['summary_bid_ask_quantity'] >= 5000)):
            return "divergent_direct_up_delta_down"


if __name__ == '__main__':
    # ts = TsPriceAction('', 'SiM1', 60)
    # ts.sub_manager_ts()
    pass


"""
Доработать:
    Получение размера объема одной свечи

"""