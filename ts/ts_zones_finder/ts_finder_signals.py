from ts.general_ts_finder import GeneralTsFinder
import datetime as dt


class TsZonesFinder(GeneralTsFinder):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_zones_finder'
        self.qv_bars = 501
        self.chart_slice = []

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        self.chart_slice = self.mongo.get_qv_last_bars(self.symbol, self.tf_sec, self.qv_bars)
        if len(self.chart_slice) == self.qv_bars:
            signals_dict = {
                'zones_finder': self.find_zone()
            }
            return self.form_signal_list(signals_dict)
        else:
            print("Размер чарт слайс и необходимого количества баров не соответствует.")

    def find_zone(self):
        """Ищет зоны с ТФ старше м15"""
        counter_high = 0
        counter_low = 0
        last_bar = self.chart_slice[-1]
        for bar in self.chart_slice:
            if bar['high'] <= last_bar['high']:
                counter_high += 1
            if bar['low'] >= last_bar['low']:
                counter_low += 1
        if counter_high == self.qv_bars:
            return "zona_high"
        elif counter_low == self.qv_bars:
            return "zona_low"


# class AlertZones(GeneralTsFinder):
#     """Поиск выхода из зоны с соотношением к м15 таймфрейму"""
#     def __init__(self, main_self, symbol, tf_sec):
#         GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
#         self.ts_name = 'ts_zones_finder'
#         self.qv_bars = 501
#         self.chart_slice = []
#
#         # self.ts = PositionsOrdersManager(0)
#         # self.qv_bars = 501
#         # self.dop_time_frame = mt5.TIMEFRAME_M15
#         # self.tm_filter = dt.datetime.now()
#         # self.control_dict = {}
#
#     def time_filter(self):
#         """фильтр обновления сигнала на одну минуту"""
#         dtn = dt.datetime.now()
#         min_filter = dt.datetime(dtn.year, dtn.month, dtn.day, dtn.hour, dtn.minute, 3)
#         if self.tm_filter < min_filter:
#             self.tm_filter = min_filter
#             return True
#         return False
#
#     def find_zones(self, symbol, tf):
#         """Ищет зоны с ТФ старше м15"""
#         rates_frame, symbol_info = cf.get_bars_one_tf(symbol, tf, 1, self.qv_bars, self.ts.terminal)
#         counter_high = 0
#         counter_low = 0
#         last_bar = rates_frame.iloc[-1]
#         for i in rates_frame.index:
#             if rates_frame.at[i, 'high'] <= last_bar['high']:
#                 counter_high += 1
#             if rates_frame.at[i, 'low'] >= last_bar['low']:
#                 counter_low += 1
#
#         if counter_high == self.qv_bars:
#             return "zone_high", last_bar['high']
#         elif counter_low == self.qv_bars:
#             return "zone_low", last_bar['low']
#         return "", 0
#
#     def send_signal(self, symbol, tf):
#         to_dict = self.control_dict[symbol][cf.full_tfs_in_sec_dict[tf]]
#         msg = f"{symbol} {cf.full_tfs_in_sec_dict[tf]} {to_dict['zone']} {to_dict['price']} {dt.datetime.now()}"
#         cf.send_message_bot(msg)
#         print(msg)
#
#     def clear_zone(self, symbol, tf):
#         to_dict = self.control_dict[symbol][cf.full_tfs_in_sec_dict[tf]]
#         to_dict['zone'] = ""
#         to_dict['price'] = 0
#
#     def zones_control(self, zone: tuple, symbol: str, tf: int):
#         """принимает решение по началу поиска сигнала от зоны"""
#         direct, price = zone  # полная зона должна приходить только при обновлении, иначе ("", 0)
#         to_dict = self.control_dict[symbol][cf.full_tfs_in_sec_dict[tf]]
#         if (not direct) and (not to_dict['zone']):
#             return
#         if direct:
#             to_dict['zone'] = direct
#             to_dict['price'] = price
#         rates_frame, symbol_info = cf.get_bars_one_tf(symbol, self.dop_time_frame, 1, 30, self.ts.terminal)
#         for i in range(-1, -len(rates_frame), -1):
#             bar_direct = rates_frame.iloc[i].at['bar_direct']
#             bar_close = rates_frame.iloc[i].at['close']
#             if to_dict['zone'] == 'zone_high':
#                 if (bar_direct == 'down_bar') and (bar_close < to_dict['price']):
#                     self.send_signal(symbol, tf)
#                     self.clear_zone(symbol, tf)
#                     break
#             if to_dict['zone'] == 'zone_low':
#                 if (bar_direct == 'up_bar') and (bar_close > to_dict['price']):
#                     self.send_signal(symbol, tf)
#                     self.clear_zone(symbol, tf)
#                     break
#
#     def run(self):
#         """Основной метод обработчик"""
#         while True:
#             if self.time_filter():
#                 for symbol in cf.symbols_list:
#                     if not (symbol in self.control_dict):
#                         self.control_dict[symbol] = {}
#                     tf = mt5.TIMEFRAME_M1
#                     tf_sec = cf.full_tfs_in_sec_dict[tf]
#                     if not (tf_sec in self.control_dict[symbol]):
#                         self.control_dict[symbol][tf_sec] = {'zone': "", 'price': 0}
#                     zone = self.find_zones(symbol, tf)
#                     self.zones_control(zone, symbol, tf)
#             time.sleep(1)

if __name__ == '__main__':
    ts = TsZonesFinder('', 'SiU1', 60)
    ts.sub_manager_ts()
    pass


"""
Доработать:
    Получение размера объема одной свечи

"""