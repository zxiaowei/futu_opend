
from vnpy.trader.app import AppEngine
import json
from vnpy.trader.vtObject import VtLogData, VtSubscribeReq
from vnpy.event.eventEngine import Event
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_TICK, EVENT_ORDER, EVENT_TRADE
from vnpy.trader.vtFunction import getJsonPath

class StrategyEngine(AppEngine):
    def __init__(self, mainEngine, eventEngine):
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        self.configFileName = 'stock_relationship.json'
        self.configFile = getJsonPath(self.configFileName, __file__)
        self.stockOwnership = {}


    def start(self):
        # load pre-defined stock ownership
        try:
            f = open(self.configFile,encoding = 'utf-8')
            self.stockOwnership = json.load(f)
            f.close()
        except:
            self.writeLog(u'载入' + self.configFile + u'文件出错')
            return

        self.registerEvent()


    def stop(self):
        pass

    def writeLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        log.gatewayName = 'SLIPPERY_GRID_ENGINE'
        event = Event(type_=EVENT_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)

    def registerEvent(self):
        self.eventEngine.register(EVENT_TICK, self.processTick)
        self.eventEngine.register(EVENT_ORDER, self.processOrder)
        self.eventEngine.register(EVENT_TRADE, self.processDeal)

    def processTick(self, tickData):
        print(tickData)

    def processOrder(self, orderData):
        print(orderData)

    def processDeal(self, dealData):
        print(dealData)

    def subscribe(self, stockCodeList):

        for stockCode in stockCodeList:
            req = VtSubscribeReq()
            req.symbol = stockCode
            self.mainEngine.subscribe(req, 'FUTU')