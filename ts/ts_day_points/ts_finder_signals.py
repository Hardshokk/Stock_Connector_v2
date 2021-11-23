from ts.general_ts_finder import GeneralTsFinder
import datetime as dt


class TsDayPoints(GeneralTsFinder):
    def __init__(self, main_self, symbol, tf_sec):
        GeneralTsFinder.__init__(self, main_self, symbol, tf_sec)
        self.ts_name = 'ts_day_points'
        self.chart_slice = []
        self.day_high = 0
        self.day_low = 99999999999
        self.start_day = dt.datetime.now()
        self.high_pre_day, self.low_pre_day = self.pre_day_init()
        self.status_higher = False
        self.status_lower = False

    def sub_manager_ts(self):
        """При появлении нового бара активирует указанные функции, возвращает сигнал, переопределяется"""
        tm_finish = dt.datetime.now()
        tm_start = dt.datetime(tm_finish.year, tm_finish.month, tm_finish.day)
        self.chart_slice = self.mongo.get_range_bars_time(self.symbol, self.tf_sec, tm_start, tm_finish)
        if self.chart_slice:
            signals_dict = {
                'update_edge_day': self.update_day_high_or_low(),
                'pre_day_update': self.pre_day_update()
            }
            return self.form_signal_list(signals_dict)

    def update_day_high_or_low(self):
        """Сигнал при обновлении хая или лоу дня"""
        bar = self.chart_slice[-1]
        if bar['high'] > self.day_high:
            self.day_high = bar['high']
            return "update_day_high"
        elif bar['low'] < self.day_low:
            self.day_high = bar['low']
            return "update_day_low"

    @staticmethod
    def select_date():
        """возвращает начало и конец предыдущего дня относительно текущего"""
        dn = dt.datetime.now()
        start = dt.datetime(dn.year, dn.month, dn.day)
        if dt.datetime.isoweekday(dn) == 1:
            start = start - dt.timedelta(days=3)
        elif (dt.datetime.isoweekday(dn) > 1) and dt.datetime.isoweekday(dn) < 6:
            start = start - dt.timedelta(days=1)
        else:
            return
        finish = start + dt.timedelta(hours=23, minutes=59, seconds=59)
        return start, finish

    def get_high_and_low_on_day(self, time_start, time_finish):
        """Получить хай и лоу предыдущих дней"""
        chart_pre_day = self.mongo.get_range_bars_time(self.symbol, self.tf_sec, time_start, time_finish)
        high_day = 0
        low_day = 9999999999
        if chart_pre_day:
            for bar in chart_pre_day:
                if bar['high'] > high_day:
                    high_day = bar['high']
                if bar['low'] < low_day:
                    low_day = bar['low']
        return high_day, low_day

    def pre_day_init(self):
        """получает первичные значения хая и лоу предыдущего дня"""
        start, finish = self.select_date()
        return self.get_high_and_low_on_day(start, finish)

    def pre_day_update(self):
        """сигнальная функция следящая за областью в которой находится цена и сигналящая если область меняется"""
        if (dt.datetime(self.start_day.year, self.start_day.month, self.start_day.day) !=
                dt.datetime(dt.datetime.now().year, dt.datetime.now().month, dt.datetime.now().day)):
            self.high_pre_day, self.low_pre_day = self.pre_day_init()
        if (self.chart_slice[-1]['close'] > self.high_pre_day) and (not self.status_higher):
            self.status_higher = True
            return "higher_pre_day"
        elif (self.chart_slice[-1]['close'] < self.low_pre_day) and (not self.low_pre_day):
            self.status_lower = True
            return "lower_pre_day"
        elif (self.chart_slice[-1]['close'] <= self.high_pre_day) and self.status_higher:
            self.status_higher = False
            return "in_range_pre_day"
        elif (self.chart_slice[-1]['close'] >= self.low_pre_day) and self.status_lower:
            self.status_lower = False
            return "in_range_pre_day"


if __name__ == '__main__':
    ts = TsDayPoints('', 'SiU1', 60)
    ts.sub_manager_ts()
    pass


"""
Доработать:
    Получение размера объема одной свечи

"""