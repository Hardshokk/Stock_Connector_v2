from ts.general_ts_worker import GeneralTsWorker


class TsPriceActionWorker(GeneralTsWorker):
    def __init__(self, main_self, symbol, signal_dict):
        GeneralTsWorker.__init__(self, main_self, symbol, signal_dict)

    def sub_run(self):
        print("Прошел sub_run, отключаю свой поток обработчик")
        self.running = False
        self.sleep(1)
