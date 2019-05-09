# encoding: utf-8

import traceback
from vnpy.trader.app import AppEngine
import json
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_TICK, EVENT_ORDER, EVENT_TRADE
from vnpy.trader.vtObject import VtLogData, VtSubscribeReq, VtOrderReq, VtCancelOrderReq,VtHistoryTradeReq
from vnpy.event.eventEngine import Event
from pandas import DataFrame
import pandas as pd
from datetime import datetime, timedelta
from app.catchLimitUp.strategyLimitUp import CatchLimitUpStrategy
from qssBasic import  EVENT_STRATEGY_CATCH_LIMITUP_STATUS, VtStrategyCatchLimitUpInfo
from vnpy.trader.language.chinese.constant import *


# CTA引擎中涉及到的交易方向类型
CTAORDER_BUY = u'买开'
CTAORDER_SELL = u'卖平'

class CatchLimitUpEngine(AppEngine):

    def __init__(self, mainEngine, eventEngine):
        try:
            self.mainEngine = mainEngine
            self.eventEngine = eventEngine

            self.configFileName = 'catch_limit_up.json'
            self.configFile = getJsonPath(self.configFileName, __file__)

            self.strategyDict = {}
            self.symbolStrategyDict = {}

        except:
            traceback.print_exc()


    def start(self):
        # load pre-defined stock ownership
        try:
            f = open(self.configFile,encoding = 'utf-8')
            self.config = json.load(f)
            f.close()
        except:
            self.writeLog(u'载入' +  self.configFile + u'文件出错')
            return


        self.registerEvent()


    def stop(self):
        pass

    def registerEvent(self):
        try:
            if self.eventEngine:
                self.eventEngine.register(EVENT_TICK, self.processTick)
                self.eventEngine.register(EVENT_ORDER, self.processOrder)
                self.eventEngine.register(EVENT_TRADE, self.processDeal)
        except:
            traceback.print_exc()

    def processTick(self, event):
        try:
            tick = event.dict_['data']
            symbol = tick.symbol

            # 过滤掉不关注的tick信息
            if symbol not in self.symbolStrategyDict:
                return

            for stra in self.symbolStrategyDict[symbol]:
                stra.onTick(tick)
                self.updateUI(stra)


        except:
            traceback.print_exc()


    # 模拟题环境不支持成交推送，只支持订单推送。 所以用订单推送来判断交易是否成功
    def processOrder(self, event):
        try:
            pass

        except:
            traceback.print_exc()

    def processDeal(self, event):
        try:
            pass
        except:
            traceback.print_exc()



    def subscribeForStrategy(self, stra):
        try:
            stockCodeList = stra.getSubscribeList()
            req = VtSubscribeReq()
            req.symbol = stockCodeList
            self.mainEngine.subscribe(req, 'FUTU')

        except:
            traceback.print_exc()

    def addStrategy(self, straConfig):
        try:
            # 生成策略实例
            stra = CatchLimitUpStrategy(self, straConfig)

            # 根据策略ID检查是否有重复的策略
            straID = stra.strategyID
            if straID not in self.strategyDict:
                self.strategyDict[straID] = stra
            else:
                return -1, u"策略[" + straID + u"]已经存在，不能重复启动"

            # 启动策略
            stra.start()

            # 建立stockCode与策略的对应关系， 一个stockCode可以对应多个策略，一个策略也可以关注多个stockCdoe
            symbolList = stra.getSymbolList()
            for symbol in symbolList:
                if symbol in self.symbolStrategyDict:
                    straList = self.symbolStrategyDict[symbol]
                else:
                    straList = []
                    self.symbolStrategyDict[symbol] = straList
                straList.append(stra)

            # 订阅行情
            self.subscribeForStrategy(stra)

            # 第一次添加策略，通知UI更新
            self.updateUI(stra)

            self.writeLog(u"成功添加策略[" + stra.strategyID + u"]")

            return 0, ""
        except:
            traceback.print_exc()

    def cancelStrategy(self, strategyID):
        pass


    def queryTodayTradeSync(self):
        try:
            gatewayName = "TradeDllAShare"
            tradeDf = self.mainEngine.qryTradeSync(gatewayName)
            return tradeDf
        except:
            traceback.print_exc()
            tradeDf = pd.DataFrame()
            return tradeDf

    def queryPositionSync(self):
        try:
            gatewayName = "TradeDllAShare"
            positionDf = self.mainEngine.qryPositionSync(gatewayName)
            return positionDf
        except:
            traceback.print_exc()
            positionDf = pd.DataFrame()
            return positionDf

    def queryAccountSync(self):
        try:
            gatewayName = "TradeDllAShare"
            accountDf = self.mainEngine.qryAccountSync(gatewayName)
            return accountDf
        except:
            traceback.print_exc()
            accountDf = pd.DataFrame()
            return accountDf

    def queryHistoryTradeSync(self, startDate,endDate):
        try:
            req = VtHistoryTradeReq()
            req.startDate = startDate
            req.endDate = endDate

            gatewayName = "TradeDllAShare"
            tradeDf = self.mainEngine.qryHistoryTradeSync( req, gatewayName)
            return tradeDf
        except:
            traceback.print_exc()
            tradeDf = pd.DataFrame()
            return tradeDf



    def sendOrder(self, symbol, orderType, price, volume, strategy):
        try:
            req = VtOrderReq()
            req.symbol = symbol
            req.vtSymbol = symbol
            req.price = price
            req.volume = volume
            req.priceType = PRICETYPE_LIMITPRICE

            gatewayName = "TradeDllAShare"

            # CTA委托类型映射
            if orderType == CTAORDER_BUY:
                req.direction = DIRECTION_LONG
            elif orderType == CTAORDER_SELL:
                req.direction = DIRECTION_SHORT
            else:
                self.writeLog(u"不支持订单方向类型:" + orderType )

            VtOrderID = self.mainEngine.sendOrder(req, gatewayName)

            if VtOrderID:
                # 下单成功，添加orderid和策略对应关系
                # self.orderStrategyDict[VtOrderID] = strategy  # 保存order和策略的映射关系
                # self.strategyDict[strategy.strategyID].addOrder(VtOrderID)  # 添加到策略委托号集合中

                self.writeLog(u'策略%s发送委托成功，%s，%s，%s@%s'
                                 %(strategy.strategyID, symbol, req.direction, volume, price))
            else:
                self.writeLog(u"策略%s发送委托失败，%s，%s，%s@%s"
                                 %(strategy.strategyID, symbol, req.direction, volume, price))

            return VtOrderID
        except:
            traceback.print_exc()
            return VtOrderID

    def cancelOrder(self,orderId, symbol, strategy):

        try:
            req = VtCancelOrderReq()
            req.orderID = orderId
            req.symbol = symbol

            gatewayName = "TradeDllAShare"

            rc = self.mainEngine.cancelOrder(req, gatewayName)

            if rc == 0 :
                self.writeLog(u'策略%s取消委托[%s %s]成功'
                                 %(strategy.strategyID, orderId, symbol ))
            else:
                self.writeLog(u'策略%s取消委托[%s %s]失败'
                                 %(strategy.strategyID, orderId, symbol))

            return 0
        except:
            traceback.print_exc()
            return -1


    def getOrderBook(self,symbol,strategy):
        pass

    def updateUI(self,stra):
        try:
            # stra 状态没有变化不需要更新UI
            if not stra.isUpdated():
                return

            for plateName in stra.plateDict:
                plateSymbolList = stra.plateDict[plateName]["symbol_list"]
                plateCatchedSymobolList = stra.plateDict[plateName]["catched_symbol"]
                plateMissedSymbolList = stra.plateDict[plateName]["missed_symbol"]

                event1 = Event(type_= EVENT_STRATEGY_CATCH_LIMITUP_STATUS)

                catchLimitUpInfo = VtStrategyCatchLimitUpInfo()
                event1.dict_['data'] = catchLimitUpInfo

                catchLimitUpInfo.plateName = plateName
                catchLimitUpInfo.numOfStocks = len(plateSymbolList)
                catchLimitUpInfo.catchedStocks = len(plateCatchedSymobolList)
                catchLimitUpInfo.missedStocks = len(plateMissedSymbolList)

                self.eventEngine.put(event1)


            stra.resetUpdatedFlag()
        except:
            traceback.print_exc()

    def writeLog(self, content):
        try:
            """快速发出日志事件"""
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'CATCH_LIMITUP_ENGINE'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()

if __name__ == '__main__':
    eng = CatchLimitUpEngine(None,None)
    eng.start()

    straConfig = {}
    straConfig['stockPoolFile'] = eng.config['stockPoolFile']

    eng.addStrategy(straConfig)

    print(eng.config)