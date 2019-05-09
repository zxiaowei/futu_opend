# encoding: UTF-8

from threading import Thread
from time import sleep
import json
import requests

from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.language.chinese.constant import *

import pandas as pd

import traceback

directionMap = {}
directionMap[DIRECTION_LONG] = "BUY"
directionMap[DIRECTION_SHORT] = "SELL"


########################################################################
class TradeDllAShareGateway(VtGateway):
    """A股Web服务接口"""
    INVALID_CLIENT_ID = -1

    # ----------------------------------------------------------------------
    def __init__(self, eventEngine, gatewayName='TradeDllAShare'):
        """Constructor"""
        super(TradeDllAShareGateway, self).__init__(eventEngine, gatewayName)

        self.ipPort = None
        self.markets = []
        self.accountId = None
        self.env = 1  # 默认仿真交易
        self.clientId = self.INVALID_CLIENT_ID

        self.fileName = self.gatewayName + '_connect.json'
        self.filePath = getJsonPath(self.fileName, __file__)

        self.tickDict = {}
        self.tradeSet = set()  # 保存成交编号的集合，防止重复推送

        self.qryEnabled = True
        self.qryThread = Thread(target=self.qryData)

    # ----------------------------------------------------------------------
    def writeLog(self, content):
        """输出日志"""
        log = VtLogData()
        log.gatewayName = self.gatewayName
        log.logContent = content
        self.onLog(log)

    # ----------------------------------------------------------------------
    def writeError(self, code, msg):
        """输出错误"""
        error = VtErrorData()
        error.gatewayName = self.gatewayName
        error.errorID = code
        error.errorMsg = msg
        self.onError(error)

    # ----------------------------------------------------------------------
    def connect(self):
        """连接"""
        if self.clientId != self.INVALID_CLIENT_ID:
            self.writeLog(u'已经连接TradeDllA股交易服务，请勿重复连接')
            return

        # 载入配置
        try:
            f = open(self.filePath)
            setting = json.load(f)
            self.ipPort = setting['ipPort']
            self.markets = setting['market'].split(',')
            self.env = setting['env']
            self.accountId = setting['accountId']
        except:
            self.writeLog(u'载入配置文件出错')
            return

        try:
            # 发送连接请求
            url = self.ipPort + "/connect"
            header = {"accept": "application/json", "Content-Type": "application/json"}
            resp = requests.post(url, headers=header, json={"accountId": self.accountId})

            respJson = json.loads(resp.text)
            if respJson["rc"] == 0:
                self.clientId = respJson["clientId"]
                self.writeLog(u"AccountId[%s] ClientId[%s] 成功连接TradeDllA股交易服务"%(self.accountId, self.clientId))
            print(resp.text)

            self.qryThread.start()

            return
        except:
            self.writeLog(u"连接TradeDllA股交易服务出错")
            return

    # ----------------------------------------------------------------------
    def qryData(self):
        """初始化时查询数据"""

        # 查询合约、成交、委托、持仓、账户
        # self.qryTrade()
        # self.qryOrder()
        # self.qryPosition()
        # self.qryAccount()

        # 启动循环查询
        # self.initQuery()
        pass

    # ----------------------------------------------------------------------
    def connectTrade(self):
        """连接交易功能"""
        # 连接交易接口
        self.writeLog(u'交易接口连接成功')

    # ----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        try:
            symbol = orderReq.symbol[3:]
            volume = orderReq.volume
            price = orderReq.price
            tradeDirection = directionMap[orderReq.direction]
            self.writeLog(u"下单[%s] symbol[%s] price[%s] volume[%s]" % (tradeDirection, symbol, price, volume))

            url = self.ipPort + "/sendorder"
            header = {"accept": "application/json", "Content-Type": "application/json"}
            resp = requests.post(url, headers=header,
                                 json={"accountId": self.accountId, "symbol": symbol, "volume": volume,
                                       "price": price, "tradeDirection": tradeDirection})
            respJson = json.loads(resp.text)
            print(respJson)
            rc = respJson["rc"]
            if rc == 0:
                vtOrderID = '.'.join([self.gatewayName, respJson["orderId"]])
            else:
                self.writeError(rc, u'委托失败：%s' % respJson["errMessage"])
                self.writeLog(u'委托失败：%s' % respJson["errMessage"])
                vtOrderID = ""
        except:
            self.writeLog(u"委托异常")
            vtOrderID = ""

        return vtOrderID

    # ----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        try:
            orderId = cancelOrderReq.orderID
            realOrderId = orderId.split('.')[-1]
            symbol = cancelOrderReq.symbol

            url = self.ipPort + "/cancelorder"
            header = {"accept": "application/json", "Content-Type": "application/json"}
            resp = requests.post(url, headers=header, json={"accountId": self.accountId,  "orderId": realOrderId,
                                                            "symbol":symbol})
            respJson = json.loads(resp.text)
            print(respJson)

            rc = respJson["rc"]
            if rc != 0:
                self.writeError(rc, u'委托失败：%s' % respJson["errMessage"])
                self.writeLog(u'委托失败：%s' % respJson["errMessage"])
        except:
            self.writeLog(u"撤单异常")

        return rc


    # ----------------------------------------------------------------------
    def qryContract(self):
        """查询合约"""
        pass
        # self.writeLog(u'合约信息查询成功')

    # ----------------------------------------------------------------------
    def qryAccountSync(self):
        """查询账户资金"""
        try:
            accountDf = pd.DataFrame()
            url = self.ipPort + "/account"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId})
            respJson = json.loads(resp.text)

            rc = respJson["rc"]
            if rc == 0:
                accountDf= pd.read_json(respJson["accountDf"])
                self.writeLog(u'%s账户资金查询成功' % self.gatewayName)
            else:
                self.writeError(rc, u'账户资金查询失败：%s' % respJson["errMessage"])
                self.writeLog(u'账户资金查询失败：%s' % respJson["errMessage"])
            return accountDf
        except:
            traceback.print_exc()
            return accountDf

    # ----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户资金"""
        try:
            url = self.ipPort + "/account"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId})
            respJson = json.loads(resp.text)

            rc = respJson["rc"]
            if rc == 0:
                accountDf = pd.read_json(respJson["accountDf"])

                for ix, row in accountDf.iterrows():
                    account = VtAccountData()
                    account.gatewayName = self.gatewayName
                    account.accountID = u"东北证券_" + self.accountId
                    account.vtAccountID = '.'.join([self.gatewayName, account.accountID])
                    account.balance = float(row['totalAsset'])
                    account.available = float(row['avaMoney'])

                    self.onAccount(account)
                self.writeLog(u'%s账户资金查询成功' % self.gatewayName)
            else:
                self.writeError(rc, u'账户资金查询失败：%s' % respJson["errMessage"])
                self.writeLog(u'账户资金查询失败：%s' % respJson["errMessage"])
        except:
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def qryPositionSync(self):
        """同步查询持仓"""
        try:
            df = pd.DataFrame()
            url = self.ipPort + "/position"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId})
            df = pd.read_json(resp.text, dtype={"symbol": "str"})
            self.writeLog(u'%s持仓查询成功' % self.gatewayName)
            return df
        except:
            traceback.print_exc()
            return df
    # ----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        try:
            url = self.ipPort + "/position"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId})
            df = pd.read_json(resp.text, dtype={"symbol": "str"})
            print(df)

            for ix, row in df.iterrows():
                pos = VtPositionData()
                pos.gatewayName = self.gatewayName

                pos.symbol = self.getFullSymbolName(row['symbol'])
                pos.vtSymbol = pos.symbol

                pos.direction = DIRECTION_LONG
                pos.vtPositionName = '.'.join([pos.vtSymbol, pos.direction])

                pos.position = int(row['totalVol'])
                pos.price = float(row['currentPrice'])
                pos.positionProfit = float(row['profit'])
                pos.frozen = int(row['totalVol']) - int(row['canSellVol'])

                if pos.price < 0: pos.price = 0
                if pos.positionProfit > 100000000: pos.positionProfit = 0

                self.onPosition(pos)

            self.writeLog(u'%s持仓查询成功' % self.gatewayName)
        except:
            traceback.print_exc()

    # add prefix SH. SZ. for symbol
    def getFullSymbolName(self,symbol):
        if symbol[0] == '6':
            return "SH."+symbol
        else:
            return "SZ."+symbol
    # ----------------------------------------------------------------------
    def qryOrder(self):
        """查询委托"""
        try:
            url = self.ipPort + "/queryOrder"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId})
            respJson = json.loads(resp.text)

            rc = respJson["rc"]
            if rc == 0:
                orderDf= pd.read_json(respJson["orderDf"],dtype={"symbol": "str", "orderId":"str"})
                self.processOrder(orderDf)
                self.writeLog(u'%s当日下单查询成功' % self.gatewayName)
            else:
                self.writeError(rc, u'当日下单查询失败：%s' % respJson["errMessage"])
                self.writeLog(u'当日下单查询失败：%s' % respJson["errMessage"])
        except:
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def qryTradeSync(self):
        """同步查询成交"""
        try:
            url = self.ipPort + "/queryTrade"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId, "ignoreApply":True})
            respJson = json.loads(resp.text)

            rc = respJson["rc"]
            if rc == 0:
                tradeDf= pd.read_json(respJson["tradeDf"],dtype={"symbol": "str", "tradeId":"str", "orderId":"str"})
                self.writeLog(u'%s当日成交查询成功' % self.gatewayName)
                return tradeDf
            else:
                self.writeError(rc, u'当日成交查询失败：%s' % respJson["errMessage"])
                self.writeLog(u'当日成交查询失败：%s' % respJson["errMessage"])
                return pd.DataFrame()
        except:
            traceback.print_exc()
            return pd.DataFrame()

    def qryTrade(self):
        """查询成交"""
        try:
            url = self.ipPort + "/queryTrade"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId, "ignoreApply":True})
            respJson = json.loads(resp.text)

            rc = respJson["rc"]
            if rc == 0:
                tradeDf= pd.read_json(respJson["tradeDf"],dtype={"symbol": "str", "tradeId":"str", "orderId":"str"})
                self.processDeal(tradeDf)
                self.writeLog(u'%s当日成交查询成功' % self.gatewayName)
            else:
                self.writeError(rc, u'当日成交查询失败：%s' % respJson["errMessage"])
                self.writeLog(u'当日成交查询失败：%s' % respJson["errMessage"])
        except:
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def qryHistoryTradeSync(self,req):
        """查询历史成交"""
        try:
            tradeDf = pd.DataFrame()

            startDate = req.startDate
            endDate = req.endDate
            ignoreApply = req.ignoreApply

            url = self.ipPort + "/queryHistoryTrade"
            header = {"accept": "application/json", "Content-Type": "application/json"}

            resp = requests.post(url, headers=header, json={"accountId": self.accountId, "startDate":startDate,
                                                            "endDate":endDate, "ignoreApply":ignoreApply})
            respJson = json.loads(resp.text)

            rc = respJson["rc"]
            if rc == 0:
                tradeDf = pd.read_json(respJson["historyTradeDf"], dtype={"symbol": "str", "tradeId": "str", "orderId": "str"})
                self.writeLog(u'%s历史成交查询成功' % self.gatewayName)
            else:
                self.writeError(rc, u'历史成交查询失败：%s' % respJson["errMessage"])
                self.writeLog(u'历史成交查询失败：%s' % respJson["errMessage"])
            return tradeDf
        except:
            traceback.print_exc()
            return tradeDf

    # ----------------------------------------------------------------------
    def close(self):
        """关闭"""
    # ----------------------------------------------------------------------
    def initQuery(self):
        """初始化连续查询"""
        if self.qryEnabled:
            # 需要循环的查询函数列表
            self.qryFunctionList = [self.qryAccount, self.qryPosition]

            self.qryCount = 0  # 查询触发倒计时
            self.qryTrigger = 2  # 查询触发点
            self.qryNextFunction = 0  # 上次运行的查询函数索引

            self.startQuery()

    # ----------------------------------------------------------------------
    def query(self, event):
        """注册到事件处理引擎上的查询函数"""
        self.qryCount += 1

        if self.qryCount > self.qryTrigger:
            # 清空倒计时
            self.qryCount = 0

            # 执行查询函数
            function = self.qryFunctionList[self.qryNextFunction]
            function()

            # 计算下次查询函数的索引，如果超过了列表长度，则重新设为0
            self.qryNextFunction += 1
            if self.qryNextFunction == len(self.qryFunctionList):
                self.qryNextFunction = 0


    def processOrder(self, data):
        """处理委托推送"""
        for ix, row in data.iterrows():
            # 如果状态是已经删除，则直接忽略
            if row['orderType'] in [u"撤单"]:
                continue
            # print(row['order_status'])

            order = VtOrderData()
            order.gatewayName = self.gatewayName

            order.symbol = row['symbol']
            order.vtSymbol = order.symbol

            order.orderID = str(row['orderId'])
            order.vtOrderID = '.'.join([self.gatewayName, order.orderID])

            order.price = float(row['orderPrice'])
            order.totalVolume = float(row['orderVolume'])
            order.tradedVolume = float(row['tradeVolume'])
            order.orderTime = row['time']

            order.status = row['orderState']
            order.direction = row["flagName"]

            self.onOrder(order)

            # ----------------------------------------------------------------------

    def processDeal(self, data):
        """处理成交推送"""
        for ix, row in data.iterrows():
            tradeID = str(row['tradeId'])
            if tradeID in self.tradeSet:
                continue
            self.tradeSet.add(tradeID)

            trade = VtTradeData()
            trade.gatewayName = self.gatewayName

            trade.symbol = row['symbol']
            trade.vtSymbol = trade.symbol

            trade.tradeID = tradeID
            trade.vtTradeID = '.'.join([self.gatewayName, trade.tradeID])

            trade.orderID = row['orderId']
            trade.vtOrderID = '.'.join([self.gatewayName, trade.orderID])

            trade.price = float(row['tradePrice'])
            trade.volume = float(row['tradeVolume'])
            trade.direction = row['flagName']

            trade.tradeTime = row['time']

            self.onTrade(trade)


    def setQryEnabled(self, qryEnabled):
        """设置是否要启动循环查询"""
        self.qryEnabled = qryEnabled