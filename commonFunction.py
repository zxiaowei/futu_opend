# encoding: UTF-8

import pytz
from datetime import datetime
from constant import  *
DAYLIGHT_ENABLE = False

import re
OPTION_TYPE_PUT = "PUT"
OPTION_TYPE_CALL = "CALL"

from math import log,sqrt,exp
from scipy import stats
RISK_FREE_RATE = 0.0228

from qtpy import QtWidgets

import traceback

from futuquant.common.constant import Market

#############################################################################
def getStockTimezone(symbol):
    if symbol[0:2] == "US":
        if DAYLIGHT_ENABLE:
            tz = pytz.timezone("EST5EDT")
        else:
            tz = pytz.timezone("EST")
    else:
        tz = pytz.timezone('Asia/Shanghai')
    return tz
#############################################################################
def getDatetimeOfSymbolTimezone(symbol):
    tz = getStockTimezone(symbol)
    dt = datetime.now(tz)
    return dt
#############################################################################
def getMarketCloseTimeBySymbol(symbol):
    if symbol[0:2] == "US":
        t = MARKET_CLOSE_TIME_US
    elif symbol[0:2] == "HK":
        t = MARKET_CLOSE_TIME_HK
    else:
        t = MARKET_CLOSE_TIME_CN

    return t
#############################################################################
# 时间time字符串相减，返回差的秒数
def timeStrSub(timeStr1, timeStr2):
    t1 = datetime.strptime(timeStr1, "%H:%M:%S")
    t2 = datetime.strptime(timeStr2, "%H:%M:%S")
    timeDetal = t1 - t2
    spanSeconds = timeDetal.total_seconds()
    return spanSeconds

# 时间date字符串相减，返回差的秒数
def dateStrSub(dateStr1, dateStr2):
    d1 = datetime.strptime(dateStr1, "%Y-%m-%d")
    d2 = datetime.strptime(dateStr2, "%Y-%m-%d")
    dateDetal = d1 - d2
    spanDays = dateDetal.days
    return spanDays
#############################################################################
# 解析期权编号,不是期权返回""
def parseOptionCode(optionCode):
    matchObj = re.search(r'(.*)\.(.*)([0-9]{6})([CP])([0-9]+)', optionCode)
    if matchObj:
        market = matchObj.group(1)
        ownerCode = matchObj.group(2)
        fullOwnerCode = market + '.' + ownerCode
        strikeDate = matchObj.group(3)
        strikeDate = "20" + strikeDate[0:2] + "-" + strikeDate[2:4] + "-" + strikeDate[4:]
        optionType = matchObj.group(4)
        if optionType == "P":
            optionType = OPTION_TYPE_PUT
        elif optionType == "C":
            optionType = OPTION_TYPE_CALL
        strikePrice = matchObj.group(5)
        strikePrice = str(float(strikePrice)/1000)
        return{ "OptionCode":optionCode, "OwnerCode":fullOwnerCode,
                "StrikeDate":strikeDate, "Type":optionType, "StrikePrice":strikePrice }
    else:
        return ""
########################################################################################
def getMarketBySymbol(symbol):
    try:
        if symbol[0:2] == "US":
            market = Market.US
        elif symbol[0:2] == "HK":
            market = Market.HK
        elif symbol[0:2] == "SH":
            market = Market.SH
        elif  symbol[0:2] == "SZ":
            market = Market.SZ
        else:
            raise Exception("Not Support Market %s" %symbol)
        return market
    except:
        traceback.print_exc()

#############################################################################
# BSM 期权价格计算
# S0: 正股价， K：行权价， T：到期剩余， r: 无风险利率， sigma： 隐含波动率
def bsm_call_value(S0,K,T,r,sigma):
    S0 = float(S0)
    d1 = (log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = (log(S0 / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    value = (S0 * stats.norm.cdf(d1,0.0,1.0) - K * exp(-r * T) * stats.norm.cdf(d2,0.0,1.0))
    return value

def bsm_put_value(S0,K,T,r,sigma):
    S0 = float(S0)
    d1 = (log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = (log(S0 / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    value = (S0 * (stats.norm.cdf(d1,0.0,1.0)-1) - K * exp(-r * T) * (stats.norm.cdf(d2,0.0,1.0)-1))
    return value

#############################################################################


class GroupBoxWithSinglWidget(QtWidgets.QGroupBox):

    # ----------------------------------------------------------------------
    def __init__(self, widget, title, parent=None):
        """Constructor"""
        super(GroupBoxWithSinglWidget, self).__init__(parent)

        self.setTitle(title)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(widget)
        self.setLayout(vbox)



if __name__ == '__main__':

    # print(getDatetimeOfSymbolTimezone("US.BABA"))
    # print(getDatetimeOfSymbolTimezone("HK.00700"))
    #
    print(timeStrSub("10:02:01","10:01:05"))

    print(parseOptionCode("US.AAPL181130P15003"))

    print(dateStrSub("2018-11-20", "2018-11-08"))