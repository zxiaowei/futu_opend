# encoding: utf-8

from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate
from vnpy.trader.language.chinese.constant import *

from commonFunction import *
from copy import copy
import pandas as pd
from vnpy.trader.vtFunction import getJsonPath
import traceback
import time

CTAORDER_BUY = u'买开'
CTAORDER_SELL = u'卖平'

class LimitUpPriceTimeLine(object):

    TRIGGER_CATCH_UP_THREAHOLD = -0.08

    def __init__(self, symbol):
        self.symbol = symbol
        self.waitForFirstQuote = True
        # 抓板触发价格
        self.triggerCatchUpPrice = 99999

        self.preClosePrice = 0
        self.limitUpPrice = 0
        self.limitDownPrice = 0

        self.openPrice = 0
        self.highPrice = 0
        self.lowPrice = 0
        self.lastPrice = 0
        self.lastPrice2 = 0

        # 触碰涨跌停次数，
        self.touchUpCount = 0
        self.touchDownCount = 0
        self.keepUp = False
        self.keepDown = False

        # 涨跌停打开次数
        self.breakUpCount = 0
        self.breakDownCount = 0
        self.breakUp = False
        self.breakDown = False

    def appendPrice(self, tick):
        if self.waitForFirstQuote:
            self.preClosePrice = tick.preClosePrice
            self.limitUpPrice = round(self.preClosePrice*1.1, 2)
            self.limitDownPrice = round(self.preClosePrice*0.9, 2)
            self.openPrice = tick.openPrice
            self.waitForFirstQuote = False
            self.triggerCatchUpPrice = round(self.preClosePrice * (1+self.TRIGGER_CATCH_UP_THREAHOLD), 2)
            # 初始化最新的俩个价格为第一个报价
            self.lastPrice2 = tick.lastPrice
            self.lastPrice = tick.lastPrice

        self.highPrice = tick.highPrice
        self.lowPrice = tick.lowPrice
        self.lastPrice2 = self.lastPrice
        self.lastPrice = tick.lastPrice

        # 统计触碰涨跌停情况
        if self.lastPrice == self.limitUpPrice :
            if not self.keepUp:
                self.touchUpCount += 1
                self.keepUp = True
                self.keepDown = False
                self.breakUp = False
                # self.breakDown = False
        elif self.lastPrice == self.limitDownPrice :
            if not self.keepDown:
                self.touchDownCount += 1
                self.keepUp = False
                self.keepDown = True
                # self.breakUp = False
                self.breakDown = False

        # 统计打开涨跌停情况
        if self.lastPrice < self.limitUpPrice:
            if self.keepUp:
                self.breakUpCount += 1
                self.keepUp = False
                # self.keepDown = False
                self.breakUp = True
                self.breakDown = False
        if self.lastPrice > self.limitDownPrice:
            if self.keepDown:
                self.breakDownCount += 1
                # self.keepUp = False
                self.keepDown = False
                self.breakUp = False
                self.breakDown = True

    def isUp(self):
        return self.lastPrice >= self.lastPrice2

    def triggerCatch(self):
        return self.lastPrice > self.triggerCatchUpPrice and self.isUp()

class CatchLimitUpStrategy(CtaTemplate):

    TOTAL_ALLOWED_CATCHED_SYMBOL = 11
    ALLOW_MISSED_IN_ONE_PLATE = 1
    ALLOW_CATCH_IN_ONE_PLATE = 1
    TOTAL_ALLOWED_VALUE = 100000

    def __init__(self, catchLimitUpEngine, straConfig):
        super(CatchLimitUpStrategy,self).__init__(catchLimitUpEngine, None)

        self.strategyID = "catchLimitUp"
        self.isUpdatedFlag = False

        self.config = straConfig

        self.stockPoolDf = None  # df ['symbol','name','industry']
        self.plateDict = {}  # dict {plate:{symbol_list:[],catched_symbol:[],missed_symbol:[]}}
        self.symbolToPlate = {}  # symbol map to plate {symbol:{plate_list:[], state: 'normal,catched,catching,missed,breakopen'}}
        self.symbolPriceTimeLineDict = {} #{symbol:LimitUpPriceTimeLine}

        self.totalCachedCount = 0
        self.totalCatchedValue = 0

    def start(self):

        self.config['stockPoolFile'] = getJsonPath(self.config['stockPoolFile'], __file__)
        self.stockPoolDf = pd.read_excel(self.config['stockPoolFile'],dtype={"symbol": "str"})
        self.stockPoolDf = self.stockPoolDf[['symbol','name','industry']]

        for index, row in self.stockPoolDf.iterrows():
            plateName = row['industry']
            symbol = row['symbol']

            if not plateName in self.plateDict:
                self.plateDict[plateName] = {"symbol_list":[],"catched_symbol":[],"missed_symbol":[]}
            if not symbol in self.plateDict[plateName]["symbol_list"]:
                self.plateDict[plateName]["symbol_list"].append(symbol)

            if not symbol in self.symbolToPlate:
                self.symbolToPlate[symbol] = {'plate_list':[],'state':'normal'}
            if not plateName in self.symbolToPlate[symbol]:
                self.symbolToPlate[symbol]['plate_list'].append(plateName)

        self.isUpdatedFlag = True

    def getSubscribeList(self):
        return self.getSymbolList()

    def getSymbolList(self):
        symbolList = self.symbolToPlate.keys()
        return list(symbolList)

    def onTick(self, tick):
        try:
            # 报价信息分为两类产生来源 “QUOTE” “ORDER_BOOK”
            tickType = tick.subType

            if tickType == "QUOTE":
                self.addQuote(tick)
            elif tickType == "ORDER_BOOK":
                pass
        except:
            traceback.print_exc()

    def addQuote(self,tick):
        try:
            symbol = tick.symbol
            timeStr = tick.date + " " + tick.time
            # 判断tick是否为当天数据， 不是的不处理
            # ToDo 需要判断日期是否有变化，策略目前不能跨天运行
            # if not self.isTodayTick(tick):
            #     return

            if not symbol in self.symbolPriceTimeLineDict:
                self.symbolPriceTimeLineDict[symbol] = LimitUpPriceTimeLine(symbol)

            # 第一个报价tick信息，初始化昨收,开盘价
            priceTimeLine = self.symbolPriceTimeLineDict[symbol]
            priceTimeLine.appendPrice(tick)

            # 目前假设一个symbol对应一个plate
            plateName = self.symbolToPlate[symbol]['plate_list'][0]
            plateInfo = self.plateDict[plateName]
            # 对应于未抓到，但是后来又开板的股票如何处理？？ 先从miss里面移除掉
            if priceTimeLine.breakUp and symbol in plateInfo['missed_symbol']:
                plateInfo['missed_symbol'].remove(symbol)
                self.symbolToPlate[symbol]['state'] = 'normal'
                self.isUpdatedFlag = True
                print("[%s][%s][%s]现价[%s]涨停价[%s]已开板.移除未抓到标记" \
                  % (timeStr, plateName, symbol, \
                     priceTimeLine.lastPrice, priceTimeLine.limitUpPrice))

            # 抓板考虑是盘中突然拉升情况再抓，还是开盘就强力拉升的也抓
            # 现简单判断超过某价格并且是上涨就抓

            if priceTimeLine.triggerCatch():
                # 抓取正常状态的symbol
                state = self.symbolToPlate[symbol]['state']
                if state != 'normal':
                    return

                # 如价格已经涨停不抓，直接标记为missed
                if priceTimeLine.keepUp:
                    if not symbol in plateInfo['missed_symbol']:
                        plateInfo['missed_symbol'].append(symbol)
                        self.symbolToPlate[symbol]['state'] = 'missed'
                        self.isUpdatedFlag = True
                        print("[%s][%s][%s]触发价[%s]为涨停价[%s].标记为未抓到" \
                              % (timeStr, plateName, symbol, \
                                 priceTimeLine.lastPrice, priceTimeLine.limitUpPrice))
                        return

                # 如果所属板块已经抓到过一个则不再抓取同一个板块的股票
                catchedCount = len(plateInfo['catched_symbol'])
                if catchedCount >= self.ALLOW_CATCH_IN_ONE_PLATE:
                    print("[%s][%s]所属板块[%s]允许抓取[%s]支股票,已经抓满%s请求被拒绝。触发价格为[%s]" \
                          % (timeStr, symbol, plateName, self.ALLOW_CATCH_IN_ONE_PLATE, plateInfo['catched_symbol'],\
                             priceTimeLine.lastPrice) )
                    return

                # 如果已经错过该板块2个股票，则不进行抓取龙3。 只抓龙1龙2
                missedCount = len(plateInfo['missed_symbol'])
                if missedCount >= self.ALLOW_MISSED_IN_ONE_PLATE:
                    print("[%s][%s]所属板块[%s]允许错过[%s]支股票,已经错过%s请求被拒绝。触发价格为[%s]" \
                          % (timeStr, symbol, plateName, self.ALLOW_MISSED_IN_ONE_PLATE, plateInfo['missed_symbol'],\
                             priceTimeLine.lastPrice) )
                    return

                # 控制总金额
                if self.totalCatchedValue + priceTimeLine.lastPrice * 100 > self.TOTAL_ALLOWED_VALUE:
                    print("[%s]总共允许抓取金额[%.2f],已经抓到[%.2f]无法满足[%s]触发价格为[%s x %d]的金额请求" \
                          % (timeStr, self.TOTAL_ALLOWED_VALUE, self.totalCatchedValue,symbol, \
                             priceTimeLine.lastPrice, 100) )
                    return

                #控制总抓取数量
                if self.totalCachedCount >= self.TOTAL_ALLOWED_CATCHED_SYMBOL:
                    print("[%s]总共允许抓取[%s]支股票,已经抓满请求被拒绝。[%s]触发价格为[%s]" \
                          % (timeStr, self.TOTAL_ALLOWED_CATCHED_SYMBOL, symbol,\
                             priceTimeLine.lastPrice) )
                    return


                # 到此处开始下单抓涨，并修改板块和symbol的状态
                # 精确状态依赖于成交反馈， 目前先认为下单即为成交了
                #目前假设一个symbol对应一个plate
                plateInfo['catched_symbol'].append(symbol)
                self.symbolToPlate[symbol]['state'] = 'catched'
                self.totalCachedCount += 1
                self.totalCatchedValue += priceTimeLine.lastPrice * 100
                self.isUpdatedFlag = True
                print("[%s]追涨下单第[%s]支[%s][%s]触发价[%s x %d]涨停价[%s].策略累计金额[%.2f]" \
                      % (timeStr, self.totalCachedCount, plateName, symbol, \
                         priceTimeLine.lastPrice, 100, priceTimeLine.limitUpPrice, self.totalCatchedValue))
                orderId = self.ctaEngine.sendOrder(symbol, CTAORDER_BUY, priceTimeLine.limitUpPrice, 100, self)
                if orderId:
                    pass
                    # time.sleep(5)
                    # rc = self.ctaEngine.cancelOrder(orderId, symbol, self)
                    # if rc != 0:
                    #     print("FFFFFFFFFFail")
                else: # 下单失败
                    print(u"下单失败")


        except:
            traceback.print_exc()

    def isUpdated(self):
        return self.isUpdatedFlag

    def resetUpdatedFlag(self):
        self.isUpdatedFlag = False