from ts.general_ts_finder import GeneralTsFinder


class TsCatchPlayer(GeneralTsFinder):
    """Стратегия ищет соотношение ratio"""
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = "ts_catch"

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        self.get_price_max_ratio_cluster()
        self.get_direct_max_cluster()
        self.get_area_max_cluster()
        return self.update_signal()

    # индивидуальная функция
    def get_price_max_ratio_cluster(self):
        self.strategy_metrics['price_max_cluster'] = 0
        price_ratio = 0
        for price in self.cluster_list:
            if abs(self.cluster_data[price]['metrics_cluster']['ratio_kf_ask_bid_quantity']) > price_ratio:
                price_ratio = abs(self.cluster_data[price]['metrics_cluster']['ratio_kf_ask_bid_quantity'])
                self.strategy_metrics['price_max_cluster'] = self.mongo.get_real_price(price)
        if self.mongo.get_price_mongo_name_format(self.strategy_metrics['price_max_cluster']) == '0':
            a = 'stop'
        self.strategy_metrics['cluster_metrics'] = \
            self.cluster_data[self.mongo.get_price_mongo_name_format(
                self.strategy_metrics['price_max_cluster'])]['metrics_cluster']

    # индивидуальная функция
    def get_direct_max_cluster(self):
        path = self.cluster_data[self.mongo.get_price_mongo_name_format(
            self.strategy_metrics['price_max_cluster'])]['metrics_cluster']
        if path['summary_ask_quantity'] > path['summary_bid_quantity']:
            self.strategy_metrics['direct_max_cluster'] = 'up'
        elif path['summary_ask_quantity'] < path['summary_bid_quantity']:
            self.strategy_metrics['direct_max_cluster'] = 'down'
        else:
            self.strategy_metrics['direct_max_cluster'] = 'none'

    # индивидуальная функция
    def get_area_max_cluster(self):
        hl = self.last_bar['high'] - self.last_bar['low']
        ph = self.last_bar['high'] - self.strategy_metrics['price_max_cluster']
        pl = self.strategy_metrics['price_max_cluster'] - self.last_bar['low']
        ph_hl = ph/hl
        pl_hl = pl/hl
        if (ph_hl < pl_hl) and (ph_hl <= 0.25):
            self.strategy_metrics['cluster_area'] = "high"
        elif (pl_hl < ph_hl) and (pl_hl <= 0.25):
            self.strategy_metrics['cluster_area'] = 'low'
        else:
            self.strategy_metrics['cluster_area'] = 'center'

    # индивидуальная функция
    def update_signal(self):
        print(self.strategy_metrics['cluster_area'], self.strategy_metrics['direct_max_cluster'],
              self.bar_metrics['bar_direct'],
              abs(self.strategy_metrics['cluster_metrics']['ratio_kf_ask_bid_quantity']))
        if ((self.strategy_metrics['cluster_area'] == "high") and
            (self.strategy_metrics['direct_max_cluster'] == "up") and
            (self.bar_metrics['bar_direct'] == "down_bar") and
                (abs(self.strategy_metrics['cluster_metrics']['ratio_kf_ask_bid_quantity']) > 400)):
            print(f"Сигнал sell_signal, {self.time_scheduler_last_bar, self.last_bar['time_open']}")
            return self.form_signal('deal', direct='sell_signal')
        elif ((self.strategy_metrics['cluster_area'] == "low") and
              (self.strategy_metrics['direct_max_cluster'] == "down") and
              (self.bar_metrics['bar_direct'] == "up_bar") and
                (abs(self.strategy_metrics['cluster_metrics']['ratio_kf_ask_bid_quantity']) > 400)):
            print(f"Сигнал buy_signal, {self.time_scheduler_last_bar, self.last_bar['time_open']}")
            return self.form_signal('deal', direct='buy_signal')
        else:
            print("Сигналов не найдено")
            return {}


if __name__ == '__main__':
    pass
