from ts.general_ts_finder import GeneralTsFinder
import datetime as dt
import common_files.common_functions as cf


class TsAbsorbingBar(GeneralTsFinder):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_absorbing_bar'
        self.symbol_description = cf.get_symbol_description_dict()

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        # после написания ТС сюда занести функции необходимые для работы ТС.
        signals_list = []
        signals_list.append(self.get_data())
        signals_list.append(self.get_interest_signal())

        return signals_list

    def get_interest_signal(self):
        """Получаю сигнал о сильном отклонении открытого интереса"""
        big_oi = self.symbol_description[self.symbol]['big_oi']
        if self.bar_vol_metrics.get('interest_delta'):
            print("***Interest_delta***", self.symbol, "  ", self.bar_vol_metrics['interest_delta'])
            if self.bar_vol_metrics['interest_delta'] >= big_oi:
                return self.form_signal(func_var='alert', my_msg="Interest Delta signal variant Open")
            elif self.bar_vol_metrics['interest_delta'] <= -big_oi:
                return self.form_signal(func_var='alert', my_msg="Interest Delta signal variant Close")
        else:
            print("Ошибка получения открытого интереса с бара. Нужно проверить.")
        return {}

    def get_data(self):
        """Получает сигнал"""
        big_bar_vol = self.symbol_description[self.symbol]['big_bar_vol']
        bar_vol = self.bar_vol_metrics['summary_bid_ask_quantity']
        bar_delta = self.bar_vol_metrics['difference_bid_ask_quantity']
        if bar_vol > big_bar_vol:
            kf = abs(bar_vol / bar_delta)
            if kf >= 15:
                return self.form_signal(func_var='alert')
        return {}

    def fullness_delta(self):
        """Считает на сколько процентов дельта равна объему, пока отключена"""
        day_number = 13
        chart = self.mongo.get_range_bars_time(self.symbol, self.tf_sec, dt.datetime(2021, 4, day_number),
                                               dt.datetime(2021, 4, day_number, 23, 51))
        signal_list = []
        for bar in chart:
            vol = bar['bar_vol_metrics']['summary_bid_ask_quantity']
            delta = bar['bar_vol_metrics']['difference_bid_ask_quantity']
            percent = abs((delta * 100) / vol)
            if percent <= 2:
                signal_list.append(bar)
        for bar in signal_list:
            print(bar['time_open'])


if __name__ == '__main__':
    # ts = TsAbsorbingBar('', 'SiM1', 60)
    # ts.sub_manager_ts()
    pass


"""
Доработать:
    Получение размера объема одной свечи

"""