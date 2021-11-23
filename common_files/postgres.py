import time
import psycopg2
from common_files import common_functions as cf
import datetime as dt
import pandas as pd
from common_files.bar_workers import Bar
from common_files.mongo import ConnectorMongo


class ConnectorPostgres:
    def __init__(self):
        self.main_db_name = 'Stocks_Market'
        self.user = 'postgres'
        self.password = '12345'
        self.host = 'localhost'
        self.port = 5432
        self.connect, self.cursor = self.create_connect_db()
        self.columns = ['id', 'symbol', 'seccode', 'tradeno', 'tradetime', 'datetrade', 'price',
                        'quantity', 'buysell', 'openinterest']

    def create_connect_db(self):
        """Подключение к postgree sql"""
        conn = psycopg2.connect(dbname=self.main_db_name, user=self.user, password=self.password,
                                host=self.host, port=self.port)
        conn.autocommit = True
        cur = conn.cursor()
        return conn, cur

    def close_connect_db(self):
        """Отключение от postgree sql"""
        self.cursor.close()
        self.connect.close()

    @staticmethod
    def get_symbol_from_code(seccode):
        """преобрзаует формат SiH1 в формат Si-3.21"""
        symbol_name = cf.fuchers_code_to_fuchers_name[seccode[:-2]]
        symbol_month = cf.fuchers_mcode_to_fuchers_month[seccode[-2:-1]]
        symbol_year = f"{str(dt.datetime.now().year)[:1]}{seccode[-1]}"
        return f"{symbol_name}-{symbol_month}.{symbol_year}"

    @staticmethod
    def get_date_from_norm_date(date):
        """принимает объект datetime на выходе отдает формат даты для получения таблицы"""
        return f"{date.year}_{date.month}_{date.day}"

    @staticmethod
    def get_date_from_tradetime(trade_time):
        """преобразует формат 10.03.2021 11:13:24.419  в  datetime объект 2021.3.10 и имя 2021-3-10"""
        day, month, year = trade_time.split(" ")[0].split(".")
        date_obj = dt.datetime(int(year), int(month), int(day))
        date_for_bd = f"{year}_{int(month)}_{int(day)}"
        return date_obj, date_for_bd

    def get_table_name(self, seccode, date):
        """функция возвращает имя таблицы SiH1_2021-3-10, символ Si-3.21, объект даты"""
        symbol = self.get_symbol_from_code(seccode)  # Si-3.21
        if isinstance(date, str):
            date, date_for_name = self.get_date_from_tradetime(date)  # 2021-3-12
        else:
            date_for_name = self.get_date_from_norm_date(date)
        table_name = f"{seccode}__{date_for_name}"  # SiH1__2021-3-12
        return table_name.lower(), symbol, date

    def exist_table(self, table_name, return_tables=False):
        """проверяет существует ли таблица в бд"""
        self.cursor.execute(f"SELECT table_name FROM information_schema.tables "
                            f"WHERE table_schema='public' ORDER BY table_name;")
        tables = self.cursor.fetchall()
        tables_set = set([table_tuple[0] for table_tuple in tables])
        if return_tables:
            return tables_set
        if table_name in tables_set:
            return True
        return False

    @staticmethod
    def _get_time_last_table(date_table, time_finder):
        """функция от get_last_table, получает время таблицы"""
        date_tuple = date_table.split("_")
        date_this_table = dt.datetime(int(date_tuple[0]), int(date_tuple[1]), int(date_tuple[2]))
        if date_this_table > time_finder:
            time_finder = date_this_table
        return time_finder

    def get_date_last_table(self, seccode=""):
        """возвращает время последней существующей таблицы, или последней существующей по указанному символу"""
        table_set = self.exist_table("", return_tables=True)
        if not table_set:
            print("База данных пуста.")
            return dt.datetime.now()
        time_is_start = dt.datetime(2021, 3, 15)
        time_finder = dt.datetime(2021, 3, 15)
        for table in table_set:
            symbol_table, date_table = table.split("__")
            if seccode:
                if symbol_table.lower() == seccode.lower():
                    time_finder = self._get_time_last_table(date_table, time_finder)
                continue
            else:
                time_finder = self._get_time_last_table(date_table, time_finder)
        if time_finder == time_is_start:
            print("Таблиц по данному инструменту вероятно не существует")
            return dt.datetime.now()
        return time_finder

    def get_time_scheduler(self, tf_sec, date_start_or_none, add_one_day=False):
        """получаем планировщик времени запросов в бд на обработку сигнала - лист с datetime объектами"""
        # В date_start передать время последнего бара в монго, если в монго таблиц нет, передать None
        if not date_start_or_none:
            table_set = self.exist_table("", return_tables=True)
            time_start = dt.datetime.now()
            for table in table_set:
                date_tuple = table.split("__")[1].split("_")
                date_table = dt.datetime(int(date_tuple[0]), int(date_tuple[1]), int(date_tuple[2]))
                if date_table < time_start:
                    time_start = date_table
        else:
            time_start = dt.datetime(date_start_or_none.year, date_start_or_none.month, date_start_or_none.day)

        if add_one_day:
            days_delta = (dt.datetime.now() + dt.timedelta(days=1) - time_start).days \
                if dt.datetime.now() > date_start_or_none else 0
        else:
            if not date_start_or_none:
                days_delta = (dt.datetime.now() - time_start).days
            else:
                days_delta = (dt.datetime.now() - time_start).days if dt.datetime.now() > date_start_or_none else 0

        time_finish = time_start + dt.timedelta(days=days_delta + 1)
        dates_for_request = []  # список дат, для перебора таблиц в базе данных, и получения тиков
        for i in range(days_delta + 1):
            dates_for_request.append(time_start + dt.timedelta(days=i))
        time_now = time_start
        step_delta = dt.timedelta(seconds=tf_sec)
        time_scheduler = []
        while time_now < time_finish:
            time_scheduler.append(time_now)
            time_now += step_delta
        return time_scheduler, dates_for_request


class GetTicks(ConnectorPostgres):
    """Класс для получения только тиков из бд"""
    def __init__(self):
        ConnectorPostgres.__init__(self)

    def get_ticks_from_postgres(self, symbol_code, dt_start, dt_finish):
        table_name, symbol, date = self.get_table_name(symbol_code, dt_start)
        if self.exist_table(table_name):
            self.cursor.execute(
                f"select * from {table_name} where tradetime>='{dt_start}' and tradetime<'{dt_finish}';"
            )
            return pd.DataFrame(self.cursor.fetchall(), columns=self.columns)
        return pd.DataFrame()

    def get_last_tick_from_postgres(self, symbol_code):
        table_name, symbol, date = self.get_table_name(symbol_code, self.get_date_last_table(seccode=symbol_code))
        if self.exist_table(table_name):
            self.cursor.execute(
                f"select * from {table_name} ORDER BY id DESC LIMIT 1;"
            )
            return pd.DataFrame(self.cursor.fetchall(), columns=self.columns)
        return pd.DataFrame()


class TickSaver(ConnectorPostgres):
    def __init__(self):
        super().__init__()

    def db_create(self, table_name):
        """функция пересоздает таблицу в бд"""
        self.cursor.execute(
            f"create table if not exists {table_name} ("
            f"id serial PRIMARY KEY,"
            f"symbol character (50),"
            f"seccode character (50),"
            f"tradeno bigint,"
            f"tradetime timestamp,"
            f"datetrade date,"
            f"price real,"
            f"quantity real,"
            f"buysell character (2),"
            f"openinterest integer);")

    def save_data(self, tick):
        seccode, tradeno, tradetime, price, quantity, buysell, openinterest = tick.values()
        table_name, symbol, date = self.get_table_name(seccode, tradetime)
        self.db_create(table_name)
        """сохраняет тики в базу данных"""
        request = f"insert into {table_name} " \
                  f"(symbol, seccode, tradeno, tradetime, datetrade, price, quantity, buysell, openinterest) values " \
                  f"('{symbol}', '{seccode}', {int(tradeno)}, '{tradetime}', '{date}', {float(price)}, " \
                  f"{int(quantity)}, '{buysell}', {int(openinterest)});"
        self.cursor.execute(request)

    def delete_line(self, symbol, date, var_qte=False, var_lte=False, var_eq=False):
        table_name = self.get_table_name(symbol, date)
        summary = sum(var_qte, var_lte, var_eq)
        assert summary == 1, "Ошибка выбора запроса в функции delete_line"
        if var_qte:
            self.cursor.execute(f"delete from {table_name} where tradetime>='{date}';")
        elif var_lte:
            self.cursor.execute(f"delete from {table_name} where tradetime<='{date}';")
        elif var_eq:
            self.cursor.execute(f"delete from {table_name} where tradetime=='{date}';")

    def drop_database(self, table_name):
        self.cursor.execute(f"drop table {table_name};")


class TickGetter(ConnectorPostgres):
    """Класс получает тики из БД по планировщику, делит их побарно и формирует из баров график"""
    def __init__(self, symbol, tf_sec):
        super().__init__()
        self.symbol = symbol  # формат seccode т.е. SiH1
        self.tf_sec = tf_sec
        self.mongo = ConnectorMongo()
        self.date_start = self._get_date_start()
        self.scheduler, self.dates_for_request = self.get_time_scheduler(self.tf_sec, self.date_start)
        self.scheduler_index = 0
        self.ticks = []
        self.df_ticks = pd.DataFrame()

    def manager_getting_ticks_from_db(self):
        """основной управляющий метод"""
        self.update_scheduler()
        len_chart = self.mongo.get_len_collection(self.symbol, self.tf_sec)
        if len_chart == 0:
            self.get_scheduler_index_now(1)
            self.ticks_request()
            self.update_chart(0)
        elif len_chart > 0:
            time_last_bar = self.mongo.get_last_bar(self.symbol, self.tf_sec)['time_open']
            # index_next_bar хранит индекс начала следующего бара за имеющимся в чарте
            index_next_bar = self.scheduler.index(time_last_bar) + 1
            # self.scheduler_index хранит индекс начала текущего формирующегося бара
            self.get_scheduler_index_now(index_next_bar)
            """если индекс текущего времени в планировщике  больше чем индекс последнего бара в монге (12736 и 866)"""
            if self.scheduler_index > index_next_bar:
                self.ticks_request(start=self.scheduler[index_next_bar])
                self.update_chart(index_next_bar)
            time.sleep(1)

    def _get_date_start(self):
        """определяет дату с которой начнется рассчет текущего планировщика"""
        if self.mongo.get_len_collection(self.symbol, self.tf_sec) == 0:
            return None
        else:
            return self.mongo.get_last_bar(self.symbol, self.tf_sec)['time_open']

    def update_scheduler(self):
        time_open_last_bar = self.mongo.get_last_bar(self.symbol, self.tf_sec).get('time_open')
        if dt.datetime.now() + dt.timedelta(seconds=self.tf_sec * 2) > self.scheduler[-1]:
            self.scheduler, self.dates_for_request = self.get_time_scheduler(self.tf_sec, time_open_last_bar,
                                                                             add_one_day=True)

    def get_scheduler_index_now(self, start_index):
        """Получает соотношение текущего времени и индекса планировщика"""
        time_now = dt.datetime.now()
        for i in range(start_index, len(self.scheduler)):
            if (time_now >= self.scheduler[i-1]) and (time_now < self.scheduler[i]):
                self.scheduler_index = i-1
                break
            else:
                continue

    def get_ticks_from_one_table(self, date, start, finish):
        """Получает набор тиков из одной таблицы за один день"""
        table_name, symbol, date = self.get_table_name(self.symbol, date)
        if self.exist_table(table_name):
            self.cursor.execute(
                f"select * from {table_name} where tradetime>='{start}' and tradetime<'{finish}';"
            )
            what_ret = self.cursor.fetchall()
            return what_ret
        return []

    def ticks_request(self, start=None):
        """Запрос на историю от начала планировщика до текущего индекса
        self.scheduler[self.scheduler_index] - текущее время по планировщику в формате datetime 2021-04-03 17:18:00
        """
        for date in self.dates_for_request:
            if self.scheduler[self.scheduler_index] >= date + dt.timedelta(days=1):
                """получение истории предыдущих дней"""
                if start:
                    self.ticks.extend(self.get_ticks_from_one_table(date, start, date + dt.timedelta(days=1)))
                elif not start:
                    self.ticks.extend(self.get_ticks_from_one_table(date, date, date + dt.timedelta(days=1)))
            elif self.scheduler[self.scheduler_index] < date + dt.timedelta(days=1):
                """получение истории текущего дня"""
                if start and (start < self.scheduler[self.scheduler_index]):
                    self.ticks.extend(self.get_ticks_from_one_table(date, start, self.scheduler[self.scheduler_index]))
                elif not start:
                    self.ticks.extend(self.get_ticks_from_one_table(date, date, self.scheduler[self.scheduler_index]))
        self.df_ticks = pd.DataFrame(self.ticks, columns=self.columns)
        self.ticks.clear()

    def update_chart(self, index_next_bar):
        """Создает чарт, т.е. добавляет в список чарта элементы класса бар"""
        if self.df_ticks[(self.df_ticks['tradetime'] >= self.scheduler[index_next_bar]) &
                         (self.df_ticks['tradetime'] < self.scheduler[self.scheduler_index])].empty:
            return
        for i in range(index_next_bar, self.scheduler_index):
            start = self.scheduler[i]
            finish = self.scheduler[i+1]
            ticks = self.df_ticks[(self.df_ticks['tradetime'] >= start) & (self.df_ticks['tradetime'] < finish)]
            if not ticks.empty:
                ticks = ticks.sort_values(by='tradetime', ascending=True).reset_index(drop=True)
                self.mongo.add_one_bar_in_collection(self.symbol, self.tf_sec,
                                                     Bar(ticks, start, self.tf_sec).get_document())


if __name__ == '__main__':
    pass
