import os
import pytz
# import mysql.connector
import pandas as pd
import psycopg2
import MetaTrader5 as mt5
import sqlite3 as sl3
import requests
from sqlalchemy import create_engine
import datetime as dt
from pygame import mixer
import time
import pickle

"""~~~~~~~~~~~~~~~~~~~~~~~~~~~Настройки создания первичного проекта базы данных~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
start_tf = 60
finish_tf = 3600
step_tf_sec = 15
date_contracts = "-9.21"
short_code = "U1"
symbols_splice_list = ['SBRF Splice', 'GOLD Splice', 'GAZR Splice', 'Si Splice', 'RTS Splice', 'ED Splice', 'Eu Splice',
                       'LKOH Splice', 'ROSN Splice', 'MXI Splice', 'VTBR Splice']
symbols_collect = {
    'fuchers': [
        {'big_vol_glass': 3000, 'long_code': f'Si{date_contracts}', 'short_code': f'Si{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},  # было 10000
        {'big_vol_glass': 600, 'long_code': f'SBRF{date_contracts}', 'short_code': f'SR{short_code}', 'big_bar_vol': 3000, 'big_delta': 1200, 'big_oi': 1200},  # было 1500
        {'big_vol_glass': 600, 'long_code': f'GAZR{date_contracts}', 'short_code': f'GZ{short_code}', 'big_bar_vol': 3000, 'big_delta': 1200, 'big_oi': 1200},  # было 1000
        {'big_vol_glass': 0, 'long_code': f'GOLD{date_contracts}', 'short_code': f'GD{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'RTS{date_contracts}', 'short_code': f'Ri{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'ED{date_contracts}', 'short_code': f'ED{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'Eu{date_contracts}', 'short_code': f'Eu{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'LKOH{date_contracts}', 'short_code': f'LH{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'ROSN{date_contracts}', 'short_code': f'RN{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'MXI{date_contracts}', 'short_code': f'MXI{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},
        {'big_vol_glass': 0, 'long_code': f'VTBR{date_contracts}', 'short_code': f'VB{short_code}', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000}
    ],
    'stocks': [
        {'big_vol_glass': 10000, 'long_code': 'SBER', 'short_code': 'SBER', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},  # было 40000
        {'big_vol_glass': 10000, 'long_code': 'GAZP', 'short_code': 'GAZP', 'big_bar_vol': 10000, 'big_delta': 10000, 'big_oi': 10000},  # было 40000
    ]
}

def get_symbol_description_dict():
    """Метод получает заданное описание символа и создает доступ к этому описанию по типу ключ значение"""
    big_vol = {}
    for var_symbol in list(symbols_collect.keys()):
        for symbol_description in symbols_collect[var_symbol]:
            big_vol[symbol_description['short_code']] = symbol_description
    return big_vol

fuchers_code_to_fuchers_name = {'SR': 'SBRF', 'GD': 'GOLD', 'GZ': 'GAZR', 'Si': 'Si', 'Ri': 'RTS', 'ED': 'ED',
                                'Eu': 'Eu', 'LH': 'LKOH', 'RN': 'ROSN'}
fuchers_mcode_to_fuchers_month = {'H': 3, 'M': 6, 'U': 9, 'Z': 12}
fuchers_fuchers_month_to_mcode = {3: 'H', 6: 'M', 9: 'U', 12: 'Z'}

symbols_splice_fuchers_dict = {'SBRF Splice': f'SBRF{date_contracts}', 'GOLD Splice': f'GOLD{date_contracts}',
                               'GAZR Splice': f'GAZR{date_contracts}', 'Si Splice': f'Si{date_contracts}',
                               'RTS Splice': f'RTS{date_contracts}', 'ED Splice': f'ED{date_contracts}',
                               'Eu Splice': f'Eu{date_contracts}', 'LKOH Splice': f'LKOH{date_contracts}',
                               'ROSN Splice': f'ROSN{date_contracts}', 'MXI Splice': f'MXI{date_contracts}',
                               'VTBR Splice': f'VTBR{date_contracts}'}

start_date_default = [2020, 6, 19, 0, 0, 0]
finish_date_default = [None, (2020, 6, 10, 3, 0, 0)]

direction_bar_dict = {'down_bar': 'down_bar', 'up_bar': 'up_bar', 'doj_bar': 'doj_bar'}
reverse_direction_bar_dict = {'down_bar': 'up_bar', 'up_bar': 'down_bar', 'doj_bar': 'doj_bar'}
reverse_direction_simple_dict = {'down': 'up', 'up': 'down'}
currency_list = ['EUR', 'USD', 'CAD', 'JPY', 'NZD', 'CHF', 'AUD', 'GBP']
full_tfs_enum_dict = {mt5.TIMEFRAME_M1: "tf_M1", mt5.TIMEFRAME_M2: "tf_M2", mt5.TIMEFRAME_M3: "tf_M3",
                      mt5.TIMEFRAME_M4: "tf_M4", mt5.TIMEFRAME_M5: "tf_M5", mt5.TIMEFRAME_M6: "tf_M6",
                      mt5.TIMEFRAME_M10: "tf_M10", mt5.TIMEFRAME_M12: "tf_M12", mt5.TIMEFRAME_M15: "tf_M15",
                      mt5.TIMEFRAME_M20: "tf_M20", mt5.TIMEFRAME_M30: "tf_M30", mt5.TIMEFRAME_H1: "tf_H1",
                      mt5.TIMEFRAME_H2: "tf_H2", mt5.TIMEFRAME_H3: "tf_H3",  mt5.TIMEFRAME_H4: "tf_H4",
                      mt5.TIMEFRAME_H6: "tf_H6", mt5.TIMEFRAME_H8: "tf_H8", mt5.TIMEFRAME_H12: "tf_H12",
                      mt5.TIMEFRAME_D1: "tf_D1", mt5.TIMEFRAME_W1: "tf_W1", mt5.TIMEFRAME_MN1: "tf_MN1"}
full_tfs_enum_list = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M2, mt5.TIMEFRAME_M3, mt5.TIMEFRAME_M4, mt5.TIMEFRAME_M5,
                      mt5.TIMEFRAME_M6, mt5.TIMEFRAME_M10, mt5.TIMEFRAME_M12, mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M20,
                      mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1, mt5.TIMEFRAME_H2, mt5.TIMEFRAME_H3, mt5.TIMEFRAME_H4,
                      mt5.TIMEFRAME_H6, mt5.TIMEFRAME_H8, mt5.TIMEFRAME_H12, mt5.TIMEFRAME_D1, mt5.TIMEFRAME_W1,
                      mt5.TIMEFRAME_MN1]
full_tfs_in_sec_dict = {mt5.TIMEFRAME_M1: 60, mt5.TIMEFRAME_M2: 120, mt5.TIMEFRAME_M3: 180,
                        mt5.TIMEFRAME_M4: 240, mt5.TIMEFRAME_M5: 300, mt5.TIMEFRAME_M6: 360,
                        mt5.TIMEFRAME_M10: 600, mt5.TIMEFRAME_M12: 720, mt5.TIMEFRAME_M15: 900,
                        mt5.TIMEFRAME_M20: 1200, mt5.TIMEFRAME_M30: 1800, mt5.TIMEFRAME_H1: 3600,
                        mt5.TIMEFRAME_H2: 7200, mt5.TIMEFRAME_H3: 10800,  mt5.TIMEFRAME_H4: 14400,
                        mt5.TIMEFRAME_H6: 21600, mt5.TIMEFRAME_H8: 28800, mt5.TIMEFRAME_H12: 43200,
                        mt5.TIMEFRAME_D1: 86400, mt5.TIMEFRAME_W1: 432000, mt5.TIMEFRAME_MN1: 1944000}
full_sec_in_tfs_dict = {60: mt5.TIMEFRAME_M1, 120: mt5.TIMEFRAME_M2, 180: mt5.TIMEFRAME_M3,
                        240: mt5.TIMEFRAME_M4, 300: mt5.TIMEFRAME_M5, 360: mt5.TIMEFRAME_M6,
                        600: mt5.TIMEFRAME_M10, 720: mt5.TIMEFRAME_M12, 900: mt5.TIMEFRAME_M15,
                        1200: mt5.TIMEFRAME_M20, 1800: mt5.TIMEFRAME_M30, 3600: mt5.TIMEFRAME_H1,
                        7200: mt5.TIMEFRAME_H2, 10800: mt5.TIMEFRAME_H3, 14400: mt5.TIMEFRAME_H4,
                        21600: mt5.TIMEFRAME_H6, 28800: mt5.TIMEFRAME_H8, 43200: mt5.TIMEFRAME_H12,
                        86400: mt5.TIMEFRAME_D1, 432000: mt5.TIMEFRAME_W1, 1944000: mt5.TIMEFRAME_MN1}

list_best_tf = [mt5.TIMEFRAME_H1, mt5.TIMEFRAME_H2, mt5.TIMEFRAME_H3, mt5.TIMEFRAME_H4,
                mt5.TIMEFRAME_H6, mt5.TIMEFRAME_H8, mt5.TIMEFRAME_H12, mt5.TIMEFRAME_D1]
mx_dict_st_point = {0: 1, 1: 1, 2: 10, 3: 100, 4: 1000, 5: 10000}
mx_dict_full_point = {0: 1, 1: 10, 2: 100, 3: 1000, 4: 10000, 5: 100000}

columns_in_table_bd = ['time_frame', 'symbol', 'tf', 'time_open', 'time_close', 'price_high',
                       'price_open', 'price_close', 'price_low', 'volume_real']

columns_in_table_bd_with_id = ['id', 'time_frame', 'symbol', 'tf', 'time_open', 'time_close', 'high',
                               'open', 'close', 'low', 'volume_real']


def get_name_tables():
    list_name_general_tables = ['tb_symbol_name', 'tb_tf_name', 'tb_common']
    name_table_symbols = list_name_general_tables[0]
    name_table_tfs = list_name_general_tables[1]
    name_table_common = list_name_general_tables[2]
    return name_table_symbols, name_table_tfs, name_table_common


def get_name_general_columns():
    list_columns_general_tables = ['symbol_name', 'tf_name', 'column_names_sym_tf']
    column_symbols = list_columns_general_tables[0]
    column_tfs = list_columns_general_tables[1]
    column_names_sym_tf = list_columns_general_tables[2]
    return column_symbols, column_tfs, column_names_sym_tf


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Общие межскриптовые функции~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""


def create_connect_db():
    """Подключение к postgree sql"""
    conn = psycopg2.connect(dbname='FX_TimeFrame', user='postgres', password='123', host='localhost', port=5432)
    conn.autocommit = True
    cur = conn.cursor()
    return conn, cur


def close_connect_db(connect, cursor):
    """Отключение от postgree sql"""
    cursor.close()
    connect.close()


def create_connect_db_sqlite3(terminal, file_path=""):
    """подключаюсь к бд sqlite3"""
    if terminal == 0:
        file_path = "..\\Files\\lvl.sqlite3"
    elif terminal == 1:
        file_path = "C:\\Program Files\\Открытие Брокер\\MQL5\Files\\lvl.sqlite3"
    conn = sl3.connect(file_path)
    cur = conn.cursor()
    return conn, cur


def close_connect_db_sqlite3(connect, cursor):
    """отключаюсь от бд"""
    connect.commit()
    cursor.close()
    connect.close()


def terminal_create_connect(terminal):
    if terminal == 0:
        terminal_path = "C:\\Terminals\\Alpari_MT5_One\\terminal64.exe"
    elif terminal == 1:
        terminal_path = "C:\\Terminals\\Open_Broker\\terminal64.exe"

    while not mt5.initialize(terminal_path):
        print('Ошибка соединения с терминалом MetaTrader5, пробую переподключиться')
        print(mt5.version())
        mt5.shutdown()
        time.sleep(1)


def terminal_close_connect():
    if mt5.shutdown():
        pass
    else:
        print('\n')
        print('Ошибка закрытия соединения')


def create_alchemy_connect():
    return create_engine('postgresql+psycopg2://postgres:123@localhost/FX_TimeFrame')


def close_alchemy_connect(engine):
    engine.dispose()


# def create_mysql_connect():
#     conn = mysql.connector.connect(host='127.0.0.1',database='market_data',
#                                    user='root',password='12345')
#     cur = conn.cursor()
#     return conn, cur


def close_mysql_connect(conn, cur):
    cur.close()
    conn.close()


def universal_request_to_bd(request, terminal, return_data=False):
    """Функция выполняет указанный запрос, универсальная"""
    conn, cur = create_connect_db_sqlite3(terminal)
    cur.execute(request)
    if return_data:
        all_lines = cur.fetchall()
        close_connect_db_sqlite3(conn, cur)
        return all_lines
    close_connect_db_sqlite3(conn, cur)


def get_tf_sec_from_time(timedelta):
    timedelta_str_list = timedelta.split(':')
    seconds = int(timedelta_str_list[0]) * 3600 + int(timedelta_str_list[1]) * 60 + int(timedelta_str_list[2])
    return seconds


def get_tf_standart(timedelta):
    timedelta_str_list = str(timedelta).split(':')
    timedelta_str_list[0] = str(int(timedelta_str_list[0].split(' days ')[1]))
    tf = f"tf_{timedelta_str_list[0]}_{timedelta_str_list[1]}_{timedelta_str_list[2]}"
    return tf


def get_timedelta(tf):
    """Получаю таймдельту из строки таймфрейма"""
    timedelta_str_list = tf.lstrip('tf_').replace('_', ':').split(':')
    seconds = int(timedelta_str_list[0])*3600 + int(timedelta_str_list[1])*60 + int(timedelta_str_list[2])
    return dt.timedelta(seconds=seconds)


def get_timedelta_sec(tf):
    """Получаю секунды из строки таймфрейма"""
    timedelta_str_list = tf.lstrip('tf_').replace('_', ':').split(':')
    return int(timedelta_str_list[0])*3600 + int(timedelta_str_list[1])*60 + int(timedelta_str_list[2])


def get_tf_from_timedelta(sec):
    time_list = str(dt.timedelta(seconds=sec)).split(':')
    return f"tf_{time_list[0]}_{time_list[1].lstrip('0')}_{time_list[2]}"


def get_all_symbols():
    conn, cur = create_connect_db()
    name_table_symbols, name_table_tfs, name_table_common = get_name_tables()
    cur.execute(
        f"select * from {name_table_symbols};"
    )
    symbols_list_l = [symbol for id_symbol, symbol in cur.fetchall()]
    return symbols_list_l


def get_all_tfs():
    conn, cur = create_connect_db()
    name_table_symbols, name_table_tfs, name_table_common = get_name_tables()
    cur.execute(
        f"select * from {name_table_tfs};"
    )
    tfs_list = [tf for id_tf, tf in cur.fetchall()]
    return tfs_list


def save_object(what_save, full_name):
    with open(f"{full_name}", "wb") as f:
        p_obj = pickle.Pickler(f)
        p_obj.dump(what_save)


def load_object(full_name):
    with open(f"{full_name}", "rb") as f:
        p_obj = pickle.Unpickler(f)
        return p_obj.load()


def save_in_log_file(msg, full_file_name):
    with open(f"{full_file_name}", "a+") as f:
        f.write(f"{msg}\n\n")


def save_html(data, log, direct_pos='', add_time=False):
    with open(f'logs\\{log}.html', 'a') as f:
        f.write('<br>')
        if isinstance(data, pd.DataFrame):
            if add_time:
                f.write(str(dt.datetime.now()))
            data.to_html(buf=f)
        else:
            if not direct_pos == '':
                f.write(f"{direct_pos}: {str(data)}")
            else:
                f.write(str(data))


def get_line_splitter():
    line = ('~'*110)
    return line


def get_log_name(develop=False, ts_log=False, name_ts_log=''):
    time_tuple = dt.datetime.now().timetuple()
    if ts_log:
        return f'log_{name_ts_log}_{time_tuple.tm_year}-{time_tuple.tm_mon}-{time_tuple.tm_mday}'
    elif develop:
        return f'log_dev_{time_tuple.tm_year}-{time_tuple.tm_mon}-{time_tuple.tm_mday}'
    else:
        return f'log_{time_tuple.tm_year}-{time_tuple.tm_mon}-{time_tuple.tm_mday}'


def get_time_frame_marking(sec_tf):
    """Возвращает список таймфрейм"""
    return [dt.datetime(dt.date.today().year, dt.date.today().month,
            dt.date.today().day) + dt.timedelta(seconds=sec_tf)*t for t in range(int(86400/sec_tf + 2))]


def get_time_control_counter(time_frame_list):
    """Возвращает порядковый номер промежутка в котором находится время в текущий момент"""
    counter = 0
    while dt.datetime.now() > time_frame_list[counter]:
        counter += 1
    return counter - 1


def night_filter():
    """Функция ночной фильтр времени"""
    time_now = dt.datetime.now()
    allowed_trade = False
    if (time_now.hour >= 9) and (time_now.hour < 20):
        allowed_trade = True
    return allowed_trade


def time_frame_control(main_tf_sec, func, tf_main=0, tm_sleep=30):
    """стартовый контроль времени по указанному таймфрейму"""
    time_frame_list = get_time_frame_marking(sec_tf=main_tf_sec)
    tm_control_counter = get_time_control_counter(time_frame_list)

    """основной программный цикл"""
    while True:
        if dt.datetime.now() > time_frame_list[tm_control_counter]:
            """Блок запуска функций"""
            tm_control_counter += 1
            func(tf_main)
            print(dt.datetime.now(), time_frame_list[tm_control_counter], tm_control_counter)

            """Конец блока запуска функций"""

            if tm_control_counter == len(time_frame_list) - 1:
                time_frame_list = get_time_frame_marking(sec_tf=main_tf_sec)
                tm_control_counter = get_time_control_counter(time_frame_list)
        time.sleep(tm_sleep)


def get_open_mini_show(row):
    """функция возвращает является ли указанный бар опен мини"""
    percent = (row.at['high']-row.at['low'])*0.15
    if row.at['close'] < row.at['open']:
        rz = row.at['high']-row.at['open']
        if rz <= percent:
            return True
        else:
            return False
    elif row.at['close'] > row.at['open']:
        rz = row.at['open']-row.at['low']
        if rz <= percent:
            return True
        else:
            return False
    else:
        return False


def get_direction_bar(pr_open, pr_close):
    """Функция возвращает направление бара"""
    direct_bar = pr_open - pr_close
    if direct_bar > 0:
        return direction_bar_dict['down_bar']
    elif direct_bar < 0:
        return direction_bar_dict['up_bar']
    elif direct_bar == 0:
        return direction_bar_dict['doj_bar']


def get_percent_price(price, percent_0, percent_25, percent_50, percent_75, percent_100):
    """Вспомогательная функция get_bar_variant"""
    pr_bar = 0
    if (price >= percent_0) and (price < percent_25):
        pr_bar = 25
    elif (price >= percent_25) and (price < percent_50):
        pr_bar = 50
    elif (price >= percent_50) and (price < percent_75):
        pr_bar = 75
    elif (price >= percent_75) and (price <= percent_100):
        pr_bar = 99
    return pr_bar


def get_bar_variant(row):
    """функция определяющая вариант переданной на анализ свечи(строки датафрейма)"""
    high_low = row.at['high'] - row.at['low']
    high_low_25per = high_low / 4

    percent_0 = row.at['low']
    percent_25 = percent_0 + high_low_25per
    percent_50 = percent_0 + high_low_25per * 2
    percent_75 = percent_0 + high_low_25per * 3
    percent_100 = row.at['high']

    pr_close = row.at['close']
    pr_open = row.at['open']
    op_bar = get_percent_price(pr_open, percent_0, percent_25, percent_50, percent_75, percent_100)
    cl_bar = get_percent_price(pr_close, percent_0, percent_25, percent_50, percent_75, percent_100)
    return f"{op_bar}_{cl_bar}"


def get_bar_variant_10(row):
    """функция определяющая 10% вариант переданной на анализ свечи(строки датафрейма)"""
    high_low = row.at['high'] - row.at['low']
    high_low_10_percent = high_low / 10
    list_price = [row.at['open'], row.at['close']]
    for n_price in range(len(list_price)):
        for i in range(1, 11):
            high_border = high_low_10_percent * i + row.at['low']
            low_border = high_low_10_percent * (i-1) + row.at['low']
            if (list_price[n_price] >= low_border) and (list_price[n_price] <= high_border):
                list_price[n_price] = (i-1) * 10
    return f"{list_price[0]}_{list_price[1]}"


def dop_columns_for_rates(df):
    """Функция дополняющая Rates DF дополнительными постоянно используемыми столбцами"""
    df['open_mini'] = df.apply(get_open_mini_show, axis=1)
    df['bar_direct'] = df.apply(lambda row: get_direction_bar(row.at['open'], row.at['close']), axis=1)
    df['bar_var'] = df.apply(lambda row: get_bar_variant(row), axis=1)
    df['atr_bar'] = df.apply(lambda row: row.at['high'] - row.at['low'], axis=1)
    df['hour'] = df.apply(lambda row: row.at['time'].hour, axis=1)
    df['minute'] = df.apply(lambda row: row.at['time'].minute, axis=1)
    df['weekday'] = df.apply(lambda row: row.at['time'].weekday(), axis=1)
    df['date'] = df.apply(lambda row: dt.datetime(row.at['time'].year, row.at['time'].month, row.at['time'].day), axis=1)
    df['bar_var_10'] = df.apply(get_bar_variant_10, axis=1)
    return df


def get_bars_one_tf(symbol, tf_e, start_pos_or_date_bar, qv_bars, terminal, copy_date=False):
    """Получаю датафрейм с барами один символ и один таймфрейм"""
    count = 0
    rates_frame = pd.DataFrame()
    if symbol_is_format_code(symbol):
        symbol = get_symbol_format_terminal(symbol)
    while rates_frame.empty:
        terminal_create_connect(terminal)
        count += 1
        if not copy_date:
            rates_frame = pd.DataFrame(mt5.copy_rates_from_pos(symbol, tf_e, start_pos_or_date_bar, qv_bars))
        elif copy_date:
            rates_frame = pd.DataFrame(mt5.copy_rates_range(symbol, tf_e, start_pos_or_date_bar, qv_bars))
        terminal_close_connect()
        if count >= 2:
            print(f"пробую получить данные с терминала get_bars_one_tf...{count}")
            terminal_close_connect()
        if count >= 30:
            print("ошибка получения данных с терминала get_bars_one_tf... Более 30 неудачных попыток")
            break
    # создадим из полученных данных DataFrame
    rates_frame['symbol'] = symbol
    rates_frame['tf'] = full_tfs_enum_dict[tf_e]
    rates_frame['tf_int'] = tf_e
    rates_frame['tf_sec'] = full_tfs_in_sec_dict[tf_e]
    if not rates_frame.empty:
        rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
        rates_frame = dop_columns_for_rates(rates_frame)
        symbol_info = get_symbol_info(symbol, terminal)
        return rates_frame, symbol_info
    terminal_close_connect()
    return pd.DataFrame(), None


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ATR индикаторы~~~~~~~~~~~~~~~~~~~~~~~~~"""


def get_atr_bar_and_atr_fractals_mean(rates_frame, period, digits):
    """Функция считает АТР за указанный период и присваивает его значение бару от которого был произведен отсчет
    далее считает фракталы от АТР, возвращает основной ДФ с дополнениями и среднее значение фракталов.
    """
    rates_frame[f'atr_{period}'] = 0
    rates_frame[f'atr_fr_low_{period}'] = False
    rates_frame[f'atr_fr_high_{period}'] = False

    """Получаю атр каждого бара"""
    for n_row in rates_frame.index:
        if n_row < period:
            continue
        sum_dif = 0
        for n_bar in range(period):
            dif_high_low = rates_frame.iloc[n_row-n_bar].at['high'] - rates_frame.iloc[n_row-n_bar].at['low']
            sum_dif += dif_high_low
        atr_one_period = round(sum_dif / period, digits)
        rates_frame.loc[n_row, f'atr_{period}'] = atr_one_period

    """Получаю столбец является ли фракталом АТР бар"""
    for index_row in rates_frame.index:
        if (index_row < 1) or (index_row >= len(rates_frame.index)-2):
            continue
        if (rates_frame.loc[index_row-1, f'atr_{period}'] > rates_frame.loc[index_row, f'atr_{period}']) and \
           (rates_frame.loc[index_row+1, f'atr_{period}'] > rates_frame.loc[index_row, f'atr_{period}']) and \
           (rates_frame.loc[index_row+2, f'atr_{period}'] > rates_frame.loc[index_row+1, f'atr_{period}']):
            rates_frame.loc[index_row, f'atr_fr_low_{period}'] = True
        if (rates_frame.loc[index_row-1, f'atr_{period}'] < rates_frame.loc[index_row, f'atr_{period}']) and \
           (rates_frame.loc[index_row+1, f'atr_{period}'] < rates_frame.loc[index_row, f'atr_{period}']) and \
           (rates_frame.loc[index_row+2, f'atr_{period}'] < rates_frame.loc[index_row+1, f'atr_{period}']):
            rates_frame.loc[index_row, f'atr_fr_high_{period}'] = True

    """Получаю срез по фракталам АТР и далее считаю среднее."""
    atr_fr_high = rates_frame.loc[rates_frame[f'atr_fr_high_{period}']]
    atr_fr_low = rates_frame.loc[rates_frame[f'atr_fr_low_{period}']]
    max_atr = round(atr_fr_high[f'atr_{period}'].mean(), digits)
    min_atr = round(atr_fr_low[f'atr_{period}'].mean(), digits)

    """Получаю атр последних 3 баров"""
    last_atr = round(rates_frame[-3:][f'atr_{period}'].mean(), digits)

    """Считаю средний атр по таймфрейму"""
    mean_atr_tf = round((max_atr+min_atr)/2, digits)
    return rates_frame, last_atr, mean_atr_tf, max_atr, min_atr


def get_account_info(terminal):
    """Функция получает все параметры счета."""
    terminal_create_connect(terminal)
    account_info = mt5.account_info()
    while not account_info:
        account_info = mt5.account_info()
        print("Не могу получить информацию об аккаунте get_account_info")
    terminal_close_connect()
    return account_info._asdict()


def get_symbol_info(symbol, terminal):
    """Функция получает все параметры символа."""
    terminal_create_connect(terminal)
    if symbol_is_format_code(symbol):
        symbol = get_symbol_format_terminal(symbol)
    symbol_info = mt5.symbol_info(symbol)
    while not symbol_info:
        terminal_close_connect()
        terminal_create_connect(terminal)
        symbol_info = mt5.symbol_info(symbol)
        print("Не могу получить информацию об символе get_symbol_info")
        terminal_close_connect()
    terminal_close_connect()
    return symbol_info._asdict()


# def get_correct_symbol_sequence(terminal, fuchers=False):
#     """возвращает правильную последовательность символов в зависимости от терминала"""
#     if terminal == 1:
#         if fuchers:
#             return symbols_fuchers_list[3:4]
#         return symbols_splice_list[:4]


def get_symbol_var(symbol):
    """функция переводящая имя фьючерса в имя для базы данных"""
    return [symbol, symbol.replace('-', '_').replace('.', '_')]


def update_atr_global_lib(n_terminal):
    """функция от get_atr_last_bar, обновляет библиотку средней волатильности"""
    if os.path.isfile("additional_files\\atr_global_lib.lib"):
        atr_global_lib = load_object("additional_files\\atr_global_lib.lib")
    else:
        atr_global_lib = {}

    if n_terminal == 1:
        symbol_list = symbols_splice_list

    for symbol in symbol_list:
        atr_global_lib[symbol] = {}
        for tf in full_tfs_enum_list:
            df_one_bar, symbol_info = get_bars_one_tf(symbol, tf, 1, 250, n_terminal)
            mean_atr = round(df_one_bar.atr_bar.mean(), symbol_info['digits'])
            atr_global_lib[symbol][full_tfs_enum_dict[tf]] = {'atr': mean_atr}
    print(atr_global_lib)
    save_object(atr_global_lib, "additional_files\\atr_global_lib.lib")


def get_atr_global_lib(terminal):
    """Функция подключает глобальную АТР библиотеку, если ее не нашел на диске значит создает заново"""
    if os.path.isfile("additional_files\\atr_global_lib.lib"):
        atr_global_lib = load_object("additional_files\\atr_global_lib.lib")
    else:
        print("Нет библиотеки с АТР. Запускаю скрипт ее создания.")
        update_atr_global_lib(terminal)
        atr_global_lib = load_object("additional_files\\atr_global_lib.lib")
    return atr_global_lib


"""**********************************************Алертблок********************************"""


def play_alert(file_name='file.mp3', duration_secs=2):
    soundfile = 'additional_files\\audio\\'+file_name
    mixer.init()
    mixer.music.load(soundfile)
    mixer.music.play()
    time.sleep(duration_secs)
    mixer.music.stop()
    mixer.quit()


def logging(message, alert=False):
    """функция оповещения"""
    send_message_bot(message)
    print(message)
    if alert:
        play_alert(file_name='error.mp3', duration_secs=3)


def global_alert_control_dict_init(global_alert_control_dict, strategy, symbol, tf):
    """общая функция инициализирующая словарь контроля алертов"""
    if not global_alert_control_dict.get(strategy):
        global_alert_control_dict[strategy] = {symbol: {tf: {}}}
    elif not global_alert_control_dict.get(strategy).get(symbol):
        global_alert_control_dict[strategy][symbol] = {tf: {}}
    elif not global_alert_control_dict.get(strategy).get(symbol).get(tf):
        global_alert_control_dict[strategy][symbol][tf] = {}
    return global_alert_control_dict


def common_save_and_play(global_alert_control_dict, strategy, symbol, tf, alert_list_tuples, message="",
                         print_message=False, send_message=False):
    """Функция объединяющая проверку словаря контроля, записи и алерта"""
    if not global_alert_control_dict[strategy][symbol][tf].get('time_control'):
        global_alert_control_dict = save_and_play(global_alert_control_dict, strategy, symbol, tf, alert_list_tuples,
                                                  message=message, print_message=print_message,
                                                  send_message=send_message)
    elif global_alert_control_dict[strategy][symbol][tf].get('time_control'):
        if global_alert_control_dict[strategy][symbol][tf]['time_control'] < dt.datetime.now():
            global_alert_control_dict = save_and_play(global_alert_control_dict, strategy, symbol, tf,
                                                      alert_list_tuples, message=message, print_message=print_message,
                                                      send_message=send_message)
    return global_alert_control_dict


def save_and_play(global_alert_control_dict, strategy, symbol, tf, alert_list_tuples, message="",
                  print_message=False, send_message=False):
    """Общая фукция от для воспроизведения и контроля алертов"""
    for alert in alert_list_tuples:
        play_alert(file_name=alert[0], duration_secs=alert[1])
    global_alert_control_dict[strategy][symbol][tf]['time_control'] = dt.datetime.now() + \
        dt.timedelta(seconds=int(full_tfs_in_sec_dict[tf] / 12))
    if print_message:
        print(message)
    if send_message:
        logging(message)
    return global_alert_control_dict


"""******************************************Важные функции********************************"""

# def alert_lvl_control(global_alert_control_dict, terminal, only_m1=False, alert=False):
#     """Функция выдающая алерт при подходе к уровню, и возвращающая словарь с данными удара в уровень"""
#     symbol_list = get_correct_symbol_sequence(terminal, fuchers=True)
#     columns_bd_lvl = ['id', 'symbol', 'tf_int', 'tf_sec', 'lvl_price']
#     signals_dict = {}
#     for symbol in symbol_list:
#         symbol_var = get_symbol_var(symbol)
#         if terminal == 1: var = 1
#         elif terminal == 0: var = 0
#         try:
#             data = universal_request_to_bd(f"select * from symbol_{symbol_var[var]};", terminal, return_data=True)
#         except sl3.OperationalError:
#             print(f"Ошибка получения датафрейма {symbol}")
#             continue
#         df_bd = pd.DataFrame(data=data, columns=columns_bd_lvl)
#         set_lvl = set(df_bd.lvl_price.to_list())
#         tfs_in_pips_dict = {mt5.TIMEFRAME_M1: 3, mt5.TIMEFRAME_M2: 3, mt5.TIMEFRAME_M3: 3,
#                             mt5.TIMEFRAME_M4: 3, mt5.TIMEFRAME_M5: 3, mt5.TIMEFRAME_M6: 3,
#                             mt5.TIMEFRAME_M10: 3, mt5.TIMEFRAME_M12: 4, mt5.TIMEFRAME_M15: 5,
#                             mt5.TIMEFRAME_M20: 7, mt5.TIMEFRAME_M30: 8, mt5.TIMEFRAME_H1: 16,
#                             mt5.TIMEFRAME_H2: 16, mt5.TIMEFRAME_H3: 18, mt5.TIMEFRAME_H4: 20,
#                             mt5.TIMEFRAME_H6: 20, mt5.TIMEFRAME_H8: 20, mt5.TIMEFRAME_H12: 22,
#                             mt5.TIMEFRAME_D1: 25, mt5.TIMEFRAME_W1: 30, mt5.TIMEFRAME_MN1: 30}
#         """Общий блок оповещения о том, что цена подошла к уровню"""
#         rates_frame, symbol_info = get_bars_one_tf(symbol, mt5.TIMEFRAME_M1, 1, 1, terminal)
#         last_price = rates_frame.iloc[-1].at['close']
#         point = symbol_info['point']
#         for lvl in set_lvl:
#             lvl_high = lvl + 3 * point
#             lvl_low = lvl - 3 * point
#             if (last_price >= lvl_low) and (last_price <= lvl_high) and alert:
#                 play_alert(file_name="price_in_lvl_range.mp3", duration_secs=5)
#                 play_alert(file_name=f"{symbol.split('-')[0].split()[0]}.mp3", duration_secs=5)
#                 print(f"На символе {symbol} цена подошла к уровню {lvl}. {dt.datetime.now()}")
#
#         """Частный блок оповещения о том, что цена уперлась в уровень"""
#         if only_m1:
#             list_tfs = full_tfs_enum_list[0:1]
#         else:
#             list_tfs = full_tfs_enum_list[:-2]
#         for tf_mini in list_tfs:
#             rates_frame, symbol_info = get_bars_one_tf(symbol, tf_mini, 1, 1, terminal)
#             high_price = rates_frame.iloc[-1].at['high']
#             low_price = rates_frame.iloc[-1].at['low']
#             open_price = rates_frame.iloc[-1].at['open']
#             close_price = rates_frame.iloc[-1].at['close']
#             point = symbol_info['point']
#             strategy = "hit_in_lvl"
#             global_alert_control_dict = global_alert_control_dict_init(global_alert_control_dict, strategy, symbol, tf_mini)
#             alert_list_tuples = [("hit_in_lvl.mp3", 3), (f"{full_tfs_enum_dict[tf_mini]}.mp3", 4),
#                                  (f"{symbol.split('-')[0].split()[0]}.mp3", 3)]
#             for lvl in set_lvl:
#                 lvl_high_border = lvl + tfs_in_pips_dict[tf_mini] * point
#                 lvl_low_border = lvl - tfs_in_pips_dict[tf_mini] * point
#                 if ((open_price >= lvl) and (close_price >= lvl)) and \
#                    ((low_price >= lvl) and (low_price <= lvl_high_border)):
#                     signals_dict[symbol] = {"gen_lvl": lvl, "lvl_high_border": lvl_high_border, "point": point,
#                                             "lvl_low_border": lvl_low_border, "rates_frame": rates_frame,
#                                             "offset_pips": tfs_in_pips_dict[tf_mini], "signal_direct": "up"}
#                     message = f"На символе {symbol} удар в уровень сверху {lvl} {full_tfs_enum_dict[tf_mini]}. {dt.datetime.now()}"
#                     if alert:
#                         global_alert_control_dict = common_save_and_play(global_alert_control_dict, strategy, symbol,
#                                                                          tf_mini, alert_list_tuples, message=message,
#                                                                          print_message=True, send_message=True)
#                 elif ((open_price <= lvl) and (close_price <= lvl)) and \
#                      ((high_price <= lvl) and (high_price >= lvl_low_border)):
#                     signals_dict[symbol] = {"gen_lvl": lvl, "lvl_high_border": lvl_high_border, "point": point,
#                                             "lvl_low_border": lvl_low_border, "rates_frame": rates_frame,
#                                             "offset_pips": tfs_in_pips_dict[tf_mini], "signal_direct": "down"}
#                     message = f"На символе {symbol} удар в уровень снизу {lvl} {full_tfs_enum_dict[tf_mini]}. {dt.datetime.now()}"
#                     if alert:
#                         global_alert_control_dict = common_save_and_play(global_alert_control_dict, strategy, symbol,
#                                                                          tf_mini, alert_list_tuples, message=message,
#                                                                          print_message=True, send_message=True)
#     return global_alert_control_dict, signals_dict


def get_lvl_from_bd(symbol, terminal):
    """функция возвращает уровни из бд по одному указанному символу"""
    columns_bd_lvl = ['id', 'symbol', 'tf_int', 'tf_sec', 'lvl_price']
    data = ()
    try:
        data = universal_request_to_bd(f"select * from symbol_{symbol};", terminal, return_data=True)
    except sl3.OperationalError:
        print(f"Ошибка получения датафрейма {symbol}")
    df_bd = pd.DataFrame(data=data, columns=columns_bd_lvl)
    return df_bd


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Блок фрактального поиска уровней и их обработка~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
"Главная функция: finder_market_lvl_and_update_database, остальные вспомогательные."


def bar_fractal(n_row, rates_frame, var_fractal):
    """Допфункция к get_first_fractal_df, определяет бар фрактал или нет"""
    direct_0 = rates_frame.iloc[n_row].at[var_fractal]
    direct_m1 = rates_frame.iloc[n_row-1].at[var_fractal]
    direct_p1 = rates_frame.iloc[n_row+1].at[var_fractal]
    if (direct_0 > direct_m1) and (direct_0 > direct_p1) and (var_fractal == "high"):
        return True
    elif (direct_0 < direct_m1) and (direct_0 < direct_p1) and (var_fractal == "low"):
        return True
    return False


def get_first_fractal_df(rates_frame):
    """Функция от get_lvl_df получает первичный фрактальный датафрейм"""
    first_fractal_df = pd.DataFrame()
    rates_frame['fractal_var'] = ''
    for n_row in range(1, len(rates_frame)-1):
        fractal_high = bar_fractal(n_row, rates_frame, "high")
        fractal_low = bar_fractal(n_row, rates_frame, "low")
        if fractal_high:
            first_fractal_df = first_fractal_df.append(rates_frame.iloc[n_row])
            first_fractal_df['fractal_var'].iat[-1] = 'f_high'
        elif fractal_low:
            first_fractal_df = first_fractal_df.append(rates_frame.iloc[n_row])
            first_fractal_df['fractal_var'].iat[-1] = 'f_low'
    first_high_fractal_df = first_fractal_df.loc[first_fractal_df['fractal_var'] == 'f_high']
    first_low_fractal_df = first_fractal_df.loc[first_fractal_df['fractal_var'] == 'f_low']
    return first_fractal_df, first_high_fractal_df, first_low_fractal_df


def get_fractal_lvl(first_var_fractal_df, lvl, var_fractal):
    """Функция от get_lvl_df получает уровневый фрактальный датафрейм"""
    new_lvl = first_var_fractal_df
    for n_lvl in range(lvl):
        start_lvl = new_lvl
        new_df = pd.DataFrame()
        for n_row in range(1, len(start_lvl)-1):
            fractal = bar_fractal(n_row, start_lvl, var_fractal)
            if fractal:
                new_df = new_df.append(start_lvl.iloc[n_row])
        new_lvl = new_df.copy()
        print(f"Уровень {n_lvl}, длина уровня: {len(new_lvl)}")
        del new_df
    return new_lvl


def get_common_lvl(fractal_lvl_high_df, fractal_lvl_low_df):
    """Функция от get_lvl_df возвращает общий df"""
    df = pd.DataFrame()
    df = df.append([fractal_lvl_high_df, fractal_lvl_low_df])
    df = df.reset_index()
    df = df.sort_values(by='index', ascending=True)
    df = df.reset_index(drop=True)
    return df


def get_lvl_df(symbol, tf_e, start, finish, terminal):
    """Основная функция от get_df_with_all_lvl"""
    # Получаю датафрейм с барами
    rates_frame, symbol_info = get_bars_one_tf(symbol, tf_e, start, finish, terminal)
    # Получаю первичный датафрейм с точками фракталов. Общий, хай фракталы и лоу фракталы
    first_fractal_df, first_high_fractal_df, first_low_fractal_df = get_first_fractal_df(rates_frame)
    # Получаю указанный уроверь фракталов
    fractal_lvl_high_df = get_fractal_lvl(first_high_fractal_df, 3, 'high')
    fractal_lvl_low_df = get_fractal_lvl(first_low_fractal_df, 3, 'low')
    fractal_lvl_common_df = get_common_lvl(fractal_lvl_high_df, fractal_lvl_low_df)
    return fractal_lvl_common_df


def db_create(symbol, terminal):
    """функция от finder_market_lvl_and_update_database, пересоздает таблицу в бд"""
    conn, cur = create_connect_db_sqlite3(terminal)
    cur.execute(
        f"drop table if exists symbol_{symbol};"
    )
    cur.execute(
        f"create table if not exists symbol_{symbol} ("
        f"id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
        f"symbol text (50),"
        f"timeframe_int int,"
        f"timeframe_str text (20),"
        f"price_lvl real);")
    close_connect_db_sqlite3(conn, cur)


def add_lvl_in_bd(df, symbol_table_name, terminal):
    """функция от finder_market_lvl_and_update_database, добавляет уровни в базу данных"""
    symbol = df.iloc[0].at['symbol']
    "here processing response list and comparison with response from database"
    for line in df.index:
        timeframe_int = int(df.loc[line, 'tf_int'])
        timeframe_str = df.loc[line, 'tf']
        fractal_var = df.loc[line, 'fractal_var']
        if fractal_var == "f_high":
            price_lvl = df.loc[line, 'high']
        elif fractal_var == "f_low":
            price_lvl = df.loc[line, 'low']
        request = f"insert into symbol_{symbol_table_name} " \
                  f"(symbol, timeframe_int, timeframe_str, price_lvl) values " \
                  f"('{symbol}', {timeframe_int}, '{timeframe_str}', {price_lvl});"
        universal_request_to_bd(request, terminal)


def get_df_with_all_lvl(symbol, terminal):
    """общая функция от finder_market_lvl_and_update_database,
    для всех рынков для получения всех уровней в одном датафрейме"""
    fractal_lvl_common_df_sum = pd.DataFrame()
    for req in [{'tf': mt5.TIMEFRAME_M15, 'start': 200, 'finish': 2000},
                {'tf': mt5.TIMEFRAME_H1, 'start': 100, 'finish': 2000},
                {'tf': mt5.TIMEFRAME_D1, 'start': 30, 'finish': 1500},
                {'tf': mt5.TIMEFRAME_W1, 'start': 8, 'finish': 400},
                {'tf': mt5.TIMEFRAME_MN1, 'start': 2, 'finish': 60}]:
        fractal_lvl_common_df = get_lvl_df(symbol, req['tf'], req['start'], req['finish'], terminal)
        fractal_lvl_common_df_sum = fractal_lvl_common_df_sum.append(fractal_lvl_common_df)
    for tf in [mt5.TIMEFRAME_W1, mt5.TIMEFRAME_MN1]:
        rates_frame, symbol_info = get_bars_one_tf(symbol, tf, 1, 2, terminal)
        rates_frame['fractal_var'] = ""
        rates_frame_new = pd.DataFrame()
        for i in range(2):
            rates_frame_new = rates_frame_new.append(rates_frame.iloc[-1])
        rates_frame_new['fractal_var'].iat[-1] = 'f_high'
        rates_frame_new['fractal_var'].iat[0] = 'f_low'
        fractal_lvl_common_df_sum = fractal_lvl_common_df_sum.append(rates_frame_new)
        fractal_lvl_common_df_sum = fractal_lvl_common_df_sum.reset_index(drop=True)
    return fractal_lvl_common_df_sum


# def get_common_lvl_from_market(n_symbol, terminal):
#     """Функция от finder_market_lvl_and_update_database, преобразует датафрейм уровней для биржи"""
#     symbol = symbols_splice_list[n_symbol]
#     fractal_lvl_common_df_sum = get_df_with_all_lvl(symbol, terminal)
#     fractal_lvl_common_df_sum['symbol'] = symbols_fuchers_list[n_symbol]
#     symbol = symbols_fuchers_list[n_symbol].replace('-', '_').replace('.', '_')
#     return symbol, fractal_lvl_common_df_sum


# def finder_market_lvl_and_update_database(terminal):
#     """Основная функция для обработки рыночных уровней"""
#     if terminal == 1:
#         for n_symbol in range(0, 4): #rangelen(symbols_splice_list)):
#             print(symbols_splice_list[n_symbol])
#             symbol, fractal_lvl_common_df = get_common_lvl_from_market(n_symbol, terminal)
#             print(f"Символ перед подачей в базу: {symbol}")
#             db_create(symbol, terminal)
#             add_lvl_in_bd(fractal_lvl_common_df, symbol, terminal)


"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Следующий блок~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""


def get_bool_value_from_str(string: str):
    """функция возвращает правильное преобразование в bool тип"""
    value = string.strip()
    return True if value == 'true' else False


def get_symbol_format_terminal(symbol):
    """Преобразует формат символа SiM1 в Si-6.21"""
    return f"{fuchers_code_to_fuchers_name[symbol[:-2]]}-{fuchers_mcode_to_fuchers_month[symbol[-2]]}.2{symbol[-1]}"


def get_symbol_format_mcode(symbol):
    """преобразует формат Si-6.21 в SiM1"""
    symbol, month, year = symbol.replace('.', '-').split('-')
    return f"{symbol}{fuchers_fuchers_month_to_mcode[int(month)]}{year[-1]}"


def symbol_is_format_code(symbol):
    """Проверяет формат символа истина если символ фьючерс"""
    for i in list(fuchers_mcode_to_fuchers_month.keys()):
        if symbol[-2] == i:
            if '-' in symbol:
                return True
    return False


def symbol_is_terminal_variant(symbol):
    """Проверяет короткий или длинный формат"""
    for i in list(fuchers_mcode_to_fuchers_month.keys()):
        if symbol[-2] == i:
            try:
                int(symbol[-1])
                return False
            except Exception as e:
                print(e)
                return True
    return True

