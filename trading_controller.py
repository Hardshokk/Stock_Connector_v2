import os
import sys
from functools import partial
import ctypes
import datetime as dt

from PyQt5 import QtCore, QtWidgets
from trading_controller_files.general_classies import TradingControllerGeneral
import xml.dom.minidom as xml_dom
from PyQt5 import QtWidgets
from common_files import postgres
import common_files.common_functions as cf
from server import connector_transaq, queue_workers
from common_files.mongo import ConnectorMongo
from charts.general_chart import WindowChart
from charts.chart_candle_glass import ChartUpdater
# Обработчики поступающих сигналов в основную программу
from trading_controller_files.signal_workers import DealSignalWorker
# Обработчики чартов
from trading_controller_files.chart_workers import ChartUpdateWorker
# Обработчики стратегий - поток поисковика сигналов и поток обработчика сигналов
from trading_controller_files.ts_imports import *
# Обработчики стакана
from trading_controller_files.glass_workers import GlassWorker

directory_save_logs = "server\\server_files"


def save_info(name_obj, var_write, what_save):
    """функция от accept_callback"""
    with open(name_obj, var_write) as f:
        f.write(what_save)
        f.write('\n')


callback_func = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_char_p)
@callback_func
def accept_callback(data):
    norm_data = data.decode(encoding='utf-8')
    main_elem = xml_dom.parseString(norm_data).childNodes[0]
    name_data = main_elem.nodeName
    if name_data == 'ticks':
        print(f"Сервер: Получаю порцию тиков. {dt.datetime.now()}")
        raw_tick_queue.send_in_queue(norm_data)
    elif name_data == 'quotes':
        print(f"Сервер: Получаю порцию стакана. {dt.datetime.now()}")
        raw_quotes_queue.send_in_queue(norm_data)
    elif name_data == 'server_status':
        print("Сервер: Это сервер_статус: ", norm_data)
        window.server.connect_status = cf.get_bool_value_from_str(main_elem.attributes['connected'].value)
        save_info(f"{directory_save_logs}\\server_status.txt", "a+", norm_data)
    elif name_data == 'news_header':
        save_info(f"{directory_save_logs}\\news.txt", "a+", norm_data)
    elif name_data == 'markets':
        save_info(f"{directory_save_logs}\\markets.txt", "w", norm_data)
    elif name_data == 'boards':
        save_info(f"{directory_save_logs}\\boards.txt", "w", norm_data)
    else:
        save_info(f"{directory_save_logs}\\msg.txt", "w", norm_data)
    return True if len(data) > 1 else False


connector_transaq.tr_lib.SetCallback(accept_callback)


def get_tick_dict(ticks):
    """обрабатывает тик из первой очереди и подает его во вторую очередь на запись в бд"""
    document = xml_dom.parseString(ticks).getElementsByTagName("tick")
    for tick in document:
        tick_dict = {}
        for name_edit in ['seccode', 'tradeno', 'tradetime', 'price', 'quantity', 'buysell', 'openinterest']:
            element = tick.getElementsByTagName(name_edit)[0]
            text = element.firstChild.data
            tick_dict[name_edit] = text.strip()
        db_write_tick_queue.send_in_queue(tick_dict)


def get_quotes_dict(quotes):
    """обрабатывает изменения стакана из первой очереди и подает его на обновление словаря"""
    document = xml_dom.parseString(quotes).getElementsByTagName("quote")
    for quote in document:
        tick_dict = {}
        for name_edit in ['board', 'seccode', 'price', 'yield', 'buy', 'sell']:
            try:
                element = quote.getElementsByTagName(name_edit)[0]
            except IndexError:
                continue
            text = element.firstChild.data
            if (name_edit == 'buy') or (name_edit == 'sell'):
                tick_dict[name_edit] = int(text.strip())
            else:
                tick_dict[name_edit] = text.strip()
        var = 'buy' if tick_dict.get('buy') else 'sell'
        if not glass_dict.get(tick_dict['seccode']):
            glass_dict[tick_dict['seccode']] = {
                f"{tick_dict['price']}": {f"{var}": tick_dict[var]}
            }
        else:
            glass_dict[tick_dict['seccode']][tick_dict['price']] = {f"{var}": tick_dict[var]}


class TradingControllerMain(TradingControllerGeneral):
    """Основное окно программы. Главный управляющий класс"""
    # Принимаемые сигналы
    deal_signal = QtCore.pyqtSignal(dict)

    signal_edit_clear_s = QtCore.pyqtSignal()
    signal_edit_append_s = QtCore.pyqtSignal(list)

    def __init__(self):
        TradingControllerGeneral.__init__(self)
        # Наборы данных
        self.symbols_list_for_tick = [symbol['short_code'] for symbol in cf.symbols_collect['fuchers'][: 3]]
        self.symbols_list_for_quotes = {'fuchers': [symbol['short_code'] for symbol in
                                                    cf.symbols_collect['fuchers'][: 3]],
                                        'stocks': [symbol['short_code'] for symbol in cf.symbols_collect['stocks']]}
        print("На тики: ", self.symbols_list_for_tick, "На стакан: ", self.symbols_list_for_quotes)
        self.main_set_symbol_tf = set()  # выжимка тюплов символ таймфрейм

        # подключаю сервер
        self.server = connector_transaq.ConnectController(self, raw_tick_queue, db_write_tick_queue, raw_quotes_queue)
        self.server.start()

        # регистрация ТС и ее обработчика
        self.ts_dict = {
            # 'ts_catch': {"signal_finder": TsCatchTread(self), 'worker': TsCatchWorker},
            'ts_absorbing_bar': {"signal_finder": TsAbsorbingBarThread(self), 'worker': TsAbsorbingBarWorker},
            'ts_roof_line': {"signal_finder": TsRoofLineThread(self), 'worker': TsRoofLineWorker},
            #+'ts_price_action': {"signal_finder": TsPriceActionThread(self), 'worker': TsPriceActionWorker},
            # 'ts_day_points': {"signal_finder": TsDayPointsThread(self), 'worker': TsDayPointsWorker},
            #+'ts_zones_finder': {"signal_finder": TsZonesFinderThread(self), 'worker': TsZonesFinderWorker},
        }
        # создаю главного распределительного обработчика поступающих сигналов от ТС
        self.signal_worker = DealSignalWorker(self)
        self.signal_worker.start()
        self.deal_signal.connect(partial(self.signal_worker.append_signal_in_queue, self.deal_signal))

        # создаю (symbol, tf) кортежи для добавления в основной набор для составления чартов
        self.get_symbol_tf_tuples()
        print("Набор символов для торговли и графиков: ", self.main_set_symbol_tf)

        # набор потоков формирующих чарт базу монго
        self.charts_treads_dict = {}  # набор активных потоков строящих графики
        for symbol, tf in self.main_set_symbol_tf:
            if not self.charts_treads_dict.get(symbol):
                self.charts_treads_dict[symbol] = {}
            self.charts_treads_dict[symbol][tf] = ChartUpdateWorker(symbol, tf)
            self.charts_treads_dict[symbol][tf].start()

        # Запускаю все стратегии
        for ts in self.ts_dict.keys():
            self.ts_dict[ts]['signal_finder'].start()

        # регистрация обработчика стакана
        self.glass_dict = glass_dict
        dn = dt.datetime.now()
        self.path_big_quotes = f"additional_files\\big_quotes_{dn.year}_{dn.month}_{dn.day}.dict"
        if os.path.isfile(self.path_big_quotes):
            self.big_quotes_dict = cf.load_object(self.path_big_quotes)
        else:
            self.big_quotes_dict = {}
        self.glass_worker_tread = GlassWorker(self)
        self.glass_worker_tread.start()
        self.signal_edit_clear_s.connect(self.clear_signal_edit)
        self.signal_edit_append_s.connect(partial(self.append_data_signal_edit, self.signal_edit_append_s))

        # создаю потоки на все символы и таймфреймы для создания графиков основная версия
        self.mdi_objects = {}
        self.charts_updaters = {}
        for symbol, tf in self.main_set_symbol_tf:
            self.mdi_objects[f"{symbol}_{tf}"] = self.charts_mdi_area.addSubWindow(WindowChart(main_self=self, symbol=symbol,
                                                                                         tf_sec=tf))
            self.mdi_objects[f"{symbol}_{tf}"].setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.charts_updaters[f"{symbol}_{tf}"] = ChartUpdater(self, self.mdi_objects[f"{symbol}_{tf}"], symbol, tf)
            self.charts_updaters[f"{symbol}_{tf}"].start()

    def create_chart(self, symbol, tf):
        if self.charts_updaters.get(f"{symbol}_{tf}"):
            self.charts_updaters[f"{symbol}_{tf}"].terminate()
        self.mdi_objects[f"{symbol}_{tf}"] = self.charts_mdi_area.addSubWindow(WindowChart(main_self=self, symbol=symbol,
                                                                                     tf_sec=tf))
        self.charts_updaters[f"{symbol}_{tf}"] = ChartUpdater(self, self.mdi_objects[f"{symbol}_{tf}"], symbol, tf)
        self.charts_updaters[f"{symbol}_{tf}"].start()
        self.mdi_objects[f"{symbol}_{tf}"].widget().show()

    def append_data_signal_edit(self, *data):
        """обработчик вывода сигнала в signal_edit"""
        self.signal_edit.append(data[1][0])

    def clear_signal_edit(self):
        """обработчик сигнала очистки signal_edit"""
        self.signal_edit.clear()

    def closeEvent(self, e):
        print("***Начинаю остановку потоков, для дальнейшего выключения программы*** ", dt.datetime.now())
        # Останавливаю все потоки стратегий
        self.hide()
        for ts in self.ts_dict.keys():
            self.ts_dict[ts]['signal_finder'].running = False
        # Останавливаю потоки сборщиков чартов
        for symbol, tf in self.main_set_symbol_tf:
            # self.mongo_charts_treads_dict[symbol][tf].running = False
            self.charts_treads_dict[symbol][tf].running = False
        # Останавливаю очередь сигналов
        self.signal_worker.queue.close()
        # Останавливаю обработчика сигналов
        self.signal_worker.running = False
        self.glass_worker_tread.running = False
        print("***Дошел до остановки сервера*** ", dt.datetime.now())
        self.server.stop_connector()
        print("***Остановка всех потоков завершена. Закрываю программу.*** ", dt.datetime.now())
        e.accept()

    def get_symbol_tf_tuples(self):
        for ts in self.ts_dict.keys():
            for symbol in self.ts_dict[ts]['signal_finder'].all_symbols_list:
                for tf in self.ts_dict[ts]['signal_finder'].tf_sec_list:
                    if symbol and tf:
                        self.main_set_symbol_tf.add((symbol, tf))
        for symbol in self.symbols_list_for_tick:
            self.main_set_symbol_tf.add((symbol, 60))


if __name__ == '__main__':
    db = postgres.TickSaver()

    db_write_tick_queue = queue_workers.WorkerQueue(daemon=True, func_worker=db.save_data)

    raw_tick_queue = queue_workers.WorkerQueue(daemon=True, func_worker=get_tick_dict)

    raw_quotes_queue = queue_workers.WorkerQueue(daemon=True, func_worker=get_quotes_dict)

    glass_dict = {}

    app = QtWidgets.QApplication([])
    window = TradingControllerMain()
    window.show()
    sys.exit(app.exec_())

"""
Основные правила написания ТС:
-Каждый поток и очередь должны обязательно иметь атрибут экземпляра класса running = True/False
"""