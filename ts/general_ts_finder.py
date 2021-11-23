import time
from common_files.mongo import ConnectorMongo


class GeneralTsFinder:
    def __init__(self, main_self, symbol, tf_sec):
        self.mongo = ConnectorMongo()
        self.ts_name = ""  # Переопределяется
        self.main_self = main_self
        self.symbol = symbol
        self.tf_sec = tf_sec
        self.strategy_metrics = {}
        self.cluster_list = None
        self.cluster_data = None
        self.bar_metrics = None
        self.bar_vol_metrics = None
        self.start_len_chart = self.mongo.get_len_collection(self.symbol, self.tf_sec)
        self.len_chart_now = self.mongo.get_len_collection(self.symbol, self.tf_sec)
        self.last_bar = self.mongo.get_last_bar(self.symbol, self.tf_sec)
        while not self.last_bar.get('time_open'):
            print("Нет последнего бара ожидаю историю.")
            time.sleep(60)
            self.last_bar = self.mongo.get_last_bar(self.symbol, self.tf_sec)
        self.time_scheduler_last_bar = self.last_bar['time_open']

    def get_last_bar_from_chart(self):
        """функция обновляющая данные для рассчета стратегии"""
        self.last_bar = self.mongo.get_last_bar(self.symbol, self.tf_sec)
        print(f"Ласт бар {self.symbol} {self.last_bar['time_open']}")
        self.cluster_list = self.last_bar['cluster_list']
        self.cluster_data = self.last_bar['cluster_data']
        self.bar_metrics = self.last_bar['bar_metrics']
        self.bar_vol_metrics = self.last_bar['bar_vol_metrics']

    def wait_new_bar(self):
        """Контролирует появление нового бара"""
        if self.start_len_chart == self.len_chart_now:
            print(f"Длина чарта {self.symbol} {self.len_chart_now} на старте равна текущей длине. "
                  f"Ожидаю появления нового бара. Время ласт_бара: {self.last_bar['time_open']}")
            self.len_chart_now = self.mongo.get_len_collection(self.symbol, self.tf_sec)
            time.sleep(1)
            return True
        return False

    def sub_manager_ts(self):
        """Переопределятся для получения сигнала из конкретной ТС"""
        pass

    def test_ts(self):
        """Включается при тестировании новой ТС, убирает временные фильтры и постояно прокидывает сигналы"""
        self.get_last_bar_from_chart()
        return self.sub_manager_ts()

    # основная функция
    def manager_ts(self):
        """основной управляющий метод"""
        if not self.wait_new_bar():
            self.get_last_bar_from_chart()
            if self.time_scheduler_last_bar < self.last_bar['time_open']:
                self.time_scheduler_last_bar = self.last_bar['time_open']
                return self.sub_manager_ts()
            return ""
        return ""

    # основная функция
    def form_signal(self, func_var, direct="", my_msg=""):
        """основная функция определяющая поля сигнала
        direct может быть любым значением, главное чтобы это значение принималось обработчиком конкретной ТС
        func_var может быть значением deal или alert
        """
        assert (func_var == 'deal') or (func_var == 'alert'), "Неверно указан вариант функции"
        msg = f"{self.ts_name} {self.symbol} {self.tf_sec} {direct} {my_msg}"
        return {'symbol': self.symbol, 'ts_name': self.ts_name, 'direct': direct, 'tf_sec': self.tf_sec,
                'signal_msg': msg, 'func_variant': func_var, 'my_msg': my_msg}

    # основная функция
    def form_signal_list(self, signals_dict):
        """Функция формирует список сигналов, данный список нужно вернуть в поток для отправки сигналов"""
        signals = []
        for key, value in signals_dict.items():
            if value:
                signals.append(self.form_signal('alert', my_msg=f"{key} {value}"))
        return signals


if __name__ == '__main__':
    pass
