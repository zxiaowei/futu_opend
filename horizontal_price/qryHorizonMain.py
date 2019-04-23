# encoding: utf-8

import pandas as pd
from futuquant import *

horizontalFragmentDict = {}
mergeFragList = []

horizonDef = {'thres':0.10,
              'upBreakAllowedTimes':1,
              'downBreakAllowedTimes':1,
              'upBreakAllowedDays':3,
              'downBreakAllowedDays':3,
              'minHorizonDays': 20}

class HorizontalFragment:

    def __init__(self, date, price):
        self.startDate = date
        self.endDate = date
        self.archorPrice = price

        self.avgVolume = 0
        self.avgPrive = 0
        self.highestPrice = 0
        self.lowPrice = 0

        self.upBreakTimes = 0
        self.upBreakDays = 0
        self.tempUpBreakList = []
        self.upBreakList = []       # [[day1,day2], [dayx,dayy]]
        self.downBreakDays = 0
        self.downBreakTimes = 0
        self.tempDownBreakList = []
        self.downBreakList = []

        self.keepDays = 0
        self.broken = False

        self.merged = False

    def handleNewKline(self, kline):

        # 如果已经打破了横盘标准，则不要再进一步判断了
        if self.broken:
            return

        newPrice = kline['close']
        changedPct = round((newPrice - self.archorPrice) / self.archorPrice, 2)
        day = kline['time_key'][0:10]
        # 判断价格波动是否连续超出允许范围
        if abs(changedPct) > horizonDef['thres']:
            if (changedPct > 0):
                self.upBreakDays = self.upBreakDays + 1
                self.tempUpBreakList.append([day, changedPct])
            else:
                self.downBreakDays = self.downBreakDays + 1
                self.tempDownBreakList.append([day, changedPct])


            # 超出范围的情况打破了横盘标准, 设置打破标志
            if self.upBreakDays >= horizonDef['upBreakAllowedDays'] :
                self.upBreakList.append(self.tempUpBreakList)
                self.upBreakTimes += 1
            elif self.downBreakDays >= horizonDef['downBreakAllowedDays']:
                self.downBreakList.append(self.tempDownBreakList)
                self.downBreakTimes += 1

            if self.upBreakTimes >= horizonDef['upBreakAllowedTimes'] \
                or self.downBreakTimes >= horizonDef['downBreakAllowedTimes'] :
                self.broken = True

        else:

            # 清除价格超限标志
            self.upBreakDays = 0
            self.downBreakDays = 0
            self.tempUpBreakList = []
            self.tempDownBreakList =[]

            self.endDate = day

        if not self.broken:
            self.keepDays = self.keepDays + 1

    def isQualified(self):
        if not self.broken or self.keepDays > horizonDef['minHorizonDays']:
            return True
        else:
            return False


class FutuAPI():
    def __init__(self):
        self.quote_ctx = None

    def open(self):
        # connect to futu api
        if  not self.quote_ctx:
            self.quote_ctx = OpenQuoteContext(host='10.0.0.2', port=22221)
            SysConfig.set_all_thread_daemon(True)

    def close(self):
        if self.quote_ctx:
            self.quote_ctx.close()
            self.quote_ctx = None

    def getDayKlines(self, stockCode, startDate, endDate):
        ret, klineDF, key = self.quote_ctx.request_history_kline(stockCode, startDate, endDate, "K_DAY")
        return klineDF


    def getTradingDays(self, startDate, endDate):
        ret, days = self.quote_ctx.get_trading_days("SH",startDate, endDate)
        return days

def loadStockList():
    # return ['SZ.002387']
    return ['SZ.300268']
    # return ['SH.000001']

def checkKeepingHorizon(kline):

    newPrice = kline['close']
    newVolume = kline['volume']

    for day in horizontalFragmentDict.keys():
        hFrag = horizontalFragmentDict[day]
        hFrag.handleNewKline(kline)

    day = kline['time_key'][0:10]
    closePrice = kline['close']
    horizontalFragmentDict[day] = HorizontalFragment(day, closePrice)


def mergeHorizontalFragment():
    baseFrag = None
    for day in horizontalFragmentDict.keys():

        frag = horizontalFragmentDict[day]
        if not frag.isQualified():
            continue
        # 没有基础片段，选择作为基础片段
        if not baseFrag:
            baseFrag = frag
            continue
        # 作为下一个片段判断是否需要merge
        nextFrag = frag

        # 如果nextFrag 完全被 baseFrag 包括，丢弃nextFrag
        if baseFrag.startDate <= nextFrag.startDate\
            and baseFrag.endDate >= nextFrag.endDate :
            # 全包含关系不需要合并BreakList
            continue
        # 如果nextFrag与baseFrag有重叠合并，扩展日期
        if baseFrag.startDate <= nextFrag.startDate \
            and baseFrag.endDate >= nextFrag.startDate\
            and baseFrag.endDate <= nextFrag.endDate :
            baseFrag.endDate = nextFrag.endDate
            if len(nextFrag.upBreakList) > 0:
                baseFrag.upBreakList.extend(nextFrag.upBreakList)
            if len(nextFrag.downBreakList) > 0:
                baseFrag.downBreakList.extend(nextFrag.downBreakList)

            continue

        # 如果没有重合则开启一个新的baseFrag
        if baseFrag.endDate < nextFrag.startDate:
            mergeFragList.append(baseFrag)
            baseFrag.merged = True
            baseFrag = nextFrag

    mergeFragList.append(baseFrag)

def printHorizontalFragment():
    for day in horizontalFragmentDict.keys():
        hFrag = horizontalFragmentDict[day]
        if hFrag.isQualified():
            print("-- %s -> %s -- %s ----%s" %(hFrag.startDate, hFrag.endDate, hFrag.upBreakList, hFrag.downBreakList))

def printMergedFragment():
    for frag in mergeFragList:
        print("-- %s -> %s -- %s ----%s" %(frag.startDate, frag.endDate, frag.upBreakList, frag.downBreakList))

def main():


    futuApi = FutuAPI()
    futuApi.open()

    startDate = '2017-10-23'
    endDate = '2019-03-05'

    stockList = loadStockList()
    tradingDayList = futuApi.getTradingDays(startDate, endDate)

    # reset date range to trading day
    if len(tradingDayList) > 0:
        startDate = tradingDayList[0]
        endDate = tradingDayList[-1]
    else:
        futuApi.close()
        exit(-1)


    for stockCode in stockList:
        dayKlineDF = futuApi.getDayKlines(stockCode,startDate, endDate)
        for day in tradingDayList:
            # print(day)
            time_key = day + " 00:00:00"
            kline = dayKlineDF[dayKlineDF['time_key'] == time_key]
            # 交易日没有k线， 可能是交易日定义错误了。跳过接着处理
            if len(kline) == 0:
                continue
            kline = kline.iloc[0]
            checkKeepingHorizon(kline)

    mergeHorizontalFragment()
    # printHorizontalFragment()
    printMergedFragment()

    futuApi.close()


if __name__ == "__main__":
    main()