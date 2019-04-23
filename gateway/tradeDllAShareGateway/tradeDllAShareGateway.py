# encoding: UTF-8

from threading import Thread
from time import sleep
import json
import requests

from vnpy.trader.vtGateway import *
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.language.chinese.constant import *

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
            return
        except:
            self.writeLog(u"连接TradeDllA股交易服务出错")
            return

    # ----------------------------------------------------------------------
    def qryData(self):
        """初始化时查询数据"""
        # 等待2秒保证行情和交易接口启动完成
        sleep(2.0)

        # 查询合约、成交、委托、持仓、账户
        # self.qryContract()
        self.qryTrade()
        self.qryOrder()
        self.qryPosition()
        self.qryAccount()

        # 启动循环查询
        self.initQuery()

    # ----------------------------------------------------------------------
    def connectTrade(self):
        """连接交易功能"""
        # 连接交易接口
        self.writeLog(u'交易接口连接成功')

    # ----------------------------------------------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        try:
            symbol = orderReq.symbol
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
            self.writeLog(u"连接TradeDllA股交易服务出错")
            vtOrderID = ""

        return vtOrderID

    # ----------------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        return

    # ----------------------------------------------------------------------
    def qryContract(self):
        """查询合约"""
        self.writeLog(u'合约信息查询成功')

    # ----------------------------------------------------------------------
    def qryAccount(self):
        """查询账户资金"""
        code, data1 = self.tradeCtxHK.accinfo_query(trd_env=self.env, acc_id=0)
        if code:
            self.writeError(code, u'查询账户资金失败：%s' % data1)
            return

        for ix, row in data1.iterrows():
            account = VtAccountData()
            account.gatewayName = self.gatewayName

            account.accountID = '%s_%s' % (self.gatewayName, 'HK')
            account.vtAccountID = '.'.join([self.gatewayName, account.accountID])
            account.balance = float(row['total_assets'])
            account.available = float(row['avl_withdrawal_cash'])

            self.onAccount(account)

        code, data2 = self.tradeCtxUS.accinfo_query(trd_env=self.env, acc_id=0)
        if code:
            self.writeError(code, u'查询账户资金失败：%s' % data2)
            return

        for ix, row in data2.iterrows():
            account = VtAccountData()
            account.gatewayName = self.gatewayName

            account.accountID = '%s_%s' % (self.gatewayName, 'US')
            account.vtAccountID = '.'.join([self.gatewayName, account.accountID])
            account.balance = float(row['total_assets'])
            account.available = float(row['avl_withdrawal_cash'])

            self.onAccount(account)

        code, data3 = self.tradeCtxCN.accinfo_query(trd_env=self.env, acc_id=0)
        if code:
            self.writeError(code, u'查询账户资金失败：%s' % data3)
            return

        for ix, row in data3.iterrows():
            account = VtAccountData()
            account.gatewayName = self.gatewayName

            account.accountID = '%s_%s' % (self.gatewayName, 'CN')
            account.vtAccountID = '.'.join([self.gatewayName, account.accountID])
            account.balance = float(row['total_assets'])
            account.available = float(row['avl_withdrawal_cash'])

            self.onAccount(account)

    # ----------------------------------------------------------------------
    def qryPosition(self):
        """查询持仓"""
        code, data1 = self.tradeCtxHK.position_list_query(trd_env=self.env, acc_id=0)
        if code:
            self.writeError(code, u'查询持仓失败：%s' % data1)
            return

        code, data2 = self.tradeCtxUS.position_list_query(trd_env=self.env, acc_id=0)
        if code:
            self.writeError(code, u'查询持仓失败：%s' % data2)
            return

        code, data3 = self.tradeCtxCN.position_list_query(trd_env=self.env, acc_id=0)
        if code:
            self.writeError(code, u'查询持仓失败：%s' % data3)
            return

        data = data1.append(data2)
        data = data.append(data3)
        for ix, row in data.iterrows():
            pos = VtPositionData()
            pos.gatewayName = self.gatewayName

            pos.symbol = row['code']
            pos.vtSymbol = pos.symbol

            pos.direction = DIRECTION_LONG
            pos.vtPositionName = '.'.join([pos.vtSymbol, pos.direction])

            pos.position = float(row['qty'])
            pos.price = float(row['cost_price'])
            pos.positionProfit = float(row['pl_val'])
            pos.frozen = float(row['qty']) - float(row['can_sell_qty'])

            if pos.price < 0: pos.price = 0
            if pos.positionProfit > 100000000: pos.positionProfit = 0

            self.onPosition(pos)

    # ----------------------------------------------------------------------
    def qryOrder(self):
        """查询委托"""
        code, data1 = self.tradeCtxHK.order_list_query("", trd_env=self.env)
        if code:
            self.writeError(code, u'查询委托失败：%s' % data1)
            return

        code, data2 = self.tradeCtxUS.order_list_query("", trd_env=self.env)
        if code:
            self.writeError(code, u'查询委托失败：%s' % data2)
            return

        code, data3 = self.tradeCtxCN.order_list_query("", trd_env=self.env)
        if code:
            self.writeError(code, u'查询委托失败：%s' % data3)
            return

        data = data1.append(data2)
        data = data.append(data3)
        self.processOrder(data)
        self.writeLog(u'委托查询成功')

    # ----------------------------------------------------------------------
    def qryTrade(self):
        """查询成交"""
        code, data1 = self.tradeCtxHK.deal_list_query(self.env)
        if code:
            self.writeError(code, u'查询成交失败：%s' % data1)
            return

        code, data2 = self.tradeCtxUS.deal_list_query(self.env)
        if code:
            self.writeError(code, u'查询成交失败：%s' % data2)
            return

        code, data3 = self.tradeCtxCN.deal_list_query(self.env)
        if code:
            self.writeError(code, u'查询成交失败：%s' % data3)
            return

        data = data1.append(data2)
        data = data.append(data3)
        self.processDeal(data)
        self.writeLog(u'成交查询成功')

    # ----------------------------------------------------------------------

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
            if row['order_status'] == OrderStatus.DELETED:
                continue

            print(row['order_status'])
            order = VtOrderData()
            order.gatewayName = self.gatewayName

            order.symbol = row['code']
            order.vtSymbol = order.symbol

            order.orderID = str(row['order_id'])
            order.vtOrderID = '.'.join([self.gatewayName, order.orderID])

            order.price = float(row['price'])
            order.totalVolume = float(row['qty'])
            order.tradedVolume = float(row['dealt_qty'])
            order.orderTime = row['create_time'].split(' ')[-1]

            order.status = statusMapReverse.get(row['order_status'], STATUS_UNKNOWN)
            order.direction = directionMapReverse[row['trd_side']]

            self.onOrder(order)

            # ----------------------------------------------------------------------

    def processDeal(self, data):
        """处理成交推送"""
        for ix, row in data.iterrows():
            tradeID = str(row['deal_id'])
            if tradeID in self.tradeSet:
                continue
            self.tradeSet.add(tradeID)

            trade = VtTradeData()
            trade.gatewayName = self.gatewayName

            trade.symbol = row['code']
            trade.vtSymbol = trade.symbol

            trade.tradeID = tradeID
            trade.vtTradeID = '.'.join([self.gatewayName, trade.tradeID])

            trade.orderID = row['order_id']
            trade.vtOrderID = '.'.join([self.gatewayName, trade.orderID])

            trade.price = float(row['price'])
            trade.volume = float(row['qty'])
            trade.direction = directionMapReverse[row['trd_side']]

            trade.tradeTime = row['create_time'].split(' ')[-1]

            self.onTrade(trade)


    def setQryEnabled(self, qryEnabled):
        """设置是否要启动循环查询"""
        self.qryEnabled = qryEnabled