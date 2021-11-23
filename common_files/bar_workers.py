import copy
import pyqtgraph as pg
import datetime as dt

# ['id', 'symbol', 'seccode', 'tradeno', 'tradetime', 'datetrade', 'price', 'quantity', 'buysell', 'openinterest']


class Bar:
    def __init__(self, ticks, start_scheduler, tf_sec):
        self.df_ticks = ticks.copy()
        self.df_ticks['buysell'] = self.df_ticks['buysell'].str.strip()
        self.time_open = start_scheduler
        self.tf_sec = tf_sec
        self.time_close = self.time_open + (dt.timedelta(seconds=self.tf_sec) - dt.timedelta(microseconds=1))
        self.high = self.df_ticks['price'].max()
        self.open = self.df_ticks['price'].iat[0]
        self.close = self.df_ticks['price'].iat[-1]
        self.low = self.df_ticks['price'].min()
        self.bar_vol_metrics = self.get_common_metrics(self.df_ticks)
        self.bar_metrics = self.calculate_metrics_bar()
        self.cluster_list = list(set(self.df_ticks['price'].values))
        self.cluster_list.sort()
        self.cluster_list_number = copy.deepcopy(self.cluster_list)
        self.cluster_list = [str(x).replace(".", "_") for x in self.cluster_list]
        self.cluster_data = self.calculate_metrics_cluster()

    def get_document(self):
        document = {
            "time_open": self.time_open,
            "time_close": self.time_close,
            "tf_sec": self.tf_sec,
            "high": self.high,
            "open": self.open,
            "close": self.close,
            "low": self.low,
            "bar_vol_metrics": self.bar_vol_metrics,
            "bar_metrics": self.bar_metrics,
            "cluster_list": self.cluster_list,
            "cluster_data": self.cluster_data
        }
        return document

    @staticmethod
    def get_common_metrics(df_ticks):
        """функция рассчетов основных метрик баров и кластеров"""
        metrics_dict = {}
        df_ticks_ask = df_ticks[df_ticks['buysell'] == 'B']
        df_ticks_bid = df_ticks[df_ticks['buysell'] == 'S']
        metrics_dict['interest_delta'] = (df_ticks['openinterest'].iat[-1] - df_ticks['openinterest'].iat[0]) / 2
        """Объемные рассчеты"""
        # summary_bid_quantity и summary_ask_quantity суммируют количество контрактов по продавцам или покупателям
        # bid_deals и ask_deals суммируют количество сделок по продавцам и покупателям отдельно
        metrics_dict['summary_ask_quantity'] = df_ticks_ask['quantity'].sum()
        metrics_dict['summary_bid_quantity'] = df_ticks_bid['quantity'].sum()
        metrics_dict['summary_ask_deals'] = len(df_ticks_ask)
        metrics_dict['summary_bid_deals'] = len(df_ticks_bid)
        for name in ["quantity", "deals"]:
            # summary_bid_ask_quantity это общий вертикальный объем контрактов свечи"""
            # summary_bid_ask_deals это общий вертикальный объем сделок свечи"""
            metrics_dict[f'summary_bid_ask_{name}'] = (metrics_dict[f'summary_ask_{name}'] +
                                                       metrics_dict[f'summary_bid_{name}'])
            # difference_bid_ask_quantity это дельта по контрактам, т.е. покупатели минус продавцы
            # difference_bid_ask_deals это дельта по сделкам, т.е. покупатели минус продавцы
            metrics_dict[f'difference_bid_ask_{name}'] = (metrics_dict[f'summary_ask_{name}'] -
                                                          metrics_dict[f'summary_bid_{name}'])
            # ratio_kf_bid_ask_quantity это соотношение проданых контрактов к купленным
            # ratio_kf_bid_ask_deals это соотношение сделок покупателей к сделкам продавцов
            qv_ask = metrics_dict[f'summary_ask_{name}'] if metrics_dict[f'summary_ask_{name}'] > 0 else 1
            qv_bid = metrics_dict[f'summary_bid_{name}'] if metrics_dict[f'summary_bid_{name}'] > 0 else 1
            metrics_dict[f'ratio_ask_{name}'] = qv_ask / qv_bid
            metrics_dict[f'ratio_bid_{name}'] = qv_bid / qv_ask
            metrics_dict[f'ratio_kf_ask_bid_{name}'] = (metrics_dict[f'ratio_ask_{name}'] -
                                                        metrics_dict[f'ratio_bid_{name}'])
        return metrics_dict

    def _calculate_ratio_prices_bar(self, bar_metrics, price_1, price_2):
        """от bar_var_calculate производит рассчеты метрики бара"""
        bar_metrics['hl'] = self.high - self.low
        if bar_metrics['hl'] == 0:
            bar_metrics.update({'hp': 0, 'lp': 0, 'hp_kf': 0, 'lp_kf': 0, 'pp_kf': 0})
            return bar_metrics
        bar_metrics['hp'] = self.high - price_1
        bar_metrics['lp'] = price_2 - self.low
        bar_metrics['hp_kf'] = bar_metrics['hp'] / bar_metrics['hl']
        bar_metrics['lp_kf'] = bar_metrics['lp'] / bar_metrics['hl']
        bar_metrics['pp_kf'] = 1 - (bar_metrics['hp_kf'] + bar_metrics['lp_kf'])
        return bar_metrics

    @staticmethod
    def _get_class_bar(bm):
        """от bar_var_calculate вариант свечи(додж, пинбар, полнотелая, fifty_коррекционная, некликвид, другая)"""
        if (bm['hp_kf'] <= 0.18) and (bm['lp_kf'] <= 0.18) and (bm['pp_kf'] >= 0.64):
            bm['bar_class'] = 'full_bar'
        elif (bm['pp_kf'] >= -0.015) and (bm['pp_kf'] <= 0.015):
            bm['bar_class'] = 'dodge_bar'
        elif (bm['hp_kf'] == 0) and (bm['lp_kf'] == 0) and (bm['pp_kf'] == 0):
            bm['bar_class'] = 'illiquid_bar'
        elif ((bm['pp_kf'] > 0.015) and (bm['pp_kf'] <= 0.15)) and ((bm['hp_kf'] >= 0.68) or (bm['lp_kf'] >= 0.68)):
            bm['bar_class'] = 'pin_bar'
        elif (bm['pp_kf'] >= 0.3) and ((bm['hp_kf'] >= 0.47) or (bm['lp_kf'] >= 0)):
            bm['bar_class'] = 'fifty_bar'
        else:
            bm['bar_class'] = 'another_bar'
        return bm

    def calculate_metrics_bar(self):
        """метод рассчета метрик бара"""
        bar_metrics = {}
        if self.open > self.close:
            bar_metrics['bar_direct'] = 'down_bar'
            bar_metrics.update(self._calculate_ratio_prices_bar(bar_metrics, self.open, self.close))
        elif self.open < self.close:
            bar_metrics['bar_direct'] = 'up_bar'
            bar_metrics.update(self._calculate_ratio_prices_bar(bar_metrics, self.close, self.open))
        elif self.open == self.close:
            bar_metrics['bar_direct'] = 'center_bar'
            bar_metrics.update(self._calculate_ratio_prices_bar(bar_metrics, self.close, self.open))
        bar_metrics.update(self._get_class_bar(bar_metrics))
        return bar_metrics

    def calculate_metrics_cluster(self):
        cluster_dict = {}
        for price in self.cluster_list:
            cluster_df = self.df_ticks[self.df_ticks['price'] == float(price.replace('_', '.'))]
            cluster_dict[price] = {'cluster_df': cluster_df['id'].to_list(),
                                   'metrics_cluster': self.get_common_metrics(cluster_df)}
        return cluster_dict


"""
После заполнения чарта, дальше перейти к созданию отдельных классов ТС.
Пока будет создана одна ТС.

# Значение каждого кластера внутри свечи и для свечи в целом
# Соотношение закрытия свечи и покластерного анализа, классификация варианта свечи
# В будущем добавить поток заявок и добавить аналитику по нему
"""

"""
    def get_points(self, price):
        в идеале нужно этот параметр получать с биржи, поэтому эта функция со временем удалится
        number = str(price).split('.')
        if len(number) == 1:
            return 0, 0
        elif len(number) == 2:
            digits = len(number[1])
            points = float(f"0.{'0' * (digits - 1)}1")
            return digits, points
        else:
            print("Ошибка, передано неверное число в функцию вычисления points, digits")
            return 0, 0
"""