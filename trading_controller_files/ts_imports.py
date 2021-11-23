"""Лист регистрации стратегий. Каждой ТС подключается поток поисковика сигналов и поток обработчика"""
from ts.ts_catch.ts_threads import TsCatchTread
from ts.ts_catch.ts_worker import TsCatchWorker

from ts.ts_absorbing_bar.ts_threads import TsAbsorbingBarThread
from ts.ts_absorbing_bar.ts_worker import TsAbsorbingBarWorker

from ts.ts_roof_line.ts_threads import TsRoofLineThread
from ts.ts_roof_line.ts_worker import TsRoofLineWorker

from ts.ts_price_action.ts_threads import TsPriceActionThread
from ts.ts_price_action.ts_worker import TsPriceActionWorker

from ts.ts_day_points.ts_threads import TsDayPointsThread
from ts.ts_day_points.ts_worker import TsDayPointsWorker

from ts.ts_zones_finder.ts_threads import TsZonesFinderThread
from ts.ts_zones_finder.ts_worker import TsZonesFinderWorker

