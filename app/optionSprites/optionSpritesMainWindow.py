# encoding: utf-8


from qtpy import QtWidgets, QtCore
from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QPushButton, QComboBox, QVBoxLayout, QMessageBox
from qtpy.QtCore import Qt
from vnpy.event.eventEngine import Event
from commonFunction import parseOptionCode
from vnpy.trader.vtObject import VtLogData
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_TIMER
from qssBasic import EVENT_OPTION_TICK
from vnpy.trader.language.chinese.constant import DIRECTION_SHORT,DIRECTION_LONG

import traceback

class OptionSpritesMainWindow(QtWidgets.QWidget):

    def __init__(self, optionSpritesEngine, eventEngine, parent=None):
        try:
            super(OptionSpritesMainWindow, self).__init__(parent)

            self.optionSpritesEngine = optionSpritesEngine
            self.eventEngine = eventEngine

            self.optionSpritesEngine.start()

            self.initUi()
            self.registerEvent()
            self.forUT()

            # for update UI every 1s
            self.latestOptionTickDict = {}
        except:
            traceback.print_exc()


    def initUi(self):

        try:
            self.setWindowTitle(u"期权精灵")

            labelOptionCode = QLabel(u"期权代码")
            labelOwnerPrice = QLabel(u"正股价")
            labelPosition = QLabel(u"持有张数")
            labelCostPrice = QLabel(u"成本价")
            labelLatestPrice = QLabel(u"当前价")
            labelCalculatePrice = QLabel(u"公允价")
            labelBid1 = QLabel(u"买1价")
            labelAsk1 = QLabel(u"卖1价")
            labelTradePrice = QLabel(u"交易价格")
            labelTradeVolume = QLabel(u"交易数量")

            self.lineOptionCode = QLineEdit()
            self.lineOwnerPrice = QLineEdit()
            self.lineOwnerPrice.setDisabled(True)
            self.linePosition = QLineEdit()
            self.linePosition.setDisabled(True)
            self.lineCostPrice = QLineEdit()
            self.lineCostPrice.setDisabled(True)
            self.lineLatestPrice = QLineEdit()
            self.lineLatestPrice.setDisabled(True)
            self.lineCalculatedPrice = QLineEdit()
            self.lineCalculatedPrice.setDisabled(True)
            self.lineBid1 = QLineEdit()
            self.lineBid1.setDisabled(True)
            self.lineAsk1 = QLineEdit()
            self.lineAsk1.setDisabled(True)
            self.lineTradePrice = QLineEdit()
            self.lineTradeVolume = QLineEdit()

            vbox = QVBoxLayout()

            glayoutTop = QGridLayout()
            minLengthOfOptionCode = 300
            glayoutTop.addWidget(labelOptionCode,0, 1, Qt.AlignLeft)
            glayoutTop.addWidget(self.lineOptionCode,1, 1, Qt.AlignLeft)
            self.lineOptionCode.setMinimumWidth(minLengthOfOptionCode)

            glayout = QGridLayout()
            glayout.addWidget(labelOwnerPrice, 2, 1)
            glayout.addWidget(labelPosition, 2, 2)
            glayout.addWidget(labelCostPrice, 2 ,3)
            glayout.addWidget(labelLatestPrice, 2, 4)
            glayout.addWidget(labelCalculatePrice, 2 ,5)
            glayout.addWidget(labelBid1, 2 ,6)
            glayout.addWidget(labelAsk1, 2 ,7)

            glayout.addWidget(self.lineOwnerPrice, 3, 1)
            glayout.addWidget(self.linePosition, 3, 2)
            glayout.addWidget(self.lineCostPrice, 3, 3)
            glayout.addWidget(self.lineLatestPrice, 3, 4)
            glayout.addWidget(self.lineCalculatedPrice, 3 ,5)
            glayout.addWidget(self.lineBid1, 3 ,6)
            glayout.addWidget(self.lineAsk1, 3 ,7)


            glayout.addWidget(labelTradePrice, 4, 3)
            glayout.addWidget(self.lineTradePrice, 4, 4)
            glayout.addWidget(labelTradeVolume, 5, 3)
            glayout.addWidget(self.lineTradeVolume, 5, 4)

            btBuy = QPushButton(u"买")
            btSell = QPushButton(u"卖")

            glayout.addWidget(btBuy, 6, 3)
            glayout.addWidget(btSell, 6, 4)

            vbox.addLayout(glayoutTop)
            vbox.addLayout(glayout)
            self.setLayout(vbox)

            self.lineOptionCode.returnPressed.connect(self.qryOption)
            self.lineOptionCode.textChanged.connect(self.codeChanged)
            btBuy.clicked.connect(self.pressBuy)
            btSell.clicked.connect(self.pressSell)
        except:
            traceback.print_exc()

    def codeChanged(self,newCode):
        self.cleanUIData()

    def cleanUIData(self):
        try:
            self.lineOwnerPrice.setText("")
            self.lineLatestPrice.setText("")
            self.lineCalculatedPrice.setText("")

            self.lineBid1.setText("")
            self.lineAsk1.setText("")

            self.linePosition.setText("")
            self.lineCostPrice.setText("")
        except:
            traceback.print_exc()

    def qryOption(self):
        try:
            optionCode = self.lineOptionCode.text()
            if optionCode:
                optionDetail = parseOptionCode(optionCode)
            else:
                return

            if not optionDetail:
                self.writeLog("错误的期权代码:%s" %(optionCode))
                return

            self.optionSpritesEngine.startMonitorOption(optionDetail)
        except:
            traceback.print_exc()

    def getCodePriceVolume(self):
        try:
            volumeStr = self.lineTradeVolume.text()
            priceStr = self.lineTradePrice.text()
            optionCode = self.lineOptionCode.text()
            volume = float(volumeStr)
            price = float(priceStr)
        except:
            self.writeLog(u"检查价格[%s]数量[%s]是否正确" %(priceStr, volumeStr))
            return -1,0,0,0
        else:
            return (0, optionCode, price, volume)

    def pressSell(self):
        try:
            retCode, optionCode, price, volume = self.getCodePriceVolume()
            if retCode == 0:
                orderID = self.optionSpritesEngine.sendOrder(optionCode, DIRECTION_SHORT, price, volume)
                if orderID:
                    QMessageBox.information(self, u"下单结果", u"提交订单成功")
                else:
                    QMessageBox.information(self, u"下单结果", u"提交订单失败")
        except:
            traceback.print_exc()

    def pressBuy(self):
        try:
            retCode, optionCode, price, volume = self.getCodePriceVolume()
            if retCode == 0:
                orderID = self.optionSpritesEngine.sendOrder(optionCode, DIRECTION_LONG, price, volume)
                if orderID:
                    QMessageBox.information(self, u"下单结果", u"提交订单成功")
                else:
                    QMessageBox.information(self, u"下单结果", u"提交订单失败")
        except:
            traceback.print_exc()

    def registerEvent(self):
        try:
            self.eventEngine.register(EVENT_OPTION_TICK, self.saveLatestOptionTick)
            self.eventEngine.register(EVENT_TIMER, self.updateLatestTickOnUI)
        except:
            traceback.print_exc()

    def saveLatestOptionTick(self, event):
        try:
            optionTick = event.dict_['data']
            optionCode = optionTick.optionCode
            self.latestOptionTickDict[optionCode] = optionTick
        except:
            traceback.print_exc()

    def updateLatestTickOnUI(self,event):
        try:
            optionCode =self.lineOptionCode.text()
            # 如果输入框中的code 是已经订阅过的option则更新UI内容
            if optionCode in self.latestOptionTickDict:
                optionTick = self.latestOptionTickDict[optionCode]
                ownerCode = optionTick.ownerCode
                strikePrice = optionTick.strikePrice
                strikeDate = optionTick.strikeDate
                lastestPrice = optionTick.latestPrice
                ownerPrice = optionTick.ownerPrice
                calculatedPrice = optionTick.calculatedPrice
                bid1 = optionTick.bid1
                ask1 = optionTick.ask1

                position = optionTick.position
                costPrice = optionTick.costPrice

                self.lineOwnerPrice.setText(str(ownerPrice))
                self.lineLatestPrice.setText(str(lastestPrice))
                self.lineCalculatedPrice.setText(str(calculatedPrice))

                self.lineBid1.setText(str(bid1))
                self.lineAsk1.setText(str(ask1))

                self.linePosition.setText(str(position))
                self.lineCostPrice.setText(str(costPrice))
        except:
            traceback.print_exc()

    def forUT(self):
        try:
            self.lineOptionCode.setText(self.optionSpritesEngine.config["OptionCode"])
        except:
            traceback.print_exc()

    def writeLog(self, content):
        try:
            """快速发出日志事件"""
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'OPTION_SPRITES_MAIN_WINDOW'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()

    def receiveMarketDataFromMainWindow(self, tickData):
        code = tickData.symbol
        optionDetail = parseOptionCode(code)
        if optionDetail:
            self.lineOptionCode.setText(optionDetail["OptionCode"])
        else:
            pass