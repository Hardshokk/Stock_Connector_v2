import pandas as pd
from common_files.common_functions import save_object
from ts.general_ts_finder import GeneralTsFinder
import datetime as dt



class TsTestBar(GeneralTsFinder):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_test'

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        # после написания ТС сюда занести функции необходимые для работы ТС, вернуть сигнал.
        return None

    @staticmethod
    def get_bid_x_ask(bar_vol, bar_delta):
        """Получает соотношение бид аск имея объем бара и дельту"""
        bid = (bar_vol - bar_delta) / 2
        ask = bid + bar_delta
        vol = ask + bid
        print(bid, ask, vol)
        return f"{bid}x{ask}"

    def get_data(self):
        """Получает сигнал"""
        # chart = self.mongo.get_qv_last_bars(self.symbol, self.tf_sec, 5)
        chart = self.mongo.get_range_bars_time(self.symbol, self.tf_sec, dt.datetime(2021, 4, 12),
                                               dt.datetime(2021, 4, 12, 23, 51))
        common_dict = {'cum_vol': [], 'cum_delta': [], 'kf': [], 'dt_start': [], 'dt_finish': [], 'close': []}
        for index in range(len(chart)):
            # candle = chart[index]
            # time_open = candle['time_open']
            # bar_vol = candle['bar_vol_metrics']['summary_bid_ask_quantity']
            # bar_delta = candle['bar_vol_metrics']['difference_bid_ask_quantity']
            # bar_ask = candle['bar_vol_metrics']['summary_ask_quantity']
            # bar_bid = candle['bar_vol_metrics']['summary_bid_quantity']

            counter = 1
            while index + counter < len(chart):
                cum_vol = 0
                cum_delta = 0
                for i in range(index, index + counter):
                    cum_vol += chart[i]['bar_vol_metrics']['summary_bid_ask_quantity']
                    cum_delta += chart[i]['bar_vol_metrics']['difference_bid_ask_quantity']
                cum_delta = 1 if cum_delta == 0 else cum_delta
                kf = abs(cum_vol / cum_delta)
                if kf >= 100000:
                    dict_data = {'cum_vol': cum_vol, 'cum_delta': cum_delta, 'kf': kf,
                                 'dt_start': chart[index]['time_open'], 'dt_finish': chart[index+counter]['time_open'],
                                 'close': chart[index+counter]['close']}

                    for key in dict_data.keys():
                        common_dict[key].append(dict_data[key])

                # print(f"cum_vol {cum_vol}, cum_delta {cum_delta}, kf {abs(cum_vol / cum_delta)}"
                #       f"{chart[index]['time_open']} {chart[index+counter]['time_open']}")

                counter += 1
        df = pd.DataFrame(common_dict)
        df['time_delta'] = df['dt_finish'] - df['dt_start']
        df = df.sort_values(by='kf', ascending=False)
        print(df.loc[:, ['cum_vol', 'kf', 'time_delta', 'dt_start', 'dt_finish']])
        # save_object(common_dict, "common_dict.df")


if __name__ == '__main__':
    pd.set_option('max_rows', 1000)
    pd.set_option('max_columns', 1000)
    pd.set_option('float_format', '{:,.0f}'.format)
    ts = TsTestBar('', 'SiU1', 60)
    ts.get_data()
    pass