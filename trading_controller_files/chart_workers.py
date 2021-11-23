from PyQt5 import QtCore
from common_files.postgres import TickGetter


class ChartUpdateWorker(QtCore.QThread):
    """Поток обрабатывает на постоянной основе получение тиков из бд и построение графика"""
    def __init__(self, symbol, period):
        QtCore.QThread.__init__(self)
        self.running = True
        self.tick_getter = TickGetter(symbol, period)

    def run(self):
        while self.running:
            self.tick_getter.manager_getting_ticks_from_db()
            self.yieldCurrentThread()
