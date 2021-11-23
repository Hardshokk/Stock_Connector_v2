from PyQt5 import QtCore
from ts.general_ts_worker import GeneralTsWorker
from workers.symbols_dependent.antirollback_worker import AntiRollbackWorker
from workers.symbols_dependent.null_loss_worker import NullLossWorker
from workers.symbols_dependent.take_profit_worker import TakeProfitWorker
from workers.symbols_dependent.stop_loss_worker import StopLossWorker
from open_funcs.contra_cluster import ContraCluster


# Классы которые необходимо переопределить располагать в этом же файле. Они полностью относятся к этому обработчику


class TsCatchWorker(GeneralTsWorker):
    """Обработчик ТС TsCatch"""
    def __init__(self, main_self, symbol, signal_dict):
        GeneralTsWorker.__init__(self, main_self, symbol, signal_dict)
        # необходимые дополнительные функции обработчики
        self.anti_rollback_w = AntiRollbackWorker(self.main_self, self.symbol)
        self.null_loss_w = NullLossWorker(self.main_self, self.symbol)
        self.take_profit_w = TakeProfitWorker(self.main_self, self.symbol)
        self.stop_loss_w = StopLossWorker(self.main_self, self.symbol)
        # функция открытия позиции
        self.func_open = ContraCluster(self.main_self, self.symbol, self.signal_dict['tf_sec'])
        self.control_open = False

    def open_pos(self):
        """Основная функция открытия позиции"""
        # открываем позицию, и если открылись больше сюда не заходим
        if not self.control_open:
            self.func_open.open_pos_contra_cluster(self.signal_dict)
            if self.func_open.control_availability_orders_in_terminal():
                self.control_open = True
        # если открылись отложенным ордером включаем контроль жизни ордера равный 1 периоду
        if self.func_open.timer_del_order:
            self.func_open.del_order_on_timer()
        # контроль дополнительных функций
        if self.func_open.control_availability_orders_in_terminal(only_pos=True):
            self.anti_rollback_w.anti_rollback_func()
            self.null_loss_w.null_loss_func()
            self.take_profit_w.tp_func()
            self.stop_loss_w.sl_func()
        print("Прошел весь цикл обработчика захожу на повторный круг")

    def sub_run(self):
        self.open_pos()


if __name__ == '__main__':
    pass
