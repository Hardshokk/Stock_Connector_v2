import sys
import time
from ctypes import *
import traceback
from functools import partial
import urllib.request as u_request
from PyQt5 import QtCore, QtWidgets
import common_files.common_functions as cf
import xml.etree.ElementTree as e_dom
import xml.dom.minidom as x_dom
from common_files.postgres import GetTicks
import datetime as dt


tr_lib = PyDLL("server\\txmlconnector64.dll")


class ConnectorTX:
    def __init__(self, main_self, raw_tick_queue, db_write_tick_queue, raw_quotes_queue):

        self.main_self = main_self
        self.log_path = 'transaq_logs\\'
        self.log_lvl = 3
        self.logs_period_live = 7
        self.running = True

        self.symbols_list_for_tick = self.main_self.symbols_list_for_tick
        self.symbols_list_for_quotes = self.main_self.symbols_list_for_quotes

        self.raw_tick_queue = raw_tick_queue
        self.db_write_tick_queue = db_write_tick_queue
        self.raw_quotes_queue = raw_quotes_queue
        self.get_last_tick_df = GetTicks()

    def save_exception_in_file(self, e):
        print("Сервер: \n", e)
        with open(f"{self.log_path}\\my_log.log", "a+") as f:
            f.writelines(traceback.format_exc())
            f.write("\n\n")

    @staticmethod
    def get_byte_str(str_request):
        """функция общего назначения получает байт строку для запроса"""
        buff_byte_str = create_string_buffer(str.encode(str_request, encoding="utf-8"))
        return buff_byte_str

    @staticmethod
    def print_msg_from_connector(response):
        """функция выводит сообщения передаваемые из библиотеки"""
        msg = string_at(response)
        msg = msg.decode(encoding="utf-8")
        print("Сервер: msg: ", msg)
        return msg

    def send_command(self, func_command):
        """В зависимости от нажатой кнопки получает функцию. Функция должна возвращать список команд"""
        commands = func_command()
        for command in commands:
            my_send_command = tr_lib.SendCommand
            my_send_command.restype = POINTER(c_char_p)
            result = tr_lib.SendCommand(command)
            msg = self.print_msg_from_connector(result)
            # можно получить какой вариант команды исполняется и передавать его в словаре чтобы фильтровать
            # статусы ответов для разных запросов. на даннай момент статусы меняются по последнему запросу
            self._get_result_command_send(msg)
            time.sleep(5)

    def _get_result_command_send(self, msg):
        main_elem = x_dom.parseString(msg).childNodes[0]
        self.last_status = cf.get_bool_value_from_str(main_elem.attributes['success'].value)

    @staticmethod
    def command_connect():
        main = e_dom.Element("command", attrib={'id': 'connect'})
        for edit_name in acc_info_dict.keys():
            param = e_dom.Element(edit_name, attrib={})
            param.text = acc_info_dict[edit_name]
            main.append(param)
        return [e_dom.tostring(main, encoding='utf-8')]

    @staticmethod
    def command_disconnect():
        return [e_dom.tostring(e_dom.Element("command", attrib={'id': 'disconnect'}))]

    @staticmethod
    def command_status_server():
        return [e_dom.tostring(e_dom.Element("command", attrib={'id': 'server_status'}))]

    @staticmethod
    def command_get_markets():
        return [e_dom.tostring(e_dom.Element("command", attrib={'id': 'get_markets'}))]

    @staticmethod
    def command_get_difference_time():
        return [e_dom.tostring(e_dom.Element("command", attrib={'id': 'get_servtime_difference'}))]

    def get_dict_subscribe_ticks(self):
        """от create_command_for_tick_subscribe"""
        dict_subscribe = {}
        for symbol in self.symbols_list_for_tick:
            last_tick_df = self.get_last_tick_df.get_last_tick_from_postgres(symbol_code=symbol)
            if last_tick_df.empty:
                number_tick = 0
            else:
                number_tick = last_tick_df.iloc[-1].at['tradeno']
            dict_subscribe[symbol] = {'board': 'FUT', 'last_tick': str(number_tick)}
        print("Сервер: тики на подписку ", dict_subscribe)
        return dict_subscribe

    def get_dict_subscribe_quotes(self):
        """от create_command_for_quotes"""
        dict_subscribe = {}
        for key in self.symbols_list_for_quotes.keys():
            for symbol in self.symbols_list_for_quotes[key]:
                if key == 'fuchers':
                    dict_subscribe[symbol] = {'board': 'FUT'}
                elif key == 'stocks':
                    dict_subscribe[symbol] = {'board': 'TQBR'}
        return dict_subscribe

    def create_command_for_tick_subscribe(self):
        """от command_subscribe, {"SiM1": {"board": "FUT", "last_tick": 1121221545}} - формат принимаемых данных"""
        dict_request = self.get_dict_subscribe_ticks()
        main = e_dom.Element("command", attrib={'id': 'subscribe_ticks'})
        for symbol in dict_request.keys():
            elem_main = e_dom.SubElement(main, "security")
            e_dom.SubElement(elem_main, "board").text = f"{dict_request[symbol]['board']}"
            e_dom.SubElement(elem_main, "seccode").text = f"{symbol}"
            e_dom.SubElement(elem_main, "tradeno").text = f"{dict_request[symbol]['last_tick']}"
        e_dom.SubElement(main, "filter").text = f"false"
        return e_dom.tostring(main, encoding='utf-8')

    def create_command_for_quotes(self, unsubscribe=False):
        """от command_subscribe"""
        command_var = 'subscribe'
        if unsubscribe:
            command_var = 'unsubscribe'
        dict_glass_symbols = self.get_dict_subscribe_quotes()
        main_elem = e_dom.Element("command", attrib={'id': command_var})
        one_elem = e_dom.SubElement(main_elem, "quotes")
        for symbol in dict_glass_symbols.keys():
            sub_one_elem = e_dom.SubElement(one_elem, "security")
            e_dom.SubElement(sub_one_elem, "board").text = f"{dict_glass_symbols[symbol]['board']}"
            e_dom.SubElement(sub_one_elem, "seccode").text = f"{symbol}"
        return e_dom.tostring(main_elem, encoding='utf-8')

    def command_subscribe(self):
        ticks = self.create_command_for_tick_subscribe()
        quotes = self.create_command_for_quotes()
        return [ticks, quotes]

    def command_unsubscribe(self):
        ticks = e_dom.Element("command", attrib={"id": "subscribe_ticks"})
        ticks_command = e_dom.tostring(ticks, encoding='utf-8')
        quotes_command = self.create_command_for_quotes(unsubscribe=True)
        print("Сервер: ", quotes_command)
        return [ticks_command, quotes_command]


class ConnectController(ConnectorTX, QtCore.QThread):
    def __init__(self, main_self, raw_tick_queue, db_write_tick_queue, raw_quotes_queue):
        QtCore.QThread.__init__(self)
        ConnectorTX.__init__(self, main_self, raw_tick_queue, db_write_tick_queue, raw_quotes_queue)
        self.last_status = False
        self.connect_status = False
        self.status_subscribe = False

    @staticmethod
    def time_control():
        dtn = dt.datetime.now()
        if ((dtn >= dt.datetime(dtn.year, dtn.month, dtn.day, 6, 45, 0)) and
                (dtn <= dt.datetime(dtn.year, dtn.month, dtn.day, 23, 55, 0))):
            return True
        return False

    @staticmethod
    def internet_is_on():
        try:
            u_request.urlopen("http://ya.ru", timeout=5)
            return True
        except u_request.URLError:
            cf.send_message_bot("Нет подключения к интернету!")
            return False

    def reconnect(self):
        self.send_command(self.command_connect)
        print("Сервер: Зашел в реконнект ожидаю минуту")
        self.sleep(60)

    def start_connector(self):
        command = e_dom.tostring(e_dom.Element('init', attrib={
            'log_path': self.log_path,
            'log_level': str(self.log_lvl),
            'logfile_lifetime': str(self.logs_period_live)}))
        tr_lib.InitializeEx(command)
        self.raw_tick_queue.start()
        self.db_write_tick_queue.start()
        self.raw_quotes_queue.start()

    def stop_connector(self):
        print('***Начинаю остановку сервера***')
        self.running = False
        self.send_command(self.command_unsubscribe)
        time.sleep(1)
        self.send_command(self.command_disconnect)
        self.raw_tick_queue.close()
        self.db_write_tick_queue.close()
        self.raw_quotes_queue.close()
        time.sleep(1)
        tr_lib.UnInitialize()
        print('***Остановка сервера завершена***')

    def run(self):
        print("Сервер: Начинаю цикл сервера.")
        self.start_connector()
        while self.running:
            if not self.time_control():
                self.sleep(60)
                continue

            if not self.connect_status:
                print("Сервер: Точка: ", 1)
                self.status_subscribe = False
                if self.internet_is_on():
                    print("Сервер: Точка: ", 2)
                    self.reconnect()
                else:
                    self.sleep(5)

            elif self.connect_status:
                print("Сервер: Точка: ", 3)
                self.send_command(self.command_status_server)
                self.sleep(2)
                if self.last_status:
                    print("Сервер: Точка: ", 4)
                    if not self.status_subscribe:
                        print("Сервер: Точка: ", 5)
                        self.send_command(self.command_subscribe)
                        self.status_subscribe = True
                else:
                    print("Сервер: Точка: ", 6)
                    print("Сервер: last_status = False, пробую переподключиться.")
                    self.status_subscribe = False
                    self.reconnect()
            self.sleep(60)


if __name__ == '__main__':
    pass
