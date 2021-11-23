from ts.general_ts_finder import GeneralTsFinder
import datetime as dt
from common_files import common_functions as cf


class TsRoofLine(GeneralTsFinder):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_roof_line'
        self.qv_bars = 10

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        # после написания ТС сюда занести функции необходимые для работы ТС.
        print("Зашел в TsRoofLine")
        signals_list = []
        signals_list.append(self.calculate_roof_line())
        return signals_list

    def calculate_roof_line(self):
        """Получает сигнал"""
        print("Начал вычисление в TsRoofLine")
        bars = self.mongo.get_qv_last_bars(self.symbol, self.tf_sec, self.qv_bars)
        if self.symbol in set(list(self.main_self.big_quotes_dict.keys())):
            df_big_app = self.main_self.big_quotes_dict[self.symbol]
            counter = 0
            for bar in bars:
                result = df_big_app[(df_big_app['time'] >= bar['time_open']) & (df_big_app['time'] <= bar['time_close'])]
                if not result.empty:
                    counter += 1
            print(f"TsRoofLine: roof_line_len: {counter}, time_start: {bars[0]['time_open']}")
            if counter == self.qv_bars:
                dn = dt.datetime.now()
                if dn.hour <= 18:
                    return self.form_signal(func_var='alert')
                else:
                    return {}
        else:
            print(f"Roof TS: Символа {self.symbol} нет в словаре больших заявок. "
                  f"Список тех кто есть: {set(list(self.main_self.big_quotes_dict.keys()))}")
        return {}


if __name__ == '__main__':
    # ts = TsRoofLine('', 'SiM1', 60)
    # ts.sub_manager_ts()
    pass


"""
Доработать:
    Получение размера объема одной свечи

"""