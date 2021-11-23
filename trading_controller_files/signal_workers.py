import os
from PyQt5 import QtCore
import common_files.common_functions as cf
from common_files.trading_script import PositionsOrdersManager
import datetime as dt
from server.queue_workers import WorkerQueueSignal


class DealSignalWorker(QtCore.QThread):
    """Главный принимающий обработчик сигналов от ТС"""
    def __init__(self, main_self):
        QtCore.QThread.__init__(self)
        self.main_self = main_self
        self.running = True
        self.file_symbol_manager = "trading_controller_files\\symbol_manager.obj"
        self.symbols_manager = {}
        self.symbols_link = {}
        self.ts = PositionsOrdersManager(self.main_self.terminal)
        self.block = False
        self.start_sync(start=True)
        self.queue = WorkerQueueSignal({'deal': self.main_worker_signal, 'alert': self.alert_worker_signal})
        self.queue.start()

    def check_availability_symbol_in_terminal(self, symbol):
        """Отдает ответ есть ли ордер или позиция по указанному символу в терминале"""
        pos_df, order_df = self.ts.get_positions_and_orders(symbol=symbol)
        if pos_df.empty and order_df.empty:
            return False
        return True

    def drop_symbol_manager_file(self):
        os.remove(self.file_symbol_manager)
        print("symbol_manager удален, из-за ошибки загрузки файла")

    def load_symbol_manager(self):
        try:
            self.symbols_manager = cf.load_object(self.file_symbol_manager)
        except EOFError:
            self.drop_symbol_manager_file()

    def start_sync(self, start=False):
        """Синхронизация при менеджера символов"""
        if os.path.isfile(self.file_symbol_manager):
            pos_df, order_df = self.ts.get_positions_and_orders()
            if not pos_df.empty:
                if start:
                    self.load_symbol_manager()
                # блокировка на момент запуска обработчика
                while self.block:
                    self.msleep(5)
                symbols_set_terminal = set(cf.get_symbol_format_mcode(x) for x in pos_df['symbol'].to_list())
                symbols_set_manager = set(self.symbols_manager.keys())
                symbols_set_links = set(self.symbols_link.keys())
                print("symbol_manager: ", symbols_set_manager, symbols_set_terminal)
                drop_symbols_from_manager = symbols_set_manager.difference(symbols_set_terminal)
                drop_symbols_from_links = symbols_set_links.difference(symbols_set_terminal)
                print("symbol_links: ", symbols_set_manager, symbols_set_terminal)
                for symbol_del in drop_symbols_from_manager:
                    del self.symbols_manager[symbol_del]
                for symbol_del in drop_symbols_from_links:
                    self.symbols_link[symbol_del]['worker'].running = False
                    self.symbols_link[symbol_del]['worker'].terminate()
                    del self.symbols_link[symbol_del]
                self.save_again_symbols_manager()
                print(f"Удалил из менеджера символов набор {drop_symbols_from_manager}")
                print(f"Удалил из менеджера ссылок {drop_symbols_from_links}")
            elif pos_df.empty:
                self.symbols_manager.clear()
                self.symbols_link.clear()
                self.drop_symbol_manager_file()

                print("Открытых позиций нет. Символ менеджер пуст.")

    def symbol_link_add_signal(self, symbol, ts_name, dict_from_signal):
        """Добавляет сохраняет ссылки на потоки обработчиков в словарь"""
        self.symbols_link[symbol] = {"ts_thread": self.main_self.ts_dict[ts_name]['signal_finder'],
                                     "worker": self.main_self.ts_dict[ts_name]['worker'](self.main_self,
                                                                                         symbol, dict_from_signal)}
        self.block = True
        self.symbols_link[symbol]['worker'].start()
        while not self.symbols_link[symbol]['worker'].ret_status:
            print("Ожидаю полного запуска обработчика.", dt.datetime.now())
            self.msleep(5)
        self.block = False

    def start_threads_workers(self):
        """После запуска программы и синхронизации запускает потоки обрботчиков"""
        for symbol in self.symbols_manager.keys():
            ts_name = self.symbols_manager[symbol]['ts_name']
            dict_from_signal = self.symbols_manager[symbol]['dict_from_signal']
            self.symbol_link_add_signal(symbol, ts_name, dict_from_signal)

    def save_again_symbols_manager(self):
        cf.save_object(self.symbols_manager, self.file_symbol_manager)

    def append_signal_in_queue(self, *signal_dict):
        """функция принимает сигнал и добавляет его в очередь обработки сигналов"""
        dict_from_signal = signal_dict[1]
        self.queue.send_in_queue(dict_from_signal)
        self.queue.get_len_queue()

    def alert_worker_signal(self, signal_dict):
        msg = f"Сигнал {signal_dict['symbol']}, {signal_dict['ts_name']}, {signal_dict['my_msg']}, " \
              f"передал управление обработчику ТС - " \
              f"{dt.datetime.now()}"
        print(msg)
        self.main_self.alert_one_symbol(msg, signal_dict['symbol'])
        self.main_self.print_message_in_log_edit(msg)

    def main_worker_signal(self, signal_dict):
        """Принимает сигналы от ТС. Основной обработчик сигналов"""
        print(signal_dict)
        symbol = signal_dict['symbol']
        ts_name = signal_dict['ts_name']
        if not self.check_availability_symbol_in_terminal(symbol) and not self.symbols_link.get(symbol):
            self.symbols_manager[symbol] = signal_dict
            self.symbol_link_add_signal(symbol, ts_name, signal_dict)
            self.save_again_symbols_manager()
            self.alert_worker_signal(signal_dict)

    def run(self):
        while self.running:
            self.start_sync()
            self.sleep(1)
        self.queue.close()
