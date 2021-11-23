from PyQt5 import QtCore


class GeneralTsWorker(QtCore.QThread):
    def __init__(self, main_self, symbol, signal_dict):
        QtCore.QThread.__init__(self)
        self.running = True
        self.main_self = main_self
        self.symbol = symbol
        self.signal_dict = signal_dict
        self.ret_status = False

    def sub_run(self):
        """Переопределяется, получает все функции которые необходимо выполнять в потоке"""
        pass

    def printer(self, counter):
        print(f"Сюда прилетел сигнал {self.signal_dict} и он обрабатывается. {counter}")

    def run(self):
        counter = 1
        while self.running:
            self.sub_run()
            self.printer(counter)
            if not self.ret_status:
                self.ret_status = True
            self.sleep(1)
            counter += 1


if __name__ == '__main__':
    pass
