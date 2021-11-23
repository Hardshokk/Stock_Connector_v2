import sys
from functools import partial
from charts.general_chart import *
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
import datetime as dt
import pandas as pd
import time
from common_files.postgres import GetTicks
from common_files.trading_script import PositionsOrdersManager
import common_files.common_functions as cf
from common_files.mongo import ConnectorMongo
pd.set_option('max_columns', 100)
pd.set_option('max_rows', 1000)


class ChartUpdater(QtCore.QThread):
    def __init__(self, main_self, sub_widget, symbol, tf_sec):
        QtCore.QThread.__init__(self)
        self.running = True
        self.sub_widget = sub_widget.widget()
        self.chart = sub_widget.widget()
        self.main_self = main_self
        self.symbol = symbol
        self.tf_sec = tf_sec
        self.chart_view_box = self.sub_widget.getPlotItem().getViewBox()
        if not cf.symbol_is_terminal_variant(self.symbol):
            self.symbol_terminal = cf.get_symbol_format_terminal(self.symbol)
        else:
            self.symbol_terminal = self.symbol
        self.offset = 0
        self.mongo = ConnectorMongo()
        self.postgres = GetTicks()
        self.len_start_chart = 50
        self.last_minute = -1
        self.bars_data = self.mongo.get_qv_last_bars(self.symbol, self.tf_sec, self.len_start_chart)
        self.graphic_data = []
        self.run_ = False
        self.count = 0
        self.pre_candle_set_for_del = set()
        self.pre_quotes_set_for_del = set()
        self.pre_pre_quotes_set_for_del = set()
        self.last_now_bar = {'max_price': 0, 'min_price': 0}
        self.last_now_quotes = {'vol_max': 0, 'vol_last': 0}
        dn = dt.datetime.now()
        try:
            self.quotes_df = cf.load_object(f"additional_files\\big_quotes_{dn.year}_{dn.month}_{dn.day-1}.dict")
        except FileNotFoundError:
            print("Файл не найден")
            self.quotes_df = {}
        # Загружаем историю до текущего момента
        self.load_chart()

    def load_chart(self):
        """первичная загрузка графика"""
        while self.offset < len(self.bars_data) - 1:
            self.print_all()

    def get_max_min(self, df):
        """Получение макс мин цен текущего бара"""
        return df['price'].max(), df['price'].min()

    def append_graphic_data(self):
        """добавление бара на чарт"""
        self.graphic_data.append({'objects': {'bar': self.bars_data[self.offset]},
                                  'x': self.offset,
                                  'time_x_start': self.bars_data[self.offset]['time_open'],
                                  'time_x_finish': self.bars_data[self.offset]['time_close'],
                                  'tf_sec': self.bars_data[self.offset]})
        # отрисовка исторических баров на чарте
        print("Добавиляю CandlesItem - append_graphic_data")
        create_bar = CandlesItem(self.chart, {'data_bar': self.graphic_data[-1]})
        self.sub_widget.signal_append_item_on_chart.emit({'symbol': self.symbol, 'tf': self.tf_sec, 'object': create_bar})
        # self.chart.addItem(create_bar)

    def append_now_bar(self):
        """отрисовка текущего бара на графике"""
        df_ticks, time_start = self.get_ticks()
        if df_ticks.empty:
            max_price = self.graphic_data[-1]['objects']['bar']['close']
            min_price = self.graphic_data[-1]['objects']['bar']['close']
        else:
            max_price, min_price = self.get_max_min(df_ticks)
        print(f"{self.symbol} ", "offset ", self.offset)
        pre_dict = {'data_bar': {'objects': {'bar': {'high': max_price, 'low': min_price}}, 'x': self.offset + 1,
                                 'time_x_start': self.bars_data[self.offset]['time_open'] +
                                                 dt.timedelta(seconds=self.tf_sec),
                                 'time_x_finish': self.bars_data[self.offset]['time_open'] + (
                                         (dt.timedelta(seconds=self.tf_sec) * 2) -
                                         dt.timedelta(milliseconds=1))}}
        if (self.last_now_bar['max_price'] != max_price) or (self.last_now_bar['min_price'] != min_price):
            print("Добавиляю PreCandlesItem - append_now_bar")
            create_bar = PreCandlesItem(self.chart, pre_dict)
            self.del_pre_candle_from_chart()
            self.sub_widget.signal_append_item_on_chart.emit(
                {'symbol': self.symbol, 'tf': self.tf_sec, 'object': create_bar})
            self.pre_candle_set_for_del.add(create_bar)
            self.last_now_bar['max_price'] = max_price
            self.last_now_bar['min_price'] = min_price
        return pre_dict

    def get_ticks(self):
        """Получение тиков из postgres"""
        # получение тиков, прикрутка их к аск бид, отрисовка текущего состояния
        time_start = self.graphic_data[-1]['time_x_start']
        time_delta = dt.timedelta(seconds=self.tf_sec)
        out_bar_ticks = self.postgres.get_ticks_from_postgres(self.symbol, time_start + time_delta, time_start +
                                                              ((time_delta * 2) - dt.timedelta(milliseconds=1)))
        return out_bar_ticks, time_start

    def draw_bar_glass(self):
        """Нарисовать стакан на истории"""
        if self.symbol in list(self.main_self.big_quotes_dict.keys()):
            # Точная отрисовка истории
            elem = self.main_self.big_quotes_dict[self.symbol]
            df_slice = elem[(elem['time'] >= self.graphic_data[-1]['time_x_start']) &
                            (elem['time'] < self.graphic_data[-1]['time_x_finish'])]
            if not df_slice.empty:
                print("Добавиляю QuotesLines - draw_bar_glass")
                create_quotes_lines = QuotesLines(self.chart, self, {'data_bar': self.graphic_data[-1],
                                                                     'df_quotes_slice': df_slice})
                self.sub_widget.signal_append_item_on_chart.emit(
                    {'symbol': self.symbol, 'tf': self.tf_sec, 'object': create_quotes_lines})

    def draw_history_glass(self):
        """Нарисовать текущий стакан"""
        if self.graphic_data:
            if self.symbol in list(self.quotes_df.keys()):
                # Отрисовка стакана
                elem = self.quotes_df[self.symbol]
                df_slice = elem[(elem['time'] >= self.graphic_data[-1]['time_x_start']) &
                                (elem['time'] < self.graphic_data[-1]['time_x_finish'])]
                if not df_slice.empty:
                    print("Добавиляю QuotesLines - draw_history_glass")
                    create_quotes_lines = QuotesLines(self.chart, self,  {'data_bar': self.graphic_data[-1],
                                                                          'df_quotes_slice': df_slice})
                    # self.chart.addItem(create_quotes_lines)
                    self.sub_widget.signal_append_item_on_chart.emit(
                        {'symbol': self.symbol, 'tf': self.tf_sec, 'object': create_quotes_lines})

    def draw_now_glass(self, pre_dict):
        """Нарисовать текущий стакан"""
        if self.symbol in list(self.main_self.big_quotes_dict.keys()):
            # Отрисовка будущего стакана
            elem = self.main_self.big_quotes_dict[self.symbol]
            df_slice = elem[(elem['time'] >= pre_dict['data_bar']['time_x_start']) &
                            (elem['time'] < pre_dict['data_bar']['time_x_finish'])]
            if not df_slice.empty:
                # self.last_now_quotes[]
                self.pre_quotes_set_for_del.update(self.pre_pre_quotes_set_for_del)
                self.pre_pre_quotes_set_for_del.clear()
                print("Добавиляю PreQuotesLines - draw_now_glass")
                print(f"Количество объектов на чарте до: {len(self.chart.getPlotItem().getViewBox().allChildren())}")
                create_quotes_lines = PreQuotesLines(self.chart, self, {'data_bar': pre_dict['data_bar'],
                                                                        'df_quotes_slice': df_slice})
                print(f"Количество объектов на чарте после : {len(self.chart.getPlotItem().getViewBox().allChildren())}")
                self.del_pre_quotes_from_chart()
                # self.chart.addItem(create_quotes_lines)
                self.sub_widget.signal_append_item_on_chart.emit(
                    {'symbol': self.symbol, 'tf': self.tf_sec, 'object': create_quotes_lines})
                self.pre_quotes_set_for_del.add(create_quotes_lines)
                print(f"Количество объектов на чарте после дропа: {len(self.chart.getPlotItem().getViewBox().allChildren())}")

    def _get_bars_data(self):
        """от get_last_data_from_bd"""
        start_time = self.bars_data[-1]['time_open'] + dt.timedelta(seconds=self.tf_sec)
        finish_time = dt.datetime.now()
        bars_data = self.mongo.get_range_bars_time(self.symbol, self.tf_sec, start_time, finish_time)
        return bars_data

    def get_last_data_from_bd(self):
        """обновляю основной список с барами из базы данных"""
        if self.last_minute != dt.datetime.now().minute:
            len_bars_data = len(self.bars_data)
            bars_data = self._get_bars_data()
            print("прошел точку 1")
            if bars_data:
                self.bars_data.extend(bars_data)
                if len_bars_data < len(self.bars_data):
                    self.last_minute = dt.datetime.now().minute
                print("прошел точку 2")
            else:
                print("прошел точку 3")
                dn = dt.datetime.now()
                if (dn.isoweekday() == 6) or (dn.isoweekday() == 7):
                    print("Сегодня выходной. Рынок не работает.")
                    return
                elif dn.hour < 7:
                    print("Сейчас ночной час. Рынок не работает.")
                    return
                else:
                    print("Не могу получить новую историю. Вероятно она не загружена или не существует.")
        else:
            print("Ожидаю обновления минуты для получения истории")

    # def clear_all_pre_candle_obj(self):
    #     """От сигнала. Убирает с графика все объекты pre_candle"""
    #     all_objects = self.chart.getPlotItem().getViewBox().allChildren()
    #     for obj in all_objects:
    #         if isinstance(obj, PreCandlesItem) or isinstance(obj, PreQuotesLines) or isinstance(obj, PreMyTextItem):
    #             self.chart.removeItem(obj)

    def del_pre_candle_from_chart(self):
        """Удаление пребаров"""
        print(f"Длина pre_candle_set = {self.pre_candle_set_for_del}")
        while self.pre_candle_set_for_del:
            print(f"Удалил с графика, длина pre_candle_set = {self.pre_candle_set_for_del}")
            # self.chart.removeItem(self.pre_candle_set_for_del.pop())
            self.sub_widget.signal_drop_item_on_chart.emit(
                {'symbol': self.symbol, 'tf': self.tf_sec, 'object': self.pre_candle_set_for_del.pop()})
        print(f"Длина pre_candle_set = {len(self.pre_candle_set_for_del)}")

    def del_pre_quotes_from_chart(self):
        print(f"Длина pre_quotes_set_for_del = {self.pre_quotes_set_for_del}")
        while self.pre_quotes_set_for_del:
            print(f"Удалил с графика, длина pre_quotes_set_for_del = {self.pre_quotes_set_for_del}")
            # self.chart.removeItem(self.pre_quotes_set_for_del.pop())
            self.sub_widget.signal_drop_item_on_chart.emit(
                {'symbol': self.symbol, 'tf': self.tf_sec, 'object': self.pre_quotes_set_for_del.pop()})
        print(f"Длина pre_quotes_set_for_del = {len(self.pre_quotes_set_for_del)}")

    def print_all(self):
        if self.bars_data:
            # хранитель данных о графике
            print(111111111)
            if self.graphic_data:
                if self.graphic_data[-1]['time_x_start'] < self.bars_data[-1]['time_open']:
                    while self.graphic_data[-1]['time_x_start'] < self.bars_data[-1]['time_open']:
                        len_box = len(self.chart_view_box.addedItems)
                        if len_box > 0:
                            print(f"len_box: {len_box}, last_elem: {self.chart_view_box.addedItems[-1]}")
                        else:
                            print("len_box пуст.")
                        # print(len(self.graphic_data), self.symbol, self.graphic_data[-1]['time_x_start'],
                        #       self.bars_data[-1]['time_open'])
                        self.append_graphic_data()
                        # self.draw_history_glass()
                        self.draw_bar_glass()
                        # Побарный счетчик сдвига
                        if self.offset < len(self.bars_data) - 1:
                            self.offset += 1
                else:
                    # отрисовка текущего бара
                    pre_dict = self.append_now_bar()
                    # отрисовка стакана
                    self.draw_now_glass(pre_dict)
                    print(33333333)
            else:
                # self.draw_history_glass()
                self.append_graphic_data()
                self.draw_bar_glass()
        else:
            print("История не получена, показывать нечего.")

    def run(self):
        print("Первый старт потока")
        while self.running:
            print(f"Начал цикл {self.symbol}")
            if self.bars_data:
                self.get_last_data_from_bd()
                self.print_all()
                print(f"Количество объектов на чарте: {len(self.chart.getPlotItem().getViewBox().allChildren())}")
            else:
                self.bars_data = self.mongo.get_qv_last_bars(self.symbol, self.tf_sec, self.len_start_chart)
            print(f"Закончил цикл {self.symbol}")
            self.sleep(3)


if __name__ == '__main__':
    pass