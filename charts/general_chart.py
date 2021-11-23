from functools import partial

import pyqtgraph as pg
import numpy as np
import datetime as dt
from PyQt5 import QtCore, QtGui
import common_files.common_functions as cf


class MyInfiniteLine(pg.InfiniteLine):
    """Класс бесконечной линии, использую в Ask Bid"""
    def __init__(self, **kwargs):
        pg.InfiniteLine.__init__(self, **kwargs)

    def setValue(self, value, label=None):
        """добавил изменение лейбла"""
        self.setPos(value)
        if label is not None:
            self.label.setText(str(label))


class MyTextItem(pg.TextItem):
    """Класс решает проблему постоянного масштабирования текста"""
    def __init__(self, x_len=0.045, y_len=-0.08):
        self.x_len = x_len
        self.y_len = y_len
        pg.TextItem.__init__(self)

    def updateTransform(self, force=False):
        if not self.isVisible():
            return

        p = self.parentItem()
        if p is None:
            pt = QtGui.QTransform()
        else:
            pt = p.sceneTransform()

        if not force and pt == self._lastTransform:
            return

        t = pt.inverted()[0]
        # reset translation
        # t.setMatrix(t.m11(), t.m12(), t.m13(), t.m21(), t.m22(), t.m23(), 0, 0, t.m33())
        t.setMatrix(self.x_len, t.m12(), t.m13(), t.m21(), self.y_len, t.m23(), 0, 0, t.m33())

        # apply rotation
        angle = -self.angle
        if self.rotateAxis is not None:
            d = pt.map(self.rotateAxis) - pt.map(pg.Point(0, 0))
            a = np.arctan2(d.y(), d.x()) * 180 / np.pi
            angle += a
        t.rotate(angle)
        self.setTransform(t)
        self._lastTransform = pt
        self.updateTextPos()


class PreMyTextItem(MyTextItem):
    """Упрощает использование подписей стаканных сигналов в будущем"""
    def __init__(self, main_self, x_len=0.045, y_len=0.08):
        MyTextItem.__init__(self, x_len=x_len, y_len=y_len)
        self.main_self = main_self


class ParentMixin(pg.GraphicsObject):
    """Промежуточный родительский класс обобщающий создание элеметов графика"""
    def __init__(self, main_self):
        pg.GraphicsObject.__init__(self)
        self.picture = None
        self.main_self = main_self
        self.x_offset = dt.datetime.timestamp(self.full_data['data_bar']['time_x_start'])
        self.inter_bar_kf = 2.4
        self.kf_step_x = 60
        self.w = (1 * self.kf_step_x) / self.inter_bar_kf  # Регулировка ширины отклонения от центра
        self.start_pos = self.x_offset - self.w
        self.weight = self.w * 2

    def main_gen_pic(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)  # Создаю объект painter
        p.setPen(pg.mkPen(self.color_pen))  # Назначаю ручку
        self.gen_pic(p)

    def paint(self, p, *args):
        """метод из родительских классов"""
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        """метод из родительских классов"""
        return QtCore.QRectF(self.picture.boundingRect())


class CandlesItem(ParentMixin):
    """Класс для создания свечей на графике"""
    def __init__(self, main_self, data):
        self.full_data = data
        self.bar_data = self.full_data['data_bar']['objects']['bar']

        ParentMixin.__init__(self, main_self)

        self.color_pen = 255, 255, 255
        self.color_up_bar = 0, 255, 33
        self.color_down_bar = 255, 12, 0

        self.main_gen_pic()  # Создаю изначальный график

    def get_last_metrics(self):
        """Для отображения бара"""
        return [(self.x_offset, self.bar_data['high'], self.bar_data['low'],
                self.bar_data['open'], self.bar_data['close'])]

    def gen_pic(self, p):
        """Метод для отрисовки необходимого элемента, переопределяется"""
        for t, high, low, open_pr, close_pr in self.get_last_metrics():
            # Рисую тени свечи
            p.drawLine(QtCore.QPointF(t, low), QtCore.QPointF(t, high))
            # Рисую тело свечи
            if open_pr > close_pr:
                p.setBrush(pg.mkBrush(self.color_down_bar))
            elif open_pr < close_pr:
                p.setBrush(pg.mkBrush(self.color_up_bar))
            else:
                p.setBrush(pg.mkBrush(self.color_pen))
            rect = QtCore.QRectF(self.start_pos, open_pr, self.weight, close_pr - open_pr)
            p.drawRect(rect)
        p.end()


class PreCandlesItem(CandlesItem):
    """Класс рисует текущую свечу"""
    def __init__(self, main_self, data):
        CandlesItem.__init__(self, main_self, data)

    def get_last_metrics(self):
        """Для отображения бара"""
        return [(self.x_offset, self.bar_data['high'], self.bar_data['low'])]

    def gen_pic(self, p):
        """Метод для отрисовки необходимого элемента, переопределяется"""
        for t, high, low in self.get_last_metrics():
            p.drawLine(QtCore.QPointF(t, high), QtCore.QPointF(t, low))
        p.end()


class QuotesLines(ParentMixin):
    """Класс для создания уровеней заявок стакана на графике"""
    pre_cot = False

    def __init__(self, main_self, self_thread, data: dict):
        self.full_data = data  # graphic_data
        self.df_quotes_slice = data['df_quotes_slice']  # Должен содержать слайс датафрейма с уровнями

        ParentMixin.__init__(self, main_self)

        self.color_pen = 255, 255, 255
        self.color_up_lvl = 94, 161, 255
        self.color_down_lvl = 255, 10, 173

        self.self_thread = self_thread
        self.main_gen_pic()  # Создаю изначальный график

    def gen_pic(self, p):
        """Метод для отрисовки необходимого элемента, переопределяется"""
        # print(self.df_quotes_slice)
        price_groups = self.df_quotes_slice.groupby(by=['price', 'direct'])
        for group_name in price_groups.groups:
            group = price_groups.get_group(group_name)
            price = float(group['price'].iat[-1])
            direct = group['direct'].iat[-1]
            print(f"Прекот перед добавлением равен равен {self.pre_cot}")
            if self.pre_cot:
                print("Добавление Претекста")
                text = PreMyTextItem(self.main_self, x_len=0.25, y_len=-0.15)
                rect = QtCore.QRectF(self.start_pos, price, self.weight, 0.999999999)
                self.self_thread.pre_pre_quotes_set_for_del.add(text)
            else:
                print("Добавление Текста")
                text = MyTextItem(x_len=0.25, y_len=-0.15)
                rect = QtCore.QRectF(self.start_pos, price, self.weight, 0.999999999)
            if direct == 'buy':
                p.setBrush(pg.mkBrush(self.color_up_lvl))
                text.setAnchor((0, 0.5))
            elif direct == 'sell':
                p.setBrush(pg.mkBrush(self.color_down_lvl))
                text.setAnchor((0, 1.5))
            p.drawRect(rect)
            # Обработка текста
            text.setPlainText(f"vol_max: {group['volume'].max()}, vol_last: {group['volume'].iat[-1]}")
            text.setPos(self.start_pos, price - 1)
            text.setZValue(10)
            print("Отправка сигнала добавления текста на чарт")
            self.main_self.signal_append_item_on_chart.emit(
                {'symbol': self.main_self.symbol, 'tf': self.main_self.tf_sec, 'object': text})
            print("Отправка сигнала добавления текста на чарт завершена")


class PreQuotesLines(QuotesLines):
    """Класс отделяет для удобства будущие котировки"""
    pre_cot = True

    def __init__(self, main_self, self_thread, data):
        QuotesLines.__init__(self, main_self, self_thread, data)
        print(f"Прекот в классе равен {self.pre_cot}")


class WindowChart(pg.graphicsWindows.PlotWidget):
    """Класс окна графика, будет перенесен в основную программу"""

    signal_append_item_on_chart = QtCore.pyqtSignal(dict)
    signal_drop_item_on_chart = QtCore.pyqtSignal(dict)

    def __init__(self, main_self=None, parent=None, **kwargs):
        pg.graphicsWindows.PlotWidget.__init__(self, parent=parent, axisItems={'bottom': pg.DateAxisItem(),
                                                                               'right': pg.AxisItem(
                                                                                   orientation='right'),
                                                                               'top': pg.AxisItem(orientation='top')})
        # Общие настройки
        self.main_self = main_self
        if kwargs:
            self.symbol = kwargs['symbol']
            self.tf_sec = kwargs['tf_sec']
        else:
            self.symbol = "SiM1"
            self.tf_sec = 60
        self.setWindowTitle(f"{self.symbol}  {self.tf_sec}")
        if not cf.symbol_is_terminal_variant(self.symbol):
            self.symbol_terminal = cf.get_symbol_format_terminal(self.symbol)
        else:
            self.symbol_terminal = self.symbol
        self.running = True

        # Обработка осей
        self.showGrid(x=True)
        self.this_main_plot = self.getPlotItem()
        self.this_main_plot.hideAxis('left')
        self.top_axis = self.this_main_plot.getAxis('top')
        self.right_axis = self.this_main_plot.getAxis('right')

        self.signal_append_item_on_chart.connect(partial(self.append_object_on_chart, self.signal_append_item_on_chart))
        self.signal_drop_item_on_chart.connect(partial(self.drop_object_on_chart, self.signal_drop_item_on_chart))

        # обработка аск бид цен
        # self.add_bid_ask()
        # self.startTimer(3000, timerType=QtCore.Qt.VeryCoarseTimer)

    def timerEvent(self, event):
        # print('Обновил бид аск')
        # self.update_bid_ask()
        # with open(f"logs\\window_{self.symbol}.chart", "a+") as f:
        #     line = '\n'.join([str(x) for x in self.this_main_plot.getViewBox().allChildren()])
        #     line = f"{line}\n{'*' * 15}{self.symbol} - {dt.datetime.now()}{'*' * 15}\n"
        #     f.write(f"{line}")
        event.accept()

    def add_bid_ask(self):
        # Получаю отображение цен бид/аск
        symbol_info = cf.get_symbol_info(self.symbol_terminal, self.main_self.terminal)
        label_opts = {'position': 0.96, 'color': (200, 200, 100),
                      'fill': (200, 200, 200, 50), 'movable': False}
        pen = pg.mkPen('#00A9FF', width=5)

        self.line_ask = MyInfiniteLine(pos=symbol_info['ask'], angle=0, pen=pen, label=str(symbol_info['ask']),
                                       labelOpts=label_opts, name="ask")
        self.line_ask.setZValue(11)
        self.addItem(self.line_ask)
        pen = pg.mkPen('#C147FF', width=5)
        self.line_bid = MyInfiniteLine(pos=symbol_info['bid'], angle=0, pen=pen, label=str(symbol_info['bid']),
                                       labelOpts=label_opts, name="bid")
        self.line_bid.setZValue(12)
        self.addItem(self.line_bid)

    def update_bid_ask(self):
        """обновление аск бид"""
        symbol_info = cf.get_symbol_info(self.symbol_terminal, self.main_self.terminal)
        self.line_ask.setValue(symbol_info['ask'], label=symbol_info['ask'])
        self.line_bid.setValue(symbol_info['bid'], label=symbol_info['bid'])

    def append_object_on_chart(self, *data):
        data_dict = data[1]
        self.main_self.mdi_objects[f"{data_dict['symbol']}_{data_dict['tf']}"].widget().getPlotItem().getViewBox().addItem(data_dict['object'])

    def drop_object_on_chart(self, *data):
        data_dict = data[1]
        # print("Объект перед удалением: ", data_dict['object'])
        # print("Методы объекта перед удалением: ", dir(data_dict['object']))
        # print("Методы widget: ", dir(self.main_self.mdi_objects[f"{data_dict['symbol']}_{data_dict['tf']}"].widget()))
        # print("Методы view_box: ", dir(self.main_self.mdi_objects[f"{data_dict['symbol']}_{data_dict['tf']}"].widget().getPlotItem().getViewBox()))
        self.main_self.mdi_objects[f"{data_dict['symbol']}_{data_dict['tf']}"].widget().getPlotItem().getViewBox().removeItem(data_dict['object'])