# encoding: utf-8


from qtpy import QtWidgets, QtCore
from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QPushButton, QComboBox, QVBoxLayout,QHBoxLayout,QGroupBox
from vnpy.event.eventEngine import Event
from vnpy.trader.vtObject import VtLogData
from vnpy.trader.vtEvent import EVENT_LOG
from vnpy.trader.language.chinese.constant import *
from constant import (CROSS_DIRECTION_DOWN, CROSS_DIRECTION_UP, TRADE_DIRECTION_BUY, TRADE_DIRECTION_SELL,
                        ORDER_PRICE_ORDERBOOK, ORDER_PRICE_AVG_ORDERBOOK )

from vnpy.trader.uiBasicWidget import BasicMonitor, BasicCell
from collections import OrderedDict
from qssBasic import EVENT_STRATEGY_STOP_ORDER_STATUS
from vnpy.trader.uiQt import BASIC_FONT
from commonFunction import GroupBoxWithSinglWidget, parseOptionCode

import sys
import traceback


class StopOrderMainWindow(QtWidgets.QWidget):

    tradeDirection = [TRADE_DIRECTION_SELL,
                      TRADE_DIRECTION_BUY]

    crossDirection = [CROSS_DIRECTION_UP,
                       CROSS_DIRECTION_DOWN]

    orderPriceStrategy = [ORDER_PRICE_ORDERBOOK,
                          ORDER_PRICE_AVG_ORDERBOOK]

    def __init__(self, stopOrderEngine, eventEngine, parent=None):
        super(StopOrderMainWindow, self).__init__(parent)

        self.stopOrderEngine = stopOrderEngine
        self.eventEngine = eventEngine

        try:
            self.stopOrderEngine.start()
            self.initUi()
            self.registerEvent()
            self.forUT()
        except:
            traceback.print_exc()


    def forUT(self):
        self.lineStockCode.setText(self.stopOrderEngine.config['stockCode'])
        self.lineStockOwnerCode.setText(self.stopOrderEngine.config['stockOwnerCode'])
        self.lineVolume.setText(self.stopOrderEngine.config['volume'])
        self.lineStockOwnerDrawdownPct.setText(self.stopOrderEngine.config['allowedDrawbackPct'])
        self.lineBeforeCloseTime.setText(self.stopOrderEngine.config['beforeCloseTime'])
        self.lineStockOwnerIncPct.setText(self.stopOrderEngine.config['incPct'])
        self.lineKeepPositionPct.setText(self.stopOrderEngine.config['keepPositionPct'])
        self.comboxCrossDirection.setCurrentText(self.stopOrderEngine.config['crossDirection'])
        self.comboxTradeDirection.setCurrentText(self.stopOrderEngine.config['tradeDirection'])

    def initUi(self):
        self.setWindowTitle(u"回撤止损赢")

        labelStockCode = QLabel(u"代码")
        labelCrossDirection = QLabel(u"当正股")
        labelTradeDirection = QLabel(u"执行")
        labelVolume = QLabel(u"标的股")
        labelStockOwnerCode = QLabel(u"正股代码")
        labelStockOwnerDrawdownPct = QLabel(u"正股最大回撤%")
        labelOrderPrice = QLabel(u"下单价格")
        labelBeforeCloseTime = QLabel(u"收盘前(秒)")
        labelStockOwnerIncPct = QLabel(u"正股涨跌>%")
        labelKeepPositionPct = QLabel(u"保留仓位%")


        self.lineStockCode = QLineEdit()
        self.comboxTradeDirection = QComboBox()
        self.comboxTradeDirection.addItems(self.tradeDirection)
        self.comboxCrossDirection = QComboBox()
        self.comboxCrossDirection.addItems(self.crossDirection)
        self.lineVolume = QLineEdit()
        self.lineStockOwnerCode = QLineEdit()
        self.lineStockOwnerDrawdownPct = QLineEdit()
        self.comboxLineOrderPrice = QComboBox()
        self.comboxLineOrderPrice.addItems(self.orderPriceStrategy)
        self.lineBeforeCloseTime = QLineEdit()
        self.lineStockOwnerIncPct = QLineEdit()
        self.lineKeepPositionPct = QLineEdit()


        # 最上层 group box
        maxLenStockCode = 300
        maxLabelLen1 = 50
        gbTarget = QGroupBox()
        gbTarget.setTitle(u"标的股")
        hbox1 = QHBoxLayout()
        hbox1.addWidget(labelStockCode)
        hbox1.addWidget(self.lineStockCode)
        labelStockCode.setMaximumWidth(maxLabelLen1)
        self.lineStockCode.setMaximumWidth(maxLenStockCode)
        hbox1.addWidget(labelStockCode)
        hbox1.addWidget(self.lineStockCode)
        hbox1.addStretch()
        gbTarget.setLayout(hbox1)

        # 第二层 grid layout
        # line 0
        glayout = QGridLayout()
        gridMaxLen1 = 120
        gridMaxLen2 = 120
        glayout.addWidget(labelStockOwnerCode, 0, 0)
        glayout.addWidget(self.lineStockOwnerCode, 0, 1)
        glayout.addWidget(labelCrossDirection, 0 , 2)
        glayout.addWidget(self.comboxCrossDirection, 0, 3)
        glayout.addWidget(labelTradeDirection, 0 ,4)
        glayout.addWidget(self.comboxTradeDirection, 0, 5)
        glayout.addWidget(labelVolume, 0 ,6)
        glayout.addWidget(self.lineVolume, 0, 7)
        self.lineStockOwnerCode.setMaximumWidth(gridMaxLen1)
        self.comboxCrossDirection.setMaximumWidth(gridMaxLen2)
        self.comboxTradeDirection.setMaximumWidth(gridMaxLen2)
        self.lineVolume.setMaximumWidth(gridMaxLen2)
        # line 1
        glayout.addWidget(labelStockOwnerDrawdownPct, 1, 0)
        glayout.addWidget(self.lineStockOwnerDrawdownPct, 1, 1)
        glayout.addWidget(labelOrderPrice, 1, 2)
        glayout.addWidget(self.comboxLineOrderPrice, 1, 3)
        self.lineStockOwnerDrawdownPct.setMaximumWidth(gridMaxLen1)
        # line 2
        glayout.addWidget(labelBeforeCloseTime, 2, 0)
        glayout.addWidget(self.lineBeforeCloseTime, 2, 1)
        glayout.addWidget(labelStockOwnerIncPct, 2, 2)
        glayout.addWidget(self.lineStockOwnerIncPct, 2, 3)
        glayout.addWidget(labelKeepPositionPct, 2, 4)
        glayout.addWidget(self.lineKeepPositionPct, 2, 5)
        self.lineBeforeCloseTime.setMaximumWidth(gridMaxLen1)
        self.lineStockOwnerIncPct.setMaximumWidth(gridMaxLen2)
        self.lineKeepPositionPct.setMaximumWidth(gridMaxLen2)

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
        hbox2.addWidget(btStopAll)
        hbox2.addStretch()
        hbox2.setSpacing(space)
        btStart.setFixedWidth(fixLenButton)
        btStopAll.setFixedWidth(fixLenButton)

        vbox = QVBoxLayout()
        vbox.addWidget(gbTarget)
        vbox.addLayout(glayout)
        vbox.addLayout(hbox2)

        # 策略状态组件
        self.strategyWidget = StrategyStopOrderMonitor(self.stopOrderEngine, self.eventEngine)
        groupBoxStraMonitor = GroupBoxWithSinglWidget(self.strategyWidget, u"策略状态")
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
            # stockCdoe stockOwnerCode 格式 XX.XXXXXX
            # volume 正整数
            # allowedDrawbackPct, incPct，keepPostionPct[0, 10]
            # beforeClosetTime 600秒以内？
            straConfig["volume"] = int(straConfig["volume"])
            straConfig["allowedDrawbackPct"] = float(straConfig["allowedDrawbackPct"])
            straConfig["beforeCloseTime"] = int(straConfig["beforeCloseTime"])
            straConfig["incPct"] = float(straConfig["incPct"])
            straConfig["keepPositionPct"] = float(straConfig["keepPositionPct"])

            return 0
        except:
            traceback.print_exc()

    def startStrategy(self):
        try:
            print(u"In stopOrderMainWindow startStrategy")

            straConfig = {}
            straConfig["stockCode"] = self.lineStockCode.text()
            straConfig["stockOwnerCode"] = self.lineStockOwnerCode.text()
            straConfig["volume"] = self.lineVolume.text()
            straConfig["allowedDrawbackPct"] = self.lineStockOwnerDrawdownPct.text()
            straConfig["orderPriceStrategy"] = self.comboxLineOrderPrice.currentText()
            straConfig["beforeCloseTime"] = self.lineBeforeCloseTime.text()
            straConfig["incPct"] = self.lineStockOwnerIncPct.text()
            straConfig["keepPositionPct"] = self.lineKeepPositionPct.text()
            straConfig["crossDirection"] = self.comboxCrossDirection.currentText()
            straConfig["tradeDirection"] = self.comboxTradeDirection.currentText()

            retCode = self.verifyAndConvertInputParam(straConfig)
            if retCode:
                return

            # 添加策略到Engine
            retCode, reason = self.stopOrderEngine.addStrategy(straConfig)
            if retCode:
                self.writeLog(reason)
                return
        except:
            traceback.print_exc()

    def receivePostionDataFromMainWindow(self,posData):
        try:
            # posData是VtPositionData类型的
            # 把从主窗口接收到的postion信息，用来更新UI
            code = posData.symbol
            direction = posData.direction
            position = posData.position - posData.frozen

            optionData = parseOptionCode(code)
            # 如果是option，解析出对应的正股
            if optionData:
                code = optionData["OptionCode"]
                ownerCode = optionData["OwnerCode"]
            else:
                code = code
                ownerCode = ""
            # 更新UI数据
            self.lineStockCode.setText(code)
            self.lineStockOwnerCode.setText(ownerCode)
            self.lineVolume.setText(str(int(position)))
        except:
            traceback.print_exc()

class StrategyStopOrderMonitor(BasicMonitor):
    def __init__(self, stopOrderEngine, eventEngine, parent=None):
        try:
            super(StrategyStopOrderMonitor, self).__init__(stopOrderEngine, eventEngine, parent)
            self.stopOrderEngine = stopOrderEngine
            self.eventEngine = eventEngine

            d = OrderedDict()
            d["strategyID"] = {'chinese': u"策略标识", 'cellType': BasicCell}
            d["status"] = {'chinese': u"状态", 'cellType': BasicCell}
            d["ownerPrice"] = {'chinese': u"正股价格", 'cellType': BasicCell}
            d["ownerMaxMinPrice"] = {'chinese': u"正股极值", 'cellType': BasicCell}
            d["triggerPrice"] = {'chinese': u"触发价格", 'cellType': BasicCell}
            d["crossDirection"] = {'chinese': u"穿透方向", 'cellType': BasicCell}
            d["tradeDirection"] = {'chinese': u"交易类型", 'cellType': BasicCell}
            d["volume"] = {'chinese': u"设定数量", 'cellType': BasicCell}
            d["orderVolume"] = {'chinese': u"下单数量", 'cellType': BasicCell}

            self.setHeaderDict(d)

            self.setDataKey('strategyID')
            self.setEventType(EVENT_STRATEGY_STOP_ORDER_STATUS)
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
            self.itemDoubleClicked.connect(self.cancelOrRestartStrategy)
        except:
            traceback.print_exc()

    def cancelOrRestartStrategy(self,cell):
        try:
            straData = cell.data   # 类型为 VtStrategyStopOrderStatus()
            stratrgyID = straData.strategyID
            self.stopOrderEngine.cancelOrRestartStrategy(stratrgyID)
        except:
            traceback.print_exc()




