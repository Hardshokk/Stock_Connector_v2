from PyQt5 import QtCore, QtWidgets
import common_files.common_functions as cf
import datetime as dt
import pandas as pd
from common_files.trading_script import PositionsOrdersManager


class MainGlassWorker(QtCore.QThread):
    """Родительский класс обработчик стакана"""
    def __init__(self, main_self):
        QtCore.QThread.__init__(self)
        self.running = True
        self.main_self = main_self
        self.pos_man = PositionsOrdersManager(self.main_self.terminal)
        self.startTimer(300000, timerType=QtCore.Qt.VeryCoarseTimer)

    def timerEvent(self, event):
        """Таймер на 5 минут"""
        self.save_df()
        event.accept()

    def save_df(self):
        dn = dt.datetime.now()
        cf.save_object(self.main_self.big_quotes_dict,
                       f"additional_files\\big_quotes_{dn.year}_{dn.month}_{dn.day}.dict")

    def do_in_cycle(self):
        """Переопределяется, расширяет основные возможности цикла"""
        pass

    def run(self):
        while self.running:
            if self.main_self.glass_dict:
                self.do_in_cycle()
                self.sleep(1)
            else:
                self.sleep(10)


class GlassWorker(MainGlassWorker):
    """Основной класс обработчик стакана"""
    def __init__(self, main_self):
        MainGlassWorker.__init__(self, main_self)
        self.big_vol = cf.get_symbol_description_dict()

    def save_log(self, what_save: list, name_log="glass_log"):
        if what_save:
            msg_for_write = "\n".join(what_save)
            self.main_self.save_info_in_log(f"{name_log}_{dt.datetime.now().year}_{dt.datetime.now().month}_"
                                            f"{dt.datetime.now().day}", f"[{msg_for_write}]\n")

    def do_in_cycle(self):
        """Главный управляющий метод класса, переопределяется от родительского
        big_quotes_dict:
        dict_keys(['SRM1', 'GAZP', 'GZM1', 'SBER', 'SiM1'])
                    short_code  price direct  ...      ask      bid        time
        0          SiM1  71721   sell  ...  71717.0  71714.0 2021-06-11 10:15:33.027707
        1          SiM1  71721   sell  ...  71716.0  71714.0 2021-06-11 10:15:34.035126
        """
        self.main_self.signal_edit_clear_s.emit()  # Сигнал очистки поля записи сигналов для отображения
        # поиск всех сигналов крупных заявок которые возможны в данный момент
        signal_list = []
        for symbol in list(self.main_self.glass_dict.keys()):
            for price in list(self.main_self.glass_dict[symbol].keys()):
                var_deal = 'buy' if self.main_self.glass_dict[symbol][price].get('buy') else 'sell'
                if self.main_self.glass_dict[symbol][price][var_deal] >= self.big_vol[symbol]['big_vol_glass']:
                    symbol_info = cf.get_symbol_info(self.big_vol[symbol]['long_code'], self.main_self.terminal)
                    data_dict = {'short_code': symbol, 'price': price, 'direct': var_deal,
                                 'volume': self.main_self.glass_dict[symbol][price][var_deal],
                                 'ask': symbol_info['ask'], 'bid': symbol_info['bid'], 'time': dt.datetime.now()}
                    msg = f"Крупная заявка: {data_dict['short_code']} {data_dict['price']} " \
                          f"{data_dict['direct']} {data_dict['volume']} " \
                          f"**ask {data_dict['ask']}** **bid {data_dict['bid']}** {data_dict['time']}"
                    self.main_self.signal_edit_append_s.emit([msg])  # Передача сигнала на отображение
                    signal_list.append(msg)  # Передача на логирование
                    # запись датафрейма с сигналами крупных объемов
                    if not (symbol in set(self.main_self.big_quotes_dict.keys())):
                        self.main_self.big_quotes_dict[symbol] = pd.DataFrame()
                    self.main_self.big_quotes_dict[symbol] = self.main_self.big_quotes_dict[symbol].append(
                        pd.DataFrame({key: [value] for key, value in data_dict.items()}))
        self.save_log(signal_list)





