# encoding: utf-8

from vnpy.trader.vtObject import VtBaseData
from vnpy.trader.language.chinese.constant import *

# UI event type
EVENT_OPTION_TICK = "eOptionTick"
EVENT_STRATEGY_STOP_ORDER_STATUS = "eStrategyStopOrderStatus"
EVENT_STRATEGY_CATCH_LIMITUP_STATUS= "eStrategyCatchLimitUpStatus"

class VtStrategyCatchLimitUpInfo(VtBaseData):
    def __init__(self):
        super(VtStrategyCatchLimitUpInfo, self).__init__()

        self.plateName = None
        self.numOfStocks = 0
        self.catchedStocks = 0
        self.missedStocks = 0

class VtStrategyStopOrderStatus(VtBaseData):
    def __init__(self):
        super(VtStrategyStopOrderStatus, self).__init__()

        self.strategyID = EMPTY_STRING
        self.status = EMPTY_STRING
        self.thresholdInfo = EMPTY_STRING
        self.ownerPrice = EMPTY_STRING
        self.ownerMaxMinPrice = EMPTY_STRING
        self.drawbackPrice = EMPTY_STRING
        self.crossDirection = EMPTY_STRING
        self.tradeDirection = EMPTY_STRING
        self.volume = EMPTY_STRING
        self.orderVolume = EMPTY_STRING

class VtOptionTickData(VtBaseData):
    def __init__(self):
        super(VtOptionTickData, self).__init__()

        self.optionCode = EMPTY_STRING
        self.ownerCode = EMPTY_STRING
        self.strikePrice = EMPTY_STRING
        self.strikeDate = EMPTY_STRING
        self.latestPrice = EMPTY_STRING
        self.impliedVolatility = EMPTY_STRING
        self.ownerPrice = EMPTY_STRING
        self.calculatedPrice = EMPTY_STRING
        self.bid1 = EMPTY_STRING
        self.ask1 = EMPTY_STRING
        self.type = EMPTY_STRING
        self.position = EMPTY_STRING
        self.costPrice = EMPTY_STRING

class VtOptionSelectorData(VtBaseData):
    def __init__(self):
        self.code = EMPTY_STRING
        self.last_price = EMPTY_STRING
        self.option_type = EMPTY_STRING
        self.strike_time = EMPTY_STRING
        self.option_strike_price = EMPTY_STRING
        self.option_open_interest = EMPTY_STRING
        self.volume = EMPTY_STRING
        self.option_delta = EMPTY_STRING
        self.option_gamma = EMPTY_STRING
        self.option_vega = EMPTY_STRING