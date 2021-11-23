import json
import os
import traceback
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
from trading_controller_files.trading_controller_form import Ui_MainWindow
# from trading_controller.functions import update_alert_file, show_alerts, get_deal
from common_files import common_functions as cf
from open_funcs.light_open import LightOpen


class TradingControllerGeneral(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        """активация и группировка"""
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        """настройка интерфейса"""
        self.setCentralWidget(self.main_tab)

        # обработка главного меню
        self.main_menu = self.menuBar()
        self.menu_file = self.main_menu.addMenu("Файл")
        self.menu_file.addAction("Новый")
        self.menu_window = self.main_menu.addMenu("Окно")

        # обработка главной панели
        self.toolbar_main = QtWidgets.QToolBar()
        self.toolbar_main.setAllowedAreas(QtCore.Qt.TopToolBarArea)
        self.toolbar_main.addAction("Добавить чарт")
        self.toolbar_main.addSeparator()
        self.toolbar_main.addAction("Обновить чарт")
        self.addToolBar(self.toolbar_main)

        # Основная обработка выравнивания

        # выравнивание во втором главном контейнере
        self.grid_main_tab_2 = QtWidgets.QGridLayout()
        self.grid_main_tab_2.setColumnMinimumWidth(0, 250)
        self.grid_main_tab_2.setColumnMinimumWidth(1, 600)
        policy_size = QtWidgets.QSizePolicy()
        policy_size.setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        policy_size.setVerticalPolicy(QtWidgets.QSizePolicy.Expanding)

        policy_size.setHorizontalStretch(2)
        policy_size.setVerticalStretch(2)
        self.sub_tab_central.setSizePolicy(policy_size)
        self.grid_main_tab_2.addWidget(self.sub_tab_central, 0, 1)

        self.sub_tab_right = QtWidgets.QTabWidget()
        self.sub_tab_right_tab_1 = QtWidgets.QWidget()
        self.sub_tab_right.setTabPosition(2)
        self.sub_tab_right.addTab(self.sub_tab_right_tab_1, "торговая панель")
        policy_size.setHorizontalStretch(0)
        policy_size.setVerticalStretch(0)
        self.sub_tab_right.setSizePolicy(policy_size)
        self.grid_main_tab_2.addWidget(self.sub_tab_right, 0, 0)
        self.main_tab_2.setLayout(self.grid_main_tab_2)

        # выравнивание в подконтейнерах
        # контейнер 3
        self.grid_sub_tab_central_tab_3 = QtWidgets.QGridLayout()
        self.sub_tab_central_tab_3.setLayout(self.grid_sub_tab_central_tab_3)

        self.sub_tab_central_tab_3_toolbar = QtWidgets.QToolBar()
        self.sub_tab_central_tab_3_toolbar.setMaximumHeight(30)
        policy_size.setHorizontalStretch(2)
        policy_size.setVerticalStretch(0)
        self.sub_tab_central_tab_3_toolbar.setSizePolicy(policy_size)
        self.grid_sub_tab_central_tab_3.addWidget(self.sub_tab_central_tab_3_toolbar, 0, 0)
        self.sub_tab_central_tab_3_toolbar.addAction('si', partial(self.create_chart, "SiU1", 60))
        self.sub_tab_central_tab_3_toolbar.addAction('sber', partial(self.create_chart, "SRU1", 60))
        self.sub_tab_central_tab_3_toolbar.addAction('gazr', partial(self.create_chart, "GZU1", 60))
        self.sub_tab_central_tab_3_toolbar.addSeparator()
        self.sub_tab_central_tab_3_toolbar.addAction('Компактно', self.charts_mdi_area.tileSubWindows)

        # Обработка области графиков
        policy_size.setHorizontalStretch(2)
        policy_size.setVerticalStretch(2)
        self.sub_tab_central_tab_3_toolbar.setSizePolicy(policy_size)
        self.grid_sub_tab_central_tab_3.addWidget(self.charts_mdi_area, 1, 0)
        self.charts_mdi_area.setSizePolicy(policy_size)
        self.charts_mdi_area_vertical_scroll = QtWidgets.QScrollBar(QtCore.Qt.Vertical)
        self.charts_mdi_area_horizontal_scroll = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.charts_mdi_area.setVerticalScrollBar(self.charts_mdi_area_vertical_scroll)
        self.charts_mdi_area.setHorizontalScrollBar(self.charts_mdi_area_horizontal_scroll)
        self.charts_mdi_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.charts_mdi_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        # Перенос привода торговли
        # заголовок
        self.use_deal_privod_hor_layout_one = QtWidgets.QHBoxLayout()
        self.use_deal_privod_label_select_symbol_2 = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setPointSize(12)
        self.use_deal_privod_label_select_symbol_2.setFont(font)
        self.use_deal_privod_label_select_symbol_2.setAlignment(QtCore.Qt.AlignCenter)
        self.use_deal_privod_label_select_symbol_2.setObjectName("use_deal_privod_label_select_symbol_2")
        self.use_deal_privod_label_select_symbol_2.setText("Торговый привод")
        self.use_deal_privod_hor_layout_one.addWidget(self.use_deal_privod_label_select_symbol_2)
        self.sub_tab_right_tab_1.setLayout(self.use_deal_privod_hor_layout_one)

        self.use_deal_privod_hor_layout_two = QtWidgets.QHBoxLayout()
        self.use_deal_privod_main_checkbox = QtWidgets.QCheckBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_main_checkbox.setChecked(False)
        self.use_deal_privod_main_checkbox.setObjectName("use_deal_privod_main_checkbox")
        self.sub_tab_right_tab_1.setLayout(self.use_deal_privod_hor_layout_two)

        self.use_deal_privod_liquidation_checkbox = QtWidgets.QCheckBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_liquidation_checkbox.setGeometry(QtCore.QRect(720, 240, 181, 17))
        self.use_deal_privod_liquidation_checkbox.setChecked(True)
        self.use_deal_privod_liquidation_checkbox.setObjectName("use_deal_privod_liquidation_checkbox")
        self.use_deal_privod_button_close_pos = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_close_pos.setGeometry(QtCore.QRect(720, 190, 91, 23))
        self.use_deal_privod_button_close_pos.setObjectName("use_deal_privod_button_close_pos")
        self.use_deal_privod_button_market_buy = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_market_buy.setGeometry(QtCore.QRect(720, 160, 91, 23))
        self.use_deal_privod_button_market_buy.setObjectName("use_deal_privod_button_market_buy")

        self.use_deal_privod_contra_cluster_label_offset = QtWidgets.QLabel(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_label_offset.setGeometry(QtCore.QRect(720, 290, 41, 16))
        self.use_deal_privod_contra_cluster_label_offset.setObjectName("use_deal_privod_contra_cluster_label_offset")
        self.use_deal_privod_label_volume = QtWidgets.QLabel(self.sub_tab_right_tab_1)
        self.use_deal_privod_label_volume.setGeometry(QtCore.QRect(720, 100, 131, 16))
        self.use_deal_privod_label_volume.setObjectName("use_deal_privod_label_volume")
        self.use_deal_privod_spin_volume = QtWidgets.QDoubleSpinBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_spin_volume.setGeometry(QtCore.QRect(850, 100, 62, 22))
        self.use_deal_privod_spin_volume.setDecimals(0)
        self.use_deal_privod_spin_volume.setMaximum(1000.0)
        self.use_deal_privod_spin_volume.setProperty("value", 2.0)
        self.use_deal_privod_spin_volume.setObjectName("use_deal_privod_spin_volume")
        self.use_deal_privod_combo_select_symbol = QtWidgets.QComboBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_combo_select_symbol.setGeometry(QtCore.QRect(790, 70, 121, 22))
        self.use_deal_privod_combo_select_symbol.setObjectName("use_deal_privod_combo_select_symbol")
        self.use_deal_privod_button_market_buy_lim = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_market_buy_lim.setGeometry(QtCore.QRect(720, 130, 91, 23))
        self.use_deal_privod_button_market_buy_lim.setObjectName("use_deal_privod_button_market_buy_lim")
        self.use_deal_privod_contra_cluster_label_sl = QtWidgets.QLabel(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_label_sl.setGeometry(QtCore.QRect(830, 290, 21, 16))
        self.use_deal_privod_contra_cluster_label_sl.setObjectName("use_deal_privod_contra_cluster_label_sl")
        self.use_deal_privod_button_delete_order = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_delete_order.setGeometry(QtCore.QRect(820, 190, 91, 23))
        self.use_deal_privod_button_delete_order.setObjectName("use_deal_privod_button_delete_order")
        self.use_deal_privod_contra_cluster_spin_offset = QtWidgets.QDoubleSpinBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_spin_offset.setGeometry(QtCore.QRect(760, 290, 62, 22))
        self.use_deal_privod_contra_cluster_spin_offset.setDecimals(0)
        self.use_deal_privod_contra_cluster_spin_offset.setMaximum(1000.0)
        self.use_deal_privod_contra_cluster_spin_offset.setProperty("value", 2.0)
        self.use_deal_privod_contra_cluster_spin_offset.setObjectName("use_deal_privod_contra_cluster_spin_offset")
        self.use_deal_privod_button_market_sell = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_market_sell.setGeometry(QtCore.QRect(820, 160, 91, 23))
        self.use_deal_privod_button_market_sell.setObjectName("use_deal_privod_button_market_sell")
        self.use_deal_privod_contra_cluster_checkbox_main = QtWidgets.QCheckBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_checkbox_main.setGeometry(QtCore.QRect(720, 270, 201, 17))
        self.use_deal_privod_contra_cluster_checkbox_main.setChecked(False)
        self.use_deal_privod_contra_cluster_checkbox_main.setObjectName("use_deal_privod_contra_cluster_checkbox_main")
        self.use_deal_privod_button_market_sell_lim = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_market_sell_lim.setGeometry(QtCore.QRect(820, 130, 91, 23))
        self.use_deal_privod_button_market_sell_lim.setObjectName("use_deal_privod_button_market_sell_lim")
        self.use_deal_privod_contra_cluster_label_tp = QtWidgets.QLabel(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_label_tp.setGeometry(QtCore.QRect(830, 320, 21, 16))
        self.use_deal_privod_contra_cluster_label_tp.setObjectName("use_deal_privod_contra_cluster_label_tp")
        self.use_deal_privod_checkbox_stop_reverse = QtWidgets.QCheckBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_checkbox_stop_reverse.setGeometry(QtCore.QRect(720, 220, 171, 17))
        self.use_deal_privod_checkbox_stop_reverse.setChecked(False)
        self.use_deal_privod_checkbox_stop_reverse.setObjectName("use_deal_privod_checkbox_stop_reverse")
        self.use_deal_privod_contra_cluster_spin_stop = QtWidgets.QDoubleSpinBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_spin_stop.setGeometry(QtCore.QRect(850, 290, 62, 22))
        self.use_deal_privod_contra_cluster_spin_stop.setDecimals(0)
        self.use_deal_privod_contra_cluster_spin_stop.setMaximum(1000.0)
        self.use_deal_privod_contra_cluster_spin_stop.setProperty("value", 25.0)
        self.use_deal_privod_contra_cluster_spin_stop.setObjectName("use_deal_privod_contra_cluster_spin_stop")
        self.use_deal_privod_contra_cluster_spin_tp = QtWidgets.QDoubleSpinBox(self.sub_tab_right_tab_1)
        self.use_deal_privod_contra_cluster_spin_tp.setGeometry(QtCore.QRect(850, 320, 62, 22))
        self.use_deal_privod_contra_cluster_spin_tp.setDecimals(0)
        self.use_deal_privod_contra_cluster_spin_tp.setMaximum(1000.0)
        self.use_deal_privod_contra_cluster_spin_tp.setProperty("value", 50.0)
        self.use_deal_privod_contra_cluster_spin_tp.setObjectName("use_deal_privod_contra_cluster_spin_tp")
        self.use_deal_privod_label_select_symbol = QtWidgets.QLabel(self.sub_tab_right_tab_1)
        self.use_deal_privod_label_select_symbol.setGeometry(QtCore.QRect(720, 70, 51, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.use_deal_privod_label_select_symbol.setFont(font)
        self.use_deal_privod_label_select_symbol.setObjectName("use_deal_privod_label_select_symbol")
        self.use_deal_privod_button_open_pos_ts_contra_cluster = QtWidgets.QPushButton(self.sub_tab_right_tab_1)
        self.use_deal_privod_button_open_pos_ts_contra_cluster.setGeometry(QtCore.QRect(720, 320, 101, 21))
        self.use_deal_privod_button_open_pos_ts_contra_cluster.setObjectName(
            "use_deal_privod_button_open_pos_ts_contra_cluster")

        # Другое
        self.button_group_besubitok = QtWidgets.QButtonGroup()
        self.button_group_besubitok.addButton(self.use_besubitok_radio_fix)
        self.button_group_besubitok.addButton(self.use_besubitok_radio_auto)
        self.use_besubitok_radio_auto.setChecked(True)

        self.button_group_sl = QtWidgets.QButtonGroup()
        self.button_group_sl.addButton(self.use_sl_radio_standart)
        self.button_group_sl.addButton(self.use_sl_radio_extra)
        self.use_sl_radio_extra.setChecked(True)

        self.button_group_price_alert = QtWidgets.QButtonGroup()
        self.button_group_price_alert.addButton(self.use_pricealert_radio_high)
        self.button_group_price_alert.addButton(self.use_pricealert_radio_low)
        self.button_group_price_alert.addButton(self.use_pricealert_radio_channel)

        """настройки"""
        self.settings = {}
        self.name_settings_file = "settings_file.json"
        self.get_settings()
        self.terminal = 1
        self.symbols_fuchers_list = [symbol['long_code'] for symbol in cf.symbols_collect['fuchers'][: 3]]
        self.stop_reverse_dict = {}
        self.alert_file_name = "alert_file.json"

        self.use_pricealert_combo_select_symbol.addItems(self.symbols_fuchers_list)
        self.use_pricealert_combo_select_symbol.setCurrentIndex(3)

        self.button_set_path_terminal.clicked.connect(self.get_path_from_terminal)

        # self.use_pricealert_button_add.clicked.connect(partial(update_alert_file, self, add_alert=True))
        # self.use_pricealert_button_delete.clicked.connect(partial(update_alert_file, self, delete_alert=True))
        # self.use_pricealert_button_clear.clicked.connect(partial(update_alert_file, self, clear_alerts=True))
        # self.use_pricealert_button_active_alerts.clicked.connect(partial(show_alerts, self))

        self.button_clear_log_edit.clicked.connect(self.log_edit.clear)

        """Блок ручного привода торговли"""
        self.light_deals = LightOpen(self)
        self.use_deal_privod_combo_select_symbol.addItems([symbol['long_code'] for symbol in
                                                           cf.symbols_collect['fuchers'][: 3]])
        self.use_deal_privod_combo_select_symbol.setCurrentIndex(0)
        self.use_deal_privod_button_market_buy_lim.clicked.connect(partial(self.light_deals.get_deal, 'buy_market_lim'))
        self.use_deal_privod_button_market_sell_lim.clicked.connect(partial(self.light_deals.get_deal, 'sell_market_lim'))
        self.use_deal_privod_button_market_buy.clicked.connect(partial(self.light_deals.get_deal, 'buy_market'))
        self.use_deal_privod_button_market_sell.clicked.connect(partial(self.light_deals.get_deal, 'sell_market'))
        self.use_deal_privod_button_close_pos.clicked.connect(partial(self.light_deals.get_deal, 'close_position'))
        self.use_deal_privod_button_delete_order.clicked.connect(partial(self.light_deals.get_deal, 'delete_order'))
        # self.use_deal_privod_button_open_pos_ts_contra_cluster.clicked.connect(
        #     partial(get_deal, self, 'open_pos_contra_cluster'))

    def get_path_from_terminal(self, show_widow_info=False, update_path=True):
        """Запрос на путь до терминала"""
        if show_widow_info:
            QtWidgets.QMessageBox.information(self, "Информация", "Выберите исполняемый файл терминала или ярлык, "
                                                                  "с которым будет работать программа.")
        directory = QtWidgets.QFileDialog.getOpenFileUrl()[0].path()[1:].replace("/", "\\\\")
        if directory != "":
            self.settings['path_to_terminal'] = directory
        if update_path:
            self.update_settings({'path_to_terminal': directory})
            self.print_message_in_log_edit(message=f"Установлен путь к терминалу: "
                                                   f"{self.settings['path_to_terminal']}")
        return directory

    def get_settings(self):
        while not self.settings:
            settings = self.load_json()
            if settings.get("path_to_terminal") and os.path.isfile(settings['path_to_terminal']):
                self.settings = settings
                self.print_message_in_log_edit(message=f"Установлен путь к терминалу: "
                                                       f"{self.settings['path_to_terminal']}")
                break
            self.create_settings()

    def load_json(self):
        if os.path.isfile(self.name_settings_file):
            with open(self.name_settings_file, "r") as f:
                read_data = f.read()
                if read_data:
                    loaded_data = json.loads(read_data)
                    return loaded_data
        return {}

    @staticmethod
    def save_json(full_file_name, what_dump):
        with open(full_file_name, "w") as f:
            f.writelines(json.dumps(what_dump))

    def create_settings(self):
        params = {
            "path_to_terminal": self.get_path_from_terminal(show_widow_info=True, update_path=False),
        }
        self.save_json(self.name_settings_file, params)

    def update_settings(self, update_dict):
        settings = self.load_json()
        if settings:
            for i in update_dict:
                settings[i] = update_dict[i]
        self.save_json(self.name_settings_file, settings)

    def print_message_in_log_edit(self, message=""):
        self.log_edit.append(f"{message}")

    @staticmethod
    def save_last_except():
        with open("logs\\trading_controller_log.txt", "a+") as f:
            traceback.print_exc(file=f)

    @staticmethod
    def save_info_in_log(name_log_only, data):
        with open(f"logs\\{name_log_only}.txt", "a+", encoding='utf-8') as f:
            f.write(f"{data}\n")

    def alert_one_symbol(self, message, symbol, print_message=True, send_on_phone=True, play_on_pc=True,
                         what_play_list_tuples=()):
        if print_message:
            self.log_edit.append(message)
        if send_on_phone:
            cf.send_message_bot(message)
        if play_on_pc:
            pass
            # if not what_play_list_tuples:
            #     self.log_edit.append("Воспроизвожу файл по умолчанию. Передайте кортеж ((file_name, duration), )")
            #     alert_list_tuples = (("hit_in_lvl.mp3", 3), (f"{symbol.split('-')[0].split()[0]}.mp3", 3))
            #     for alert in alert_list_tuples:
            #         cf.play_alert(file_name=alert[0], duration_secs=alert[1])
            # else:
            #     for alert in what_play_list_tuples:
            #         cf.play_alert(file_name=alert[0], duration_secs=alert[1])
