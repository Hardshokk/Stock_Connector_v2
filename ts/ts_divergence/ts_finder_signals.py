from ts.general_ts_finder import GeneralTsFinder
import datetime as dt


class TsDivergence(GeneralTsFinder):
    """Стратегия дивергенции кумдельты и свечного графика"""
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_divergence'
        self.cum_price_chart = []

    def generate_signal(self):
        pass

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        # после написания ТС сюда занести функции необходимые для работы ТС.
        return self.generate_signal()

    def get_cum_price_list(self, time_start=dt.datetime(dt.datetime.now().year, dt.datetime.now().month,
                                                        dt.datetime.now().day), time_finish=dt.datetime.now()):
        """1. Получает бары из монги, подгружает их в кум дельта чарт"""
        mongo_list = self.mongo.get_range_bars_time(self.symbol, self.tf_sec, time_start, time_finish)
        chart_list = list(mongo_list)
        if not self.cum_price_chart:
            cum_delta = 0.
            tm_last_bar_in_cum_chart = time_start
        else:
            cum_delta = self.cum_price_chart[-1]['cum_delta']
            tm_last_bar_in_cum_chart = self.cum_price_chart[-1]['time_open']
        for bar in chart_list:
            if bar['time_open'] <= tm_last_bar_in_cum_chart:
                continue
            prices = {'high': bar['high'], 'low': bar['low'], 'close': bar['close'], 'open': bar['open']}
            delta = bar['bar_vol_metrics']['difference_bid_ask_quantity']
            cum_delta += delta
            self.cum_price_chart.append({'cum_delta': cum_delta, 'prices': prices, 'delta': delta,
                                         'time_open': bar['time_open'], 'fractal_high': False, 'fractal_low': False,
                                         'cum_fractal_high': False, 'cum_fractal_low': False})

    def assign_fractals(self, fractal_range, fractal_price=False, fractal_cum=False):
        """Присваивает свечам фракталам первичное значение фракталов с указанным режением"""
        assert not (fractal_price and fractal_cum) or (not (not fractal_price and not fractal_cum)), \
            "Указаны неверные параметры для рассчета фракталов кумдельты и цены"
        if fractal_range * 2 + 1 > len(self.cum_price_chart):
            print("Посчитать фракталы невозможно всвязи большой длинной диапазона фрактала или маленькой длиной чарта")
            return
        key_fractal_high = 'fractal_high'
        key_fractal_low = 'fractal_low'
        if fractal_cum:
            key_fractal_high = 'cum_fractal_high'
            key_fractal_low = 'cum_fractal_low'
        for index in range(fractal_range, len(self.cum_price_chart)-fractal_range):
            counter_high = 0
            counter_low = 0
            for i in range(index - fractal_range, index + fractal_range):
                if fractal_price:
                    if self.cum_price_chart[i]['prices']['high'] <= self.cum_price_chart[index]['prices']['high']:
                        counter_high += 1
                    if self.cum_price_chart[i]['prices']['low'] >= self.cum_price_chart[index]['prices']['low']:
                        counter_low += 1
                if fractal_cum:
                    if self.cum_price_chart[i]['cum_delta'] <= self.cum_price_chart[index]['cum_delta']:
                        counter_high += 1
                    if self.cum_price_chart[i]['cum_delta'] >= self.cum_price_chart[index]['cum_delta']:
                        counter_low += 1
            if counter_high == fractal_range * 2:
                self.cum_price_chart[index][key_fractal_high] = True
            if counter_low == fractal_range * 2:
                self.cum_price_chart[index][key_fractal_low] = True
            if self.cum_price_chart[index][key_fractal_high] and self.cum_price_chart[index][key_fractal_low]:
                self.cum_price_chart[index][key_fractal_high] = False
                self.cum_price_chart[index][key_fractal_low] = False

    def _assign_value_fractal(self, fractal_direct, index, left_index, right_index):
        """от update_fractals"""
        if fractal_direct == 'fractal_high':
            if ((self.cum_price_chart[index]['prices']['high'] >= self.cum_price_chart[left_index]['prices']['high']) and
                    (self.cum_price_chart[index]['prices']['high'] >= self.cum_price_chart[right_index]['prices']['high'])):
                self.cum_price_chart[left_index][fractal_direct] = False
                self.cum_price_chart[right_index][fractal_direct] = False
        elif fractal_direct == 'fractal_low':
            if ((self.cum_price_chart[index]['prices']['low'] <= self.cum_price_chart[left_index]['prices']['low']) and
                    (self.cum_price_chart[index]['prices']['low'] <= self.cum_price_chart[right_index]['prices']['low'])):
                self.cum_price_chart[left_index][fractal_direct] = False
                self.cum_price_chart[right_index][fractal_direct] = False

    def _update_fractals(self, fractal_direct):
        """common_update_fractals, проводит рассчет у каких баров снять статус фрактала"""
        for index in range(1, len(self.cum_price_chart)):
            left_index = index - 1
            right_index = index + 1
            while not self.cum_price_chart[left_index][fractal_direct]:
                left_index -= 1
                if left_index < 0:
                    break
            while not self.cum_price_chart[right_index][fractal_direct]:
                right_index += 1
                if right_index > len(self.cum_price_chart)-1:
                    right_index = -1
                    break
            if right_index == -1:
                break
            if left_index == -1:
                continue
            self._assign_value_fractal(fractal_direct, index, left_index, right_index)

    def common_update_fractals(self, qv_update):
        for i in range(qv_update):
            self._update_fractals('fractal_high')
            self._update_fractals('fractal_low')

    def test(self):
        for i in self.cum_price_chart:
            if i['fractal_high']:
                print(f"high {i['time_open']}")
        for i in self.cum_price_chart:
            if i['fractal_low']:
                print(f"low {i['time_open']}")
        for i in self.cum_price_chart:
            if i['cum_fractal_high']:
                print(f"high cum {i['time_open']}")
        for i in self.cum_price_chart:
            if i['cum_fractal_low']:
                print(f"low cum {i['time_open']}")
        for i in self.cum_price_chart:
            if i['cum_fractal_high'] and i['fractal_high']:
                print(f"high cum price {i['time_open']}")
        for i in self.cum_price_chart:
            if i['cum_fractal_low'] and i['fractal_low']:
                print(f"low cum price {i['time_open']}")


if __name__ == '__main__':
    """удалить после окончания разработки"""
    dt_now = dt.datetime.now()
    start = dt.datetime(dt_now.year, dt_now.month, dt_now.day) - dt.timedelta(days=0)
    finish = dt.datetime(dt_now.year, dt_now.month, dt_now.day)
    ts = TsDivergence('', 'SiU1', 60)
    ts.get_cum_price_list(time_start=start)
    ts.assign_fractals(5, fractal_price=True)
    ts.assign_fractals(5, fractal_cum=True)
    ts.common_update_fractals(0)
    ts.test()
    pass
