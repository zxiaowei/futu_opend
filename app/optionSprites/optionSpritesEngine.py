# encoding: utf-8

import traceback
from vnpy.trader.app import AppEngine
import json
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.vtEvent import EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_POSITION, EVENT_LOG
from vnpy.event.eventEngine import Event
from vnpy.trader.vtObject import VtSubscribeReq, VtOrderReq, VtLogData, VtTradingDaysReq
from qssBasic import VtOptionTickData, EVENT_OPTION_TICK
import time
from copy import copy
from commonFunction import (bsm_call_value, bsm_put_value, getDatetimeOfSymbolTimezone, dateStrSub, RISK_FREE_RATE,
                            OPTION_TYPE_PUT, OPTION_TYPE_CALL, getMarketBySymbol)
from vnpy.trader.language.chinese.constant import PRICETYPE_LIMITPRICE
from constant import TRADING_DAYS_1YEAR


class OptionSpritesEngine(AppEngine):

    def __init__(self, mainEngine, eventEngine):
        try:
            self.mainEngine = mainEngine
            self.eventEngine = eventEngine

            self.configFileName = 'option_sprites_config.json'
            self.configFile = getJsonPath(self.configFileName, __file__)
            self.config = {}

            self.workingOptionDict = {}
            self.optionTick = {}

            # 用于从正股找到option
            self.ownerToOption = {}

        except:
            traceback.print_exc()

    def start(self):
        # load pre-defined stock ownership
        try:
            f = open(self.configFile,encoding = 'utf-8')
            self.config = json.load(f)
            f.close()
        except:
            self.writeLog(u'载入' + self.configFile + u'文件出错')
            return

        self.registerEvent()


    def stop(self):
        pass


    def registerEvent(self):
        try:
            self.eventEngine.register(EVENT_TICK, self.processTick)
            self.eventEngine.register(EVENT_ORDER, self.processOrder)
            self.eventEngine.register(EVENT_TRADE, self.processDeal)
            self.eventEngine.register(EVENT_POSITION, self.processPositionEvent)
        except:
            traceback.print_exc()

    def startMonitorOption(self, optionDetail):
        try:
            optionCode = optionDetail["OptionCode"]
            # 之前已经处理过，不需要再订阅
            if optionCode not in self.workingOptionDict:
                # 维护option信息dict
                self.workingOptionDict[optionCode] = {"OwnerCode": optionDetail["OwnerCode"],
                                                      "StrikeDate": optionDetail["StrikeDate"],
                                                      "Type": optionDetail["Type"],
                                                      "StrikePrice": optionDetail["StrikePrice"]}

                # 维护正股对应的option list
                # 正股可能之前随其他option出现过
                ownerCode = optionDetail["OwnerCode"]
                if ownerCode not in self.ownerToOption:
                    optionList = []
                    self.ownerToOption[ownerCode] = optionList
                self.ownerToOption[ownerCode].append(optionCode)

                # 订阅option和正股的报价+摆盘
                self.subscribeForOption(optionCode)
        except:
            traceback.print_exc()

    def subscribeForOption(self, optionCode):
        try:
            optionDetail= self.workingOptionDict[optionCode]
            codeList = (optionCode, optionDetail["OwnerCode"])
            for stockCode in codeList:
                req = VtSubscribeReq()
                req.symbol = stockCode
                self.mainEngine.subscribe(req, 'FUTU')
                # time.sleep(1)
        except:
            traceback.print_exc()


    def processTick(self, event):
        try:
            tick = event.dict_['data']
            symbol = tick.symbol

            # 期权的报价和摆盘信息都要处理
            if self.isMonitoredOption(symbol):
                # 生成optionTickData 存储option用于展示的信息
                if symbol not in self.optionTick:
                    self.optionTick[symbol] = VtOptionTickData()
                optionTickData = self.optionTick[symbol]

                if tick.subType == "QUOTE":
                    optionTickData.optionCode = symbol
                    optionTickData.strikePrice = tick.strikePrice
                    optionTickData.latestPrice = tick.lastPrice
                    optionTickData.impliedVolatility = tick.impliedVolatility/100

                elif tick.subType == "ORDER_BOOK":
                    optionTickData.bid1 = tick.bidPrice1
                    optionTickData.ask1 = tick.askPrice1

            # 正股只处理报价信息
            if self.isMonitorOwnerCode(symbol):
                if tick.subType == "QUOTE":
                    for optionCode in self.ownerToOption[symbol]:
                        # 还没有获得期权报价信息时，无法进一步计算公允价格，忽略此条正股报价
                        if optionCode in self.optionTick:
                            optionTickData = self.optionTick[optionCode]
                            optionTickData.ownerCode = symbol
                            optionTickData.ownerPrice = tick.lastPrice
                            optionTickData.strikeDate = self.workingOptionDict[optionCode]["StrikeDate"]
                            optionTickData.type = self.workingOptionDict[optionCode]["Type"]


                            # 计算公允价
                            S0 = optionTickData.ownerPrice
                            K = optionTickData.strikePrice
                            currentDateStr = getDatetimeOfSymbolTimezone(symbol).strftime("%Y-%m-%d")
                            market = getMarketBySymbol(symbol)
                            days = self.getTradingDays(market, currentDateStr, optionTickData.strikeDate)
                            T = round(len(days) / TRADING_DAYS_1YEAR, 4)
                            r = RISK_FREE_RATE
                            sigma = optionTickData.impliedVolatility
                            if optionTickData.type == OPTION_TYPE_PUT:
                                optionTickData.calculatedPrice = bsm_put_value(S0,K,T,r,sigma)
                            elif optionTickData.type == OPTION_TYPE_CALL:
                                optionTickData.calculatedPrice = bsm_call_value(S0,K,T,r,sigma)
                            optionTickData.calculatedPrice = round(optionTickData.calculatedPrice,3)
                            # print(optionTickData.ownerPrice)
                            #发送数据给UI显示
                            # 先复制一份数据
                            newOptionTick = copy(optionTickData)
                            self.onOptionTick(newOptionTick)
        except:
            traceback.print_exc()

    def onOptionTick(self, optionTick):
        try:
            # 期权价格信息推送
            event1 = Event(type_=EVENT_OPTION_TICK)
            event1.dict_['data'] = optionTick
            self.eventEngine.put(event1)
        except:
            traceback.print_exc()

    def isMonitoredOption(self, code):
        try:
            if code in self.workingOptionDict:
                return True
            else:
                return False
        except:
            traceback.print_exc()

    def isMonitorOwnerCode(self, code):
        try:
            if code in self.ownerToOption:
                return True
            else:
                return False
        except:
            traceback.print_exc()

    # 模拟题环境不支持成交推送，只支持订单推送。 所以用订单推送来判断交易是否成功
    def processOrder(self, event):
        try:
            order = event.dict_['data']
            print("processOrder: %s: %s  %s  %s  %s  %s" % (order.symbol, order.vtOrderID, order.price, order.orderTime, order.status, order.direction))
        except:
            traceback.print_exc()

    def processDeal(self, event):
        try:
            deal = event.dict_['data']
            print("processDeal: %s: %s  %s  %s  %s  %s" % (deal.symbol, deal.tradeID, deal.orderID, deal.price, deal.direction, deal.tradeTime))
        except:
            traceback.print_exc()

    def processPositionEvent(self, event):
        try:
            position = event.dict_['data']
            symbol = position.symbol
            # 期权的仓位信息
            if self.isMonitoredOption(symbol):
                # 当已经产生了optiontick才把仓位信息填入，否则不处理
                # optiontick信息是在第一次处理option的报价信息时生成的
                if symbol in self.optionTick:
                    optionTickData = self.optionTick[symbol]
                    # 仓位有变化再更新
                    if optionTickData.position != position.position or optionTickData.costPrice != position.price:
                        optionTickData.position = position.position
                        optionTickData.costPrice = position.price
                        # 发送数据给UI显示，先复制一份数据
                        newOptionTick = copy(optionTickData)
                        self.onOptionTick(newOptionTick)
        except:
            traceback.print_exc()

    def sendOrder(self, symbol, orderType, price, volume):
        try:
            req = VtOrderReq()
            req.symbol = symbol
            req.vtSymbol = symbol
            req.price = price
            req.volume = volume
            req.priceType = PRICETYPE_LIMITPRICE

            gatewayName = "FUTU"

            req.direction = orderType
            orderID = self.mainEngine.sendOrder(req, gatewayName)

            if orderID:
                self.writeLog(u'委托成功 %s, %s，%s@%s %s' %(symbol,orderType,volume, price, orderID))
            else:
                self.writeLog(u'委托失败 %s, %s，%s@%s %s' %(symbol,orderType,volume, price, orderID))
            return orderID
        except:
            traceback.print_exc()


    def writeLog(self, content):
        try:
            """快速发出日志事件"""
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'OPTION_SPRITES_ENGINE'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()

    def getTradingDays(self, market, start, end):
        try:
            tradingDaysReq = VtTradingDaysReq()
            tradingDaysReq.market = market
            tradingDaysReq.startDate = start
            tradingDaysReq.endDate = end
            gatewayName = "FUTU"

            days = self.mainEngine.getTradingDays(tradingDaysReq, gatewayName)
            return days
        except:
            traceback.print_exc()