# encoding: utf-8

import traceback
from vnpy.trader.app import AppEngine
import json
from vnpy.trader.vtObject import VtLogData, VtOptionChainReq, VtMarketSnapshotReq
from vnpy.trader.vtFunction import getJsonPath
from vnpy.trader.vtEvent import  EVENT_LOG
from vnpy.event.eventEngine import Event


class OptionSelectorEngine(AppEngine):

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


    def qryOptionList(self, stockCode, startDate, endDate):
        try:
            optionReq = VtOptionChainReq()
            optionReq.symbol= stockCode
            optionReq.startDate = startDate
            optionReq.endDate = endDate
            gateway = 'FUTU'

            retCode, df1 = self.mainEngine.getOptionChain(optionReq, gateway)
            if retCode:
                return

            codeList = list(df1['code'])

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
            return None
