import pymongo
import datetime as dt
import time


class ConnectorMongo:
    def __init__(self):
        self.host = 'localhost'
        self.port = 27017
        self.db_name = 'charts_db'
        self.client = pymongo.MongoClient(self.host, self.port)
        self.db = self.client[self.db_name]
        self.collections_list = self.db.list_collection_names()

    def add_index_field(self, symbol, tf_sec, field_name):
        self.db[symbol][tf_sec].create_index([(field_name, pymongo.ASCENDING)], unique=True)

    def add_one_bar_in_collection(self, symbol, tf_sec, what_add):
        if not ("time_open_1" in set(self.db[symbol][tf_sec].index_information().keys())):
            self.add_index_field(symbol, tf_sec, "time_open")
        try:
            self.db[symbol][tf_sec].insert_one(what_add)
        except pymongo.errors.DuplicateKeyError:
            print("Ошибка добавления, этот бар уже существует")

    def add_many_bars_in_collection(self, symbol, tf_sec, list_what_add):
        if not ("time_open_1" in set(self.db[symbol][tf_sec].index_information().keys())):
            self.add_index_field(symbol, tf_sec, "time_open")
        try:
            self.db[symbol][tf_sec].insert_many(list_what_add)
        except pymongo.errors.DuplicateKeyError:
            print("Ошибка добавления, этот бар уже существует")

    def get_last_bar(self, symbol, tf_sec):
        if self.get_len_collection(symbol, tf_sec) > 0:
            return self.db[symbol][tf_sec].find().sort("_id", -1).limit(1)[0]
        return {}

    def get_len_collection(self, symbol, tf_sec):
        return self.db[symbol][tf_sec].count_documents({})

    def get_qv_last_bars(self, symbol, tf_sec, qv_bars):
        last_bar = self.get_last_bar(symbol, tf_sec)
        time_finish = last_bar.get('time_open')
        if not time_finish:
            print("Баров по данному инструменту нет.")
            return []
        response = []
        x = 1
        while len(response) < qv_bars:
            time_start = time_finish - dt.timedelta(seconds=tf_sec * qv_bars * x)
            response = list(self.get_range_bars_time(symbol, tf_sec, time_start, time_finish))
            x += 1
        if len(response) > qv_bars:
            response = response[-qv_bars:]
        return response

    def get_range_bars_time(self, symbol, tf_sec, time_start, time_finish):
        return list(self.db[symbol][tf_sec].find({"$and": [{"time_open": {'$gte': time_start}},
                                                      {"time_open": {'$lte': time_finish}}]}))

    def drop_collection(self, symbol, tf):
        self.db[symbol][tf].drop()

    @staticmethod
    def get_real_price(price):
        return float(price.replace('_', '.'))

    @staticmethod
    def get_price_mongo_name_format(price):
        return f"{price}".replace('.', '_')
