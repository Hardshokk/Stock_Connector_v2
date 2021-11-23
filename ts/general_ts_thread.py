import traceback
import datetime as dt
from PyQt5 import QtCore


class GeneralTsThread(QtCore.QThread):
    """Класс родитель классов потоков"""
    def __init__(self, main_self):
        QtCore.QThread.__init__(self)
        self.running = True
        self.main_self = main_self
        self.all_symbols_list = ["SiU1", "SRU1"]  # , "GZU1"]
        self.tf_sec_list = [60]
        self.class_ts = None  # Переопределяется

    @staticmethod
    def main_thread_dict_init(symbol_list, tf_sec_list, ts_class, main_self):
        """создает словарь с экземплярами классов стратегии разделенные на символы и таймфреймы"""
        main_dict = {}
        for symbol in symbol_list:
            main_dict[symbol] = {}
            for tf_sec in tf_sec_list:
                main_dict[symbol][tf_sec] = ts_class(main_self, symbol, tf_sec)
        return main_dict

    @staticmethod
    def how_many_wait(second_interval):
        """Определяет сколько секунд нужно подождать до начала нового периода"""
        dn = dt.datetime.now()
        d_fut = dn + dt.timedelta(seconds=second_interval)
        wait_sec = (dt.datetime(d_fut.year, d_fut.month, d_fut.day, d_fut.hour, d_fut.minute, 4) - dn).seconds
        return wait_sec

    def run(self):
        main_thread_dict = self.main_thread_dict_init(self.all_symbols_list, self.tf_sec_list,
                                                      self.class_ts, self.main_self)
        while self.running:
            print(f'Начинаю новый цикл {dt.datetime.now()}')
            for symbol in self.all_symbols_list:
                for tf_sec in self.tf_sec_list:
                    try:
                        signal = main_thread_dict[symbol][tf_sec].manager_ts()  # Стандартный режим
                        # signal = main_thread_dict[symbol][tf_sec].test_ts()  # Режим тестирования
                    except Exception as e:
                        with open("logs\\ts_log.log", "a+") as f:
                            f.write(f"Ошибка: {e}")
                            f.writelines(traceback.format_exc())
                            f.write("\n\n")
                        signal = None
                    if isinstance(signal, dict):
                        if signal:
                            self.main_self.deal_signal.emit(signal)
                    elif isinstance(signal, list):
                        for sub_signal in signal:
                            if sub_signal:
                                self.main_self.deal_signal.emit(sub_signal)
            self.sleep(self.how_many_wait(60))


if __name__ == '__main__':
    pass
