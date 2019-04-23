# encoding: UTF-8


from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate
from vnpy.trader.language.chinese.constant import *
from constant import (TRADE_DIRECTION_SELL, TRADE_DIRECTION_BUY, CROSS_DIRECTION_DOWN,CROSS_DIRECTION_UP,
                      STOP_ORDER_THRESHOLD_DIRECTION_GREATER, STOP_ORDER_THRESHOLD_DIRECTION_LESS)
from commonFunction import *
from copy import copy

import traceback

########################################################################
class PriceTimeLine(object):

    def __init__(self):
        try:
            self.highestPriceDatetime = []
            self.lowestPriceDatetime = []
            self.latestPriceDatetime = []

            self.preClosePrice = EMPTY_FLOAT

            self.getFirstQuote = False

            self.waitingReset = False
        except:
            traceback.print_exc()

    def reset(self):

        self.highestPriceDatetime = []
        self.lowestPriceDatetime = []




    def appendPrice(self,tick):
        try:
            newPrice = tick.lastPrice
            newDatetime = tick.datetime
            self.latestPriceDatetime = [newPrice, newDatetime]

            if not self.getFirstQuote:
                self.highestPriceDatetime = self.latestPriceDatetime
                self.lowestPriceDatetime = self.latestPriceDatetime
                self.getFirstQuote = True
                return

            # 更新最高最低价
            if newPrice > self.highestPriceDatetime[0]:
                self.highestPriceDatetime = self.latestPriceDatetime
            if newPrice < self.lowestPriceDatetime[0]:
                self.lowestPriceDatetime = self.latestPriceDatetime
        except:
            traceback.print_exc()

    def getGapLowest(self):
        try:
            return self.latestPriceDatetime[0] - self.lowestPriceDatetime[0]
        except:
            traceback.print_exc()

    def getGapHighest(self):
        try:
            return self.highestPriceDatetime[0] - self.latestPriceDatetime[0]
        except:
            traceback.print_exc()

    def getHighestPrice(self):
        try:
            return self.highestPriceDatetime[0]
        except:
            traceback.print_exc()

    def getLowestPrice(self):
        try:
            return self.lowestPriceDatetime[0]
        except:
            traceback.print_exc()



########################################################################
class StopOrderStrategy(CtaTemplate):
    """"""
    className = 'StopOrderStrategy'
    author = u'我叫止损赢'
    TRADE_FORWARD = "F"
    TRADE_BACKWARD = "B"

    def __init__(self, stopOrderEngine, setting):
        super(StopOrderStrategy,self).__init__(stopOrderEngine, setting)

        try:
            self.status = STRATEGY_STATUS_NOT_STARTED

            # save strategy setting. use it to create new strategy with same setting
            self.setting = setting

            # 如果强制查询摆盘。是否可以不处理摆盘事件了。
            # Todo 待优化
            self.forceQryOrderBook = True

            self.stockCode = setting["stockCode"]
            self.stockOwnerCode = setting["stockOwnerCode"]
            self.volume = setting["volume"]
            self.allowedDrawbackPct = setting["allowedDrawbackPct"] / 100
            self.orderPriceStrategy = setting["orderPriceStrategy"]
            self.beforeCloseTime = setting["beforeCloseTime"]
            self.incPct = setting["incPct"] / 100
            self.keepPositionPct = setting["keepPositionPct"] / 100
            self.crossDirection = setting["crossDirection"]  # 标的与正股涨跌的关系，正向 或 反向
            self.tradeDirection = setting["tradeDirection"]  # 交易方向
            self.nextTradeDirection = None
            self.setNextTradeDirection(self.TRADE_FORWARD)
            self.thresholdPrice = setting["thresholdPrice"]  # 策略启动的价格threshold
            self.thresholdIsPct = setting["thresholdIsPct"]  # thresholdPrice 是不是百分比
            self.thresholdPriceEnabled = setting["thresholdPriceEnabled"] # threshold price 是否开启
            self.realThresholdPrice = None  # 如果传入的threshold为pct，转换成真实的threshold price价格
            self.startThresholdDirection = setting["startThresholdDirection"]
            self.isThresholdPriceBroken = False # 交易方向转换不需要重置，之前有交易必然会变成False
            self.profitPct = 0.02   # 改成UI输入

            # 一个策略只能有一个symbol 用于下单。 这个不够灵活，需要改
            # 这是在sendorder时候默认使用的symblo
            self.vtSymbol = self.stockCode

            # 策略唯一标识
            # self.strategyID = self.tradeDirection + self.stockCode +"+" + self.stockOwnerCode
            self.strategyID = self.stockOwnerCode + self.crossDirection[2:4] + self.tradeDirection + self.stockCode

            orderBook1 = {'bid': [0 for i in range(10)], 'ask': [0 for i in range(10)]}
            orderBook2 = {'bid': [0 for i in range(10)], 'ask': [0 for i in range(10)]}
            self.orderBookDict = {self.stockCode:orderBook1, self.stockOwnerCode:orderBook2}
            pTimeLine1 = PriceTimeLine()
            pTimeLine2 = PriceTimeLine()
            self.quoteDict = {self.stockCode:pTimeLine1, self.stockOwnerCode:pTimeLine2}

            # 收到第一个tick时根据pre_close计算
            self.drawbackGap = EMPTY_FLOAT
            self.incGap = EMPTY_FLOAT
            # 方向变化时，根据之前挂单是正股价格计算
            self.profitGap = EMPTY_STRING
            self.orderPrice1 = None
            self.orderPrice2 = None
            #
            self.marketCloseTime = EMPTY_STRING

            # 以后需要根据incGap来判断需要保留多少
            self.sellVolumeBeforeClose = self.volume

            # 保存策略发出的order
            self.workingOrderList = []
            self.orderList = []
        except:
            traceback.print_exc()

    def getNextTradeDirection(self):
        return self.nextTradeDirection

    def setNextTradeDirection(self, forwardDirection):
        try:
            if forwardDirection == self.TRADE_FORWARD:
                if self.nextTradeDirection == None:
                    if self.tradeDirection in [TRADE_DIRECTION_BUY, TRADE_DIRECTION_BUY_THEN_SELL]:
                        self.nextTradeDirection = TRADE_DIRECTION_BUY
                    elif self.tradeDirection in [TRADE_DIRECTION_SELL, TRADE_DIRECTION_SELL_THEN_BUY]:
                        self.nextTradeDirection = TRADE_DIRECTION_SELL
                    else:
                        raise Exception(u"交易方向参数设置不正确")
                elif self.nextTradeDirection == TRADE_DIRECTION_BUY and self.tradeDirection == TRADE_DIRECTION_BUY_THEN_SELL:
                    self.nextTradeDirection = TRADE_DIRECTION_SELL
                elif self.nextTradeDirection == TRADE_DIRECTION_SELL and self.tradeDirection == TRADE_DIRECTION_SELL_THEN_BUY:
                    self.nextTradeDirection = TRADE_DIRECTION_BUY
                # 其他情况没有后续的交易
                else:
                    self.nextTradeDirection = None
            elif forwardDirection == self.TRADE_BACKWARD:
                # 目前不处理后退的情况
                pass
        except:
            traceback.print_exc()

    def start(self):
        self.trading = True
        self.status = STRATEGY_STATUS_WAITING_FOR_FIRST_QUOTE

    def addOrder(self,orderID):
        try:
            self.orderList.append(orderID)
            self.workingOrderList.append(orderID)
        except:
            traceback.print_exc()

    def removeWorkingOrder(self, orderID):
        try:
            self.workingOrderList.remove(orderID)
        except:
            traceback.print_exc()

    def orderFinished(self, orderID):
        self.removeWorkingOrder(orderID)
        self.changeStatusWhenOrderFinished()
        self.setNextTradeDirection(self.TRADE_FORWARD)
        self.resetForNextTrade()


    def resetForNextTrade(self):

        if self.nextTradeDirection != None :
            # 根据新的Trade重置部分策略参数
            self.quoteDict[self.self.stockOwnerCode].reset()

    def orderCancelled(self, orderID):
        self.removeWorkingOrder(orderID)
        self.status = STRATEGY_STATUS_ORDER_CANCELLED

    def changeStatusWhenOrderFinished(self):
        # 当策略有订单成交并且，策略是先买后卖时，改变状态为等待卖出
        if self.status == STRATEGY_STATUS_ORDER_WORKING and self.tradeDirection == TRADE_DIRECTION_BUY_THEN_SELL :
            self.status = STRATEGY_STATUS_ALREADY_BUY_NEED_SELL
        elif self.status == STRATEGY_STATUS_ORDER_WORKING and self.tradeDirection == TRADE_DIRECTION_SELL_THEN_BUY :
            self.status = STRATEGY_STATUS_ALREADY_SELL_NEED_BUY
        # 其他情况设置状态为完成
        else:
            self.status = STRATEGY_STATUS_COMPLETE

    # 返回策略需要订阅的symbol
    def getSymbolList(self):
        try:
            if self.stockCode == self.stockOwnerCode:
                return [self.stockCode]
            else:
                return [self.stockCode, self.stockOwnerCode]
        except:
            traceback.print_exc()

    def onTick(self, tick):

        try:
            # 报价信息分为两类产生来源 “QUOTE” “ORDER_BOOK”
            tickType = tick.subType

            if tickType == "QUOTE":
                self.addQuote(tick)
            elif tickType == "ORDER_BOOK":
                self.updateOrderBook(tick)
        except:
            traceback.print_exc()

    def addQuote(self, tick):
        try:
            symbol = tick.symbol
            # 判断tick是否为当天数据， 不是的不处理
            # ToDo 需要判断日期是否有变化，策略目前不能跨天运行
            if not self.isTodayTick(tick):
                return

            pTimeLine = self.quoteDict[symbol]

            # 第一个报价tick信息，初始化昨收,开盘价
            if not pTimeLine.getFirstQuote :
                pTimeLine.preClosePrice = tick.preClosePrice

                # 根据正股昨收价计算相应的指标。
                # 只有正股才会计算以下数据，后面code的罗辑要考虑到标的的tick先于正股到达的情况，不要产生一些正股数据没初始化问题
                # 此策略所有流程都是根据正股股价做出判断，不会产生问题。
                if symbol == self.stockOwnerCode:
                    self.drawbackGap =  pTimeLine.preClosePrice * self.allowedDrawbackPct
                    self.drawbackGap = round(self.drawbackGap, 3)
                    self.incGap = pTimeLine.preClosePrice * self.incPct
                    self.incGap = round(self.incGap, 3)
                    self.marketCloseTime = getMarketCloseTimeBySymbol(symbol)

                    # 处理thresholdPirce 价格
                    if self.thresholdPriceEnabled:
                        if self.thresholdIsPct:
                            self.realThresholdPrice = pTimeLine.preClosePrice * (1 + self.thresholdPrice)
                            self.realThresholdPrice = round(self.realThresholdPrice, 3)
                        else:
                            self.realThresholdPrice = self.thresholdPrice

                    # 如果是open tick，并且策略设定为需要考虑开盘就触发的情况
                    # todo 增加设置选项参数
                    if self.isOpenTick(tick) and False:
                        # 创造一个open tick，放入TimeLine.
                        # open tick的报价为昨收价
                        openTick = copy(tick)
                        openTick.lastPrice = tick.preClosePrice
                        pTimeLine.appendPrice(openTick)

                    # 收到第一份正股当天报价信息，进入运行状态
                    self.status = STRATEGY_STATUS_RUNNING

            # 正股和标的都更新pTimeLine
            pTimeLine.appendPrice(tick)


            gap = 0
            if symbol == self.stockOwnerCode:
                # 如果启动了threshold 检查新价格是否突破了threshold，没突破则不需要后续处理
                # 突破过一次即可，后续不在检查是否突破
                if self.thresholdPriceEnabled and not self.isThresholdPriceBroken:
                    self.isThresholdPriceBroken = self.doesTickBreakThresholdPrice(tick)
                    if not self.isThresholdPriceBroken:
                        return

                # 判断正股新的报价是否超出了设定的正股的回撤范围
                # 如果标的波动与正股是正向关系, 检查从高点下跌的幅度
                if self.crossDirection == CROSS_DIRECTION_DOWN:
                    gap = pTimeLine.getGapHighest()
                # 如果标的波动与正股是反向关系, 检查从低点反弹的幅度
                elif self.crossDirection == CROSS_DIRECTION_UP:
                    gap = pTimeLine.getGapLowest()

                # 检查距离收盘结束时间, < 预设的强行交易时间则触发强制卖出
                # 使用正股最新报价信息作为当前时间， 如果正股报价长时间不产生报价会导致问题？？？
                # todo
                timeLeftToClose = timeStrSub(self.marketCloseTime, tick.time)
                actionByForce = False
                if timeLeftToClose < self.beforeCloseTime:
                    actionByForce = True
                    # 考虑当天正股的涨跌幅，保留适当仓位
                    # todo：
                    # self.volume = self.sellVolumeBeforeClose
                    print(u"收盘前强制卖出")

                # 如果gap大于设定的允许值or到达收盘前强制清仓时间，并且没有正在等待成交的订单，则触发交易
                # 交易价格从标的的摆盘数据获得
                orderId = ""
                if (gap > self.drawbackGap or actionByForce) and self.status != STRATEGY_STATUS_ORDER_WORKING:
                    if self.tradeDirection == TRADE_DIRECTION_SELL:
                        orderPrice = self.getOrderPrice()
                        orderId = self.sell(orderPrice, self.volume)
                    elif self.tradeDirection == TRADE_DIRECTION_BUY:
                        orderPrice = self.getOrderPrice()
                        orderId = self.buy(orderPrice, self.volume)
                    else:
                        raise Exception(u"交易方向参数设置不正确")
                    # orderId不空，表示下单成功
                    if orderId:
                        self.status = STRATEGY_STATUS_ORDER_WORKING
                    else:
                        self.status = STRATEGY_STATUS_ORDER_FAIL
        except:
            traceback.print_exc()

    def doesTickBreakThresholdPrice(self, tick):
        try:
            result = False
            lastPrice = tick.lastPrice
            if self.startThresholdDirection == STOP_ORDER_THRESHOLD_DIRECTION_GREATER:
                if lastPrice > self.realThresholdPrice:
                    result = True
            elif self.startThresholdDirection == STOP_ORDER_THRESHOLD_DIRECTION_LESS:
                if lastPrice < self.realThresholdPrice:
                    result = True
            return result

        except:
            return False
            traceback.print_exc()

    # 判断tick是否为开盘第一个报价
    def isOpenTick(self,tick):
        return False

    def isTodayTick(self,tick):
        try:
            tickDateStr = tick.date
            symbol = tick.symbol
            todayStr = self.ctaEngine.getTodayStr(symbol)
            if tickDateStr == todayStr:
                return True
            else:
                return False
        except:
            traceback.print_exc()

    def statusAllowTickIn(self):
        if self.status == STRATEGY_STATUS_RUNNING \
            or self.status == STRATEGY_STATUS_ORDER_WORKING \
            or self.status == STRATEGY_STATUS_WAITING_FOR_FIRST_QUOTE \
            or self.status == STRATEGY_STATUS_ALREADY_SELL_NEED_BUY \
            or self.status == STRATEGY_STATUS_ALREADY_BUY_NEED_SELL :
            return True
        else:
            return False

    def statusNeedComplete(self):
        if self.status == STRATEGY_STATUS_COMPLETE \
           or self.status == STRATEGY_STATUS_CANCEL \
           or self.status == STRATEGY_STATUS_ORDER_CANCELLED \
           or  self.status == STRATEGY_STATUS_ORDER_FAIL:
            return True
        else:
            return False

    def statusAllowCancellation(self):
        if self.status == STRATEGY_STATUS_RUNNING \
            or self.status == STRATEGY_STATUS_WAITING_FOR_FIRST_QUOTE \
            or self.status == STRATEGY_STATUS_ALREADY_SELL_NEED_BUY \
            or self.status == STRATEGY_STATUS_ALREADY_BUY_NEED_SELL :
            return True
        else:
            return False

    def getOrderPrice(self):
        try:
            price = 0
            bid1, ask1 = self.getLatestOrderBook(self.stockCode, 1)
            if self.orderPriceStrategy == ORDER_PRICE_ORDERBOOK:
                if self.tradeDirection == TRADE_DIRECTION_SELL:
                    price = bid1
                elif self.tradeDirection == TRADE_DIRECTION_BUY:
                    price = ask1
            elif self.orderPriceStrategy == ORDER_PRICE_AVG_ORDERBOOK:
                price = (bid1 + ask1) / 2
                price = round(price, 3)
            print(u"下单价格:%s"%price)
            return price
        except:
            traceback.print_exc()

    def updateOrderBook(self,tick):
        try:
            symbol = tick.symbol
            orderBook = self.orderBookDict[symbol]
            orderBook["bid"][0] = tick.bidPrice1
            orderBook["ask"][0] = tick.askPrice1
        except:
            traceback.print_exc()

    def getLatestOrderBook(self, symbol, index):

        try:
            # 极限情况下程序一启动就触发清仓，此时orderbook可能还没更新，需要主动查询摆盘
            # ToDo 从摆盘缓存取报价，不需要缓存摆盘
            bid1 =  self.orderBookDict[symbol]["bid"][index-1]
            ask1 =  self.orderBookDict[symbol]["ask"][index-1]
            print(u"缓存摆盘bid1:%s  ask1:%s" %(bid1,ask1))
            # 如果指定强制查询最新摆盘
            if self.forceQryOrderBook:
                bid1 = 0
                ask1 = 0
            #  还未获得推送的信息，则主动查询摆盘第一档
            if bid1 == 0 or ask1 == 0 :
                orderBookDict = self.getOrderBook(symbol)
                bid1 = orderBookDict['Bid'][0][0]
                ask1 = orderBookDict['Ask'][0][0]
                print(u"主动查询摆盘价bid1:%s  ask1:%s" % (bid1, ask1))

            return bid1, ask1
        except:
            traceback.print_exc()

    def onOrder(self, order):
        pass

    def onTrade(self, trade):
        pass

    def getOrderBook(self, symbol):
        try:
            orderBook = self.ctaEngine.getOrderBook(symbol, self)
            return orderBook
        except:
            traceback.print_exc()

    def getOwnerPrice(self):
        try:
            pTimeline = self.quoteDict[self.stockOwnerCode]
            # owner pirceline可能还没有数据,防止访问越界
            if len(pTimeline.latestPriceDatetime):
                return pTimeline.latestPriceDatetime[0]
            else:
                return 0
        except:
            traceback.print_exc()

    def getOwnerMaxMinPrice(self):
        try:
            pTimeline = self.quoteDict[self.stockOwnerCode]
            price = 0
            # owner pirceline可能还没有数据，防止访问越界
            if len(pTimeline.latestPriceDatetime):
                if self.crossDirection == CROSS_DIRECTION_UP:
                    price = pTimeline.lowestPriceDatetime[0]
                elif self.crossDirection == CROSS_DIRECTION_DOWN:
                    price = pTimeline.highestPriceDatetime[0]

            return price
        except:
            traceback.print_exc()

    def getTriggerPrice(self):
        try:
            pTimeline = self.quoteDict[self.stockOwnerCode]
            triggerPrice = 0
            # owner pirceline可能还没有数据，防止访问越界
            if len(pTimeline.latestPriceDatetime):
                if self.crossDirection == CROSS_DIRECTION_UP:
                    price = pTimeline.lowestPriceDatetime[0]
                    triggerPrice = price + self.drawbackGap
                elif self.crossDirection == CROSS_DIRECTION_DOWN:
                    price = pTimeline.highestPriceDatetime[0]
                    triggerPrice = price - self.drawbackGap

            return triggerPrice
        except:
            traceback.print_exc()
