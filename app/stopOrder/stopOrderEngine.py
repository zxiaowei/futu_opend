# encoding: utf-8

from vnpy.trader.app import AppEngine
import json
from vnpy.trader.vtObject import VtLogData, VtSubscribeReq, VtOrderReq, VtOrderBookReq
from vnpy.event.eventEngine import Event
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_TICK, EVENT_ORDER, EVENT_TRADE
from vnpy.trader.vtFunction import getJsonPath
from constant import *
from vnpy.trader.language.chinese.constant import *
from futuquant.common.constant import *
from qssBasic import EVENT_STRATEGY_STOP_ORDER_STATUS, VtStrategyStopOrderStatus
from commonFunction import getDatetimeOfSymbolTimezone
from .strategyStopOrder import StopOrderStrategy

import traceback

# CTA引擎中涉及到的交易方向类型
CTAORDER_BUY = u'买开'
CTAORDER_SELL = u'卖平'

class StopOrderEngine(AppEngine):
    def __init__(self, mainEngine, eventEngine):
        try:
            self.mainEngine = mainEngine
            self.eventEngine = eventEngine

            self.configFileName = 'stop_order_config_00700.json'
            self.configFile = getJsonPath(self.configFileName, __file__)
            self.config = {}

            self.strategyDict = {}
            self.symbolStrategyDict = {}
            # 保存strategy历史 setting, 用来重启strategy时使用。 只根据strategyID保留最新的setting
            self.strategyHisSettingDict = {}

            self.orderStrategyDict = {}

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

    def writeLog(self, content):
        try:
            """快速发出日志事件"""
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'STOP_ORDER_ENGINE'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()

    def registerEvent(self):
        try:
            self.eventEngine.register(EVENT_TICK, self.processTick)
            self.eventEngine.register(EVENT_ORDER, self.processOrder)
            self.eventEngine.register(EVENT_TRADE, self.processDeal)
        except:
            traceback.print_exc()

    def checkIfStrategyComplete(self,stra):
        try:
            # 订单完成，UI取消策略，已挂订单取消, 下单失败 4种情况下结束策略运行
            if stra.statusNeedComplete():
                # 清除字典
                del self.strategyDict[stra.strategyID]
                # 清除 symbol 对应的list
                for symbol in stra.getSymbolList():
                    straList = self.symbolStrategyDict[symbol]
                    straList.remove(stra)

                # 把strategy加入到历史列表中，供重新启动策略使用
                self.strategyHisSettingDict[stra.strategyID] = stra.setting

                # 通知UI 策略完成
                self.updateUI(stra)

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
                # working和已经挂单状态需要持续的接收 tick
                if stra.statusAllowTickIn():
                    stra.onTick(tick)
                    self.updateUI(stra)

                self.checkIfStrategyComplete(stra)
        except:
            traceback.print_exc()

    def updateUI(self,stra):
        try:
            event1 = Event(type_= EVENT_STRATEGY_STOP_ORDER_STATUS)

            straStatus = VtStrategyStopOrderStatus()
            event1.dict_['data'] = straStatus

            straStatus.strategyID = stra.strategyID
            straStatus.status = stra.status
            if stra.thresholdPriceEnabled:
                # 已经获取了真实的threshold值，则显示真实数值
                if stra.realThresholdPrice:
                    straStatus.thresholdInfo = stra.startThresholdDirection + str(stra.realThresholdPrice)
                # 否则用用户输入代替显示信息
                else:
                    suffix = ""
                    if stra.thresholdIsPct:
                        suffix = u"百分比"
                    straStatus.thresholdInfo = stra.startThresholdDirection + suffix + str(stra.thresholdPrice)

                # 用V X标识价格是否已经冲破 threshold
                if stra.isThresholdPriceBroken:
                    straStatus.thresholdInfo = "V" + straStatus.thresholdInfo
                else:
                    straStatus.thresholdInfo = "X" + straStatus.thresholdInfo
            else:
                straStatus.thresholdInfo = "无限制"
            straStatus.ownerPrice = stra.getOwnerPrice()
            straStatus.ownerMaxMinPrice = stra.getOwnerMaxMinPrice()
            straStatus.triggerPrice = stra.getTriggerPrice()
            straStatus.crossDirection = stra.crossDirection
            straStatus.tradeDirection = stra.tradeDirection
            straStatus.volume = stra.volume
            straStatus.orderVolume =stra.volume


            self.eventEngine.put(event1)
        except:
            traceback.print_exc()

    # 模拟题环境不支持成交推送，只支持订单推送。 所以用订单推送来判断交易是否成功
    def processOrder(self, event):
        try:
            order = event.dict_['data']
            print("processOrder: %s: %s  %s  %s  %s  %s" % (order.symbol, order.vtOrderID, order.price, order.orderTime, order.status, order.direction))

            # 需要使用vtOrderID来匹配， sendorder的时候返回的是vtOrderID
            orderID = order.vtOrderID
            if orderID in self.orderStrategyDict:
                stra = self.orderStrategyDict[orderID]
                # 全部成交
                if order.status == STATUS_ALLTRADED:
                    # todo
                    # 策略完成状态改变，不应该在此处，应该挪到策略里面
                    # 此处应该只通知策略某个order已经全部成交了
                    stra.removeWorkingOrder(orderID)
                    stra.status = STRATEGY_STATUS_COMPLETE
                # 订单撤销
                elif order.status == STATUS_CANCELLED:
                    stra.removeWorkingOrder(orderID)
                    stra.status = STRATEGY_STATUS_ORDER_CANCELLED
        except:
            traceback.print_exc()

    def processDeal(self, event):
        try:
            deal = event.dict_['data']
            print("processDeal: %s: %s  %s  %s  %s  %s" % (deal.symbol, deal.tradeID, deal.orderID, deal.price, deal.direction, deal.tradeTime))
        except:
            traceback.print_exc()


    def subscribeForStrategy(self, stra):
        try:
            stockCodeList = stra.getSymbolList()
            for stockCode in stockCodeList:
                req = VtSubscribeReq()
                req.symbol = stockCode
                self.mainEngine.subscribe(req, 'FUTU')
        except:
            traceback.print_exc()

    def addStrategy(self, straConfig):
        try:
            # 生成策略实例
            stra = StopOrderStrategy(self, straConfig)
            # 根据策略ID检查是否有重复的策略
            straID = stra.strategyID
            if straID not in self.strategyDict:
                self.strategyDict[straID] = stra
            else:
                return -1, u"策略[" + straID + u"]已经存在，不能重复启动"

            # 建立stockCode与策略的对应关系， 一个stockCode可以对应多个策略，一个策略也可以关注多个stockCdoe
            symbolList = stra.getSymbolList()
            for symbol in symbolList:
                if symbol in self.symbolStrategyDict:
                    straList = self.symbolStrategyDict[symbol]
                else:
                    straList = []
                    self.symbolStrategyDict[symbol] = straList
                straList.append(stra)

            # 启动策略
            stra.start()
            # 订阅行情
            self.subscribeForStrategy(stra)

            # 第一次添加策略，通知UI更新
            self.updateUI(stra)

            self.writeLog(u"成功添加策略[" + straID + u"]")

            return 0, ""
        except:
            traceback.print_exc()


    def cancelOrRestartStrategy(self, strategyID):
        # 获取strategy 实例
        strategyExist = True
        try:
            stra = self.strategyDict[strategyID]
        except:
            strategyExist = False

        try:
            # 策略存在取消策略
            if strategyExist:
                self.cancelStrategy(strategyID)
            # 策略不存在重新启动策略
            else:
                self.restartStrategy(strategyID)
        except:
            traceback.print_exc()

    def restartStrategy(self, strategyID):
        try:
            setting = self.strategyHisSettingDict[strategyID]
        except:
            self.writeLog(u"未查询到策略历史，无法重启策略:" + strategyID )
            return

        try:
            self.writeLog(u"重启策略[" + strategyID + u"]")
            # 重新生成策略 添加到Engine
            retCode, reason = self.addStrategy(setting)
            if retCode:
                self.writeLog(reason)
                return
        except:
            traceback.print_exc()

    def cancelStrategy(self, strategyID):
        # 获取strategy 实例
        try:
            stra = self.strategyDict[strategyID]
        except:
            self.writeLog(u"策略[" + strategyID + u"]不存在")
            return

        try:
            # 只取消正在运行中的strategy
            if stra.statusAllowCancellation() :
                # 只进行状态修改， 在下一次收到tick时，依靠checkIfStrategyComplete来更新UI清理数据。
                stra.status = STRATEGY_STATUS_CANCEL
                self.writeLog(u"取消策略[" + strategyID + u"]")
            else:
                self.writeLog(u"策略[" + strategyID + u"]不在运行状态不需要取消")
        except:
            traceback.print_exc()



    def sendOrder(self, symbol, orderType, price, volume, strategy):
        try:
            req = VtOrderReq()
            req.symbol = symbol
            req.vtSymbol = symbol
            req.price = price
            req.volume = volume
            req.priceType = PRICETYPE_LIMITPRICE

            gatewayName = "FUTU"

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
                self.orderStrategyDict[VtOrderID] = strategy  # 保存order和策略的映射关系
                self.strategyDict[strategy.strategyID].addOrder(VtOrderID)  # 添加到策略委托号集合中

                self.writeLog(u'策略%s发送委托成功，%s，%s，%s@%s'
                                 %(strategy.strategyID, symbol, req.direction, volume, price))
            else:
                self.writeLog(u"策略%s发送委托失败，%s，%s，%s@%s"
                                 %(strategy.strategyID, symbol, req.direction, volume, price))

            return VtOrderID
        except:
            traceback.print_exc()

    def getOrderBook(self,symbol,strategy):
        try:
            req = VtOrderBookReq()
            req.symbol = symbol
            gatewayName = "FUTU"

            orderBookDict = self.mainEngine.getOrderBook(req, gatewayName)
            # self.writeLog(u'请求%s摆盘信息' %(symbol))

            return orderBookDict
        except:
            traceback.print_exc()

    def getTodayStr(self,symbol):
        try:
            dt = getDatetimeOfSymbolTimezone(symbol)
            return dt.strftime("%Y%m%d")
        except:
            traceback.print_exc()
