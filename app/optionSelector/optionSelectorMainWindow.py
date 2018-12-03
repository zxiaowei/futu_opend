# encoding: utf-8


from qtpy import QtWidgets, QtCore
from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QPushButton, QComboBox, QVBoxLayout, QMessageBox
from qtpy.QtCore import Qt
from vnpy.event.eventEngine import Event
from commonFunction import parseOptionCode
from vnpy.trader.vtObject import VtLogData
from vnpy.trader.language.chinese.constant import DIRECTION_SHORT,DIRECTION_LONG

import traceback

class OptionSelectorMainWindow(QtWidgets.QWidget):

    optionType = ["CALL", "PUT"]
    optionPropertiesList = ['code', 'last_price', 'option_type','strike_time', 'option_strike_price',
                            'option_open_interest', 'volume', 'option_delta']

    def __init__(self, optionSelectorEngine, eventEngine, parent=None):
        try:
            super(OptionSelectorMainWindow, self).__init__(parent)
            self.optionSelectorEngine = optionSelectorEngine
            self.eventEngine = eventEngine

            self.optionSelectorEngine.start()
            self.initUi()
            self.registerEvent()
            self.forUT()

        except:
            traceback.print_exc()


    def initUi(self):
        try:
            self.setWindowTitle(u"期权选择器")

            labelStockCode = QLabel(u"代码")
            lableStartDate = QLabel(u"开始日期")
            labelEndDate = QLabel(u"结束日期")
            labelType = QLabel(u"类型")
            labelStrikePrice = QLabel(u"行权价范围")

            self.lineStockCode = QLineEdit()
            self.lineStartDate = QLineEdit()
            self.lineEndDate = QLineEdit()
            self.comboxType = QComboBox()
            self.comboxType.addItems(self.optionType)
            self.lineLowStrikePrice = QLineEdit()
            self.lineHighStrikePrice = QLineEdit()

            btQry = QPushButton(u"查询")
            btUpdateDisplay = QPushButton(u"更新显示")

            glayout = QGridLayout()
            glayout.addWidget(labelStockCode, 0, 0)
            glayout.addWidget(self.lineStockCode, 1, 0)
            glayout.addWidget(lableStartDate, 2, 0)
            glayout.addWidget(labelEndDate, 2, 1)
            glayout.addWidget(labelType, 2,2)
            glayout.addWidget(labelStrikePrice, 2, 3)
            glayout.addWidget(self.lineStartDate, 3, 0)
            glayout.addWidget(self.lineEndDate, 3, 1)
            glayout.addWidget(self.comboxType, 3, 2)
            glayout.addWidget(self.lineLowStrikePrice, 3, 3)
            glayout.addWidget(self.lineHighStrikePrice, 3, 4)
            glayout.addWidget(btQry, 4, 0)
            glayout.addWidget(btUpdateDisplay, 4, 1)

            btQry.clicked.connect(self.qryOptionList)
            btUpdateDisplay.clicked.connect(self.updateDisplay)

            self.setLayout(glayout)
        except:
            traceback.print_exc()

    def qryOptionList(self):
        try:
            stockCode = self.lineStockCode.text()
            startDate = self.lineStartDate.text()
            endDate = self.lineEndDate.text()

            self.optionSelectorEngine.qryOptionList(stockCode, startDate, endDate)

            self.updateDisplay()
        except:
            traceback.print_exc()

    def updateDisplay(self):
        try:
            stockCode = self.lineStockCode.text()
            df1 = self.optionSelectorEngine.getOptionDF(stockCode)

            optType = self.comboxType.currentText()
            optLowPriceStr = self.lineLowStrikePrice.text()
            optHighPriceStr = self.lineHighStrikePrice.text()

            filterLow = False
            filterHigh = False

            try:
                optLowPrice = round(float(optLowPriceStr), 3)
                filterLow = True
            except:
                pass

            try:
                optHighPrice = round(float(optHighPriceStr), 3)
                filterHigh = True
            except:
                pass

            if len(df1) > 0:
                optionDF = df1[self.optionPropertiesList]
                optionDF = optionDF[optionDF['option_type']==optType]
                if filterLow:
                    optionDF = optionDF[optionDF['option_strike_price'] >= optLowPrice]
                if filterHigh:
                    optionDF = optionDF[optionDF['option_strike_price'] <= optHighPrice]

                optionDF = optionDF.sort_values(["option_strike_price","strike_time"], ascending=True)

            pass
        except:
            traceback.print_exc()

    def registerEvent(self):
        pass

    def forUT(self):
        self.lineStockCode.setText("US.AAPL")
        self.lineStartDate.setText("2018-12-03")
        self.lineEndDate.setText("2018-12-15")
        self.lineLowStrikePrice.setText("160")
        self.lineHighStrikePrice.setText("190")