# encoding: utf-8


from qtpy import QtWidgets
from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QPushButton, QComboBox, QVBoxLayout,QHBoxLayout,QGroupBox
from vnpy.event.eventEngine import Event
from vnpy.trader.vtObject import VtLogData
from vnpy.trader.vtEvent import EVENT_LOG
from vnpy.trader.language.chinese.constant import *
from constant import (CROSS_DIRECTION_DOWN, CROSS_DIRECTION_UP,
                      TRADE_DIRECTION_BUY, TRADE_DIRECTION_SELL, TRADE_DIRECTION_BUY_THEN_SELL,
                      TRADE_DIRECTION_BUY_THEN_STOP,
                      ORDER_PRICE_ORDERBOOK, ORDER_PRICE_AVG_ORDERBOOK,STOP_ORDER_THRESHOLD_DIRECTION_GREATER,
                      STOP_ORDER_THRESHOLD_DIRECTION_LESS)

from vnpy.trader.uiBasicWidget import BasicMonitor, BasicCell, NumCell
from collections import OrderedDict
from qssBasic import EVENT_STRATEGY_CATCH_LIMITUP_STATUS
from vnpy.trader.uiQt import BASIC_FONT
from commonFunction import GroupBoxWithSinglWidget, parseOptionCode

import re
import sys
import traceback




class CatchLimitUpMainWindow(QtWidgets.QWidget):

    def __init__(self, catchLimitUpEngine, eventEngine, parent=None):
        super(CatchLimitUpMainWindow, self).__init__(parent)

        self.catchLimitUpEngine = catchLimitUpEngine
        self.eventEngine = eventEngine

        try:
            self.catchLimitUpEngine.start()
            self.initUi()
            self.registerEvent()
            self.forUT()
        except:
            traceback.print_exc()


    def forUT(self):
        pass

    def initUi(self):
        self.setWindowTitle(u"看板儿狗")

        # HBox layout for button
        hbox2 = QHBoxLayout()
        fixLenButton = 180
        space = 50
        btStart = QPushButton(u"启动策略")
        size = btStart.sizeHint()
        btStart.setMinimumHeight(size.height() * 2)
        btStopAll = QPushButton(u"停止全部策略")
        btStopAll.setMinimumHeight(size.height() * 2)
        hbox2.addWidget(btStart)
        # hbox2.addWidget(btStopAll)
        hbox2.addStretch()
        hbox2.setSpacing(space)
        btStart.setFixedWidth(fixLenButton)
        btStopAll.setFixedWidth(fixLenButton)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox2)

        # 策略状态组件
        self.strategyWidget = LimitUpPlateMonitor(self.catchLimitUpEngine, self.eventEngine)
        groupBoxStraMonitor = GroupBoxWithSinglWidget(self.strategyWidget, u"板块信息")
        vbox.addWidget(groupBoxStraMonitor)

        self.setLayout(vbox)

        btStart.clicked.connect(self.startStrategy)

    def registerEvent(self):
        # 暂不需要独立的log处理， log会显示在主窗口的“日志”窗口中
        # self.eventEngine.register(EVENT_LOG, self.processLogEvent)
        pass

    def processLogEvent(self, event):
        pass

    def writeLog(self, content):
        try:
            """快速发出日志事件"""
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'STOPORDER_MAIN_WINDOW'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()


    def verifyAndConvertInputParam(self, straConfig):
        try:
            pass

            return 0
        except:
            traceback.print_exc()
            return -1

    def startStrategy(self):
        try:
            print(u"In catchLimitUpMainWindow startStrategy")
            straConfig = {}
            straConfig['stockPoolFile'] = self.catchLimitUpEngine.config['stockPoolFile']

            # 添加策略到Engine
            retCode, reason = self.catchLimitUpEngine.addStrategy(straConfig)
            if retCode:
                self.writeLog(reason)
                return
        except:
            traceback.print_exc()

    def receivePostionDataFromMainWindow(self,posData):
        pass

    def receiveOptionSelectorDataFromMainWindow(self, optionSelectorData):
        pass

class LimitUpPlateMonitor(BasicMonitor):
    def __init__(self, catchLimitUpEngine, eventEngine, parent=None):
        try:
            super(LimitUpPlateMonitor, self).__init__(catchLimitUpEngine, eventEngine, parent)
            self.catchLimitUpEngine = catchLimitUpEngine
            self.eventEngine = eventEngine

            d = OrderedDict()
            d["plateName"] = {'chinese': u"板块名称", 'cellType': BasicCell}
            d["numOfStocks"] = {'chinese': u"包含股票数量", 'cellType': NumCell}
            d["catchedStocks"] = {'chinese': u"已抓到数量", 'cellType': NumCell}
            d["missedStocks"] = {'chinese': u"未抓到数量", 'cellType': NumCell}


            self.setHeaderDict(d)

            self.setDataKey('plateName')
            self.setEventType(EVENT_STRATEGY_CATCH_LIMITUP_STATUS)
            self.setFont(BASIC_FONT)
            self.setSaveData(True)
            self.setSorting(True)

            self.initTable()
            self.registerEvent()
            self.connectSignal()
        except:
            traceback.print_exc()

    def connectSignal(self):
        try:
            pass
        except:
            traceback.print_exc()


