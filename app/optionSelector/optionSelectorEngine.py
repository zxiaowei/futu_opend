# encoding: utf-8

import traceback
from vnpy.trader.app import AppEngine
import json
from vnpy.trader.vtObject import VtLogData, VtOptionChainReq, VtMarketSnapshotReq, VtHisKlineReq, VtTradingDaysReq
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.vtEvent import  EVENT_LOG
from vnpy.event.eventEngine import Event
from pandas import DataFrame
from datetime import datetime, timedelta
from commonFunction import getMarketBySymbol, getDatetimeOfSymbolTimezone

class OptionSelectorEngine(AppEngine):

    localKlineEnabled = False

    def __init__(self, mainEngine, eventEngine):
        try:
            self.mainEngine = mainEngine
            self.eventEngine = eventEngine

            self.configFileName = 'option_selector_config.json'
            self.configFile = getJsonPath(self.configFileName, __file__)

            self.optionDict = {}

        except:
            traceback.print_exc()


    def start(self):
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
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'OPTION_SELECTOR_ENGINE'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()


    def registerEvent(self):
        try:
            pass
        except:
            traceback.print_exc()

    def qryMarketSnapshot(self, code):
        try:
            snapshotReq = VtMarketSnapshotReq()
            snapshotReq.symbolList = code
            gateway = 'FUTU'
            retCode, df1 = self.mainEngine.getMarketSnapshot(snapshotReq, gateway)
            if retCode:
                return DataFrame()
            else:
                return df1

        except:
            traceback.print_exc()

#
    def calSTD(self, code, numOfDays=15):
        try:
            # 获取指定范围的日期
            dtToday = getDatetimeOfSymbolTimezone(code)
            dayEnd = dtToday - timedelta(days=1)
            dayEndStr = dayEnd.strftime("%Y-%m-%d")
            dayYearAgo = dtToday - timedelta(days=365)
            tradingDaysReq = VtTradingDaysReq()
            tradingDaysReq.market = getMarketBySymbol(code)
            tradingDaysReq.startDate = dayYearAgo.strftime("%Y-%m-%d")
            tradingDaysReq.endDate = dayEndStr
            gatewayName = "FUTU"

            days = self.mainEngine.getTradingDays(tradingDaysReq, gatewayName)
            if len(days) > 0 :
                startDateStr = days[-numOfDays - 1]
            else:
                return -1
            # 查询numOfDays + 1 天之前的收盘价用于计算STD
            ret, klineDF = self.getHisKline(code, startDateStr, dayEndStr, "K_DAY")
            if ret == 0:
                dfVolatility = klineDF['close'].pct_change()[1:]
                stdValue = dfVolatility.std()
            else:
                stdValue = -1
            return stdValue
        except:
            traceback.print_exc()
            return -1

#--------------------------------------------------------------------------------
    def getHisKline(self, symbol, start, end, type):
        try:
            klineReq = VtHisKlineReq()
            klineReq.symbol = symbol
            klineReq.startDate = start
            klineReq.endDate = end
            klineReq.kType = type

            gateway = 'FUTU'

            ret = -1
            df = ""

            if self.localKlineEnabled:
                # 先尝试获取本地Kline
                ret, df = self.mainEngine.getHisKline(klineReq, gateway)
            # 如果本地没有Kline 尝试在线获取Kline
            if ret:
                ret, df = self.mainEngine.requestHisKline(klineReq, gateway)
                if ret:
                    self.writeLog(u"获取Kline失败: %s" %symbol)

            return ret, df
        except:
            traceback.print_exc()
            return -1, ""
#--------------------------------------------------------------------------------

    def qryOptionList(self, stockCode, startDate, endDate, lowPrice, highPrice, optType):
        try:

            dfOptChain = DataFrame()

            # getOptionChain最多接收一个月的日期范围，startDate-endDate范围过大需要分段处理
            dStart = datetime.strptime(startDate, "%Y-%m-%d")
            dEnd = datetime.strptime(endDate, "%Y-%m-%d")
            dParaStart = dStart
            # 每次最多查询30天的数据
            dParaEnd = dParaStart + timedelta(days=30)
            dEnd30 = dEnd + timedelta(days=30)
            while dParaEnd <= dEnd30:
                optionReq = VtOptionChainReq()
                optionReq.symbol= stockCode
                optionReq.startDate = dParaStart.strftime("%Y-%m-%d")
                if dParaEnd < dEnd:
                    optionReq.endDate = dParaEnd.strftime("%Y-%m-%d")
                else:
                    optionReq.endDate = dEnd.strftime("%Y-%m-%d")
                gateway = 'FUTU'

                retCode, df1 = self.mainEngine.getOptionChain(optionReq, gateway)
                if retCode:
                    return
                else:
                    dfOptChain = dfOptChain.append(df1)

                dParaStart = dParaEnd + timedelta(days=1)
                dParaEnd = dParaStart + timedelta(days=30)

            if len(dfOptChain) == 0:
                return

            # 排除掉不满足行权价的code， 减少输入getMarketSnapshot的code数量
            if lowPrice != 0:
                dfOptChain = dfOptChain[dfOptChain['strike_price'] >= lowPrice]
            if highPrice != 0:
                dfOptChain = dfOptChain[dfOptChain['strike_price'] <= highPrice]
            # 过滤期权类型
            if optType != "C&P":
                dfOptChain = dfOptChain[dfOptChain['option_type'] == optType ]

            codeList = list(dfOptChain['code'])

            snapshotReq = VtMarketSnapshotReq()
            snapshotReq.symbolList = codeList
            gateway = 'FUTU'
            retCode, df2 = self.mainEngine.getMarketSnapshot(snapshotReq, gateway)
            if retCode:
                return

            self.optionDict[stockCode] = df2

        except:
            traceback.print_exc()

    def getOptionDF(self, stockCode):
        if stockCode in self.optionDict:
            return self.optionDict[stockCode]
        else:
            return DataFrame()
