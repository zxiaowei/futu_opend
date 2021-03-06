# encoding: utf-8


from qtpy import QtWidgets, QtCore
from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QPushButton, QComboBox, QVBoxLayout, QMessageBox
from commonFunction import parseOptionCode, GroupBoxWithSinglWidget
from vnpy.trader.vtObject import VtLogData
from vnpy.trader.language.chinese.constant import DIRECTION_SHORT,DIRECTION_LONG
from vnpy.trader.uiBasicWidget import BasicMonitor, BasicCell, FloatCell, NumCell
from collections import OrderedDict
from vnpy.trader.uiQt import BASIC_FONT
from qssBasic import VtOptionSelectorData
from datetime import datetime, timedelta
from vnpy.event.eventEngine import Event
from vnpy.trader.vtEvent import EVENT_LOG

import traceback

class OptionSelectorMainWindow(QtWidgets.QWidget):

    optionType = ["CALL", "PUT","C&P"]
    optionPropertiesList = ['code', 'last_price', 'option_type','strike_time', 'option_strike_price',
                            'option_open_interest', 'volume', 'option_delta','option_gamma', 'option_vega']

    def __init__(self, optionSelectorEngine, eventEngine, mainWindow=None, parent=None):
        try:
            super(OptionSelectorMainWindow, self).__init__(parent)
            self.optionSelectorEngine = optionSelectorEngine
            self.eventEngine = eventEngine
            self.mainWindow = mainWindow

            self.optionSelectorEngine.start()
            self.initUi()
            self.registerEvent()
            self.forUT()

        except:
            traceback.print_exc()


    def initUi(self):
        try:
            self.setWindowTitle(u"期权选择器")
            self.setMinimumWidth(1200)
            self.setMinimumHeight(800)

            labelStockCode = QLabel(u"代码")
            labelStockPrice = QLabel(u"价格(非实时)")
            labelSTDTimes = QLabel(u"标准差倍数")
            labelSTDValue = QLabel(u"标准差")
            labelSTDDays = QLabel(u"计算天数")
            lableStartDate = QLabel(u"开始日期")
            labelEndDate = QLabel(u"结束日期")
            labelType = QLabel(u"类型")
            labelStrikePrice = QLabel(u"行权价范围")

            self.lineStockCode = QLineEdit()
            self.lineStockPrice = QLineEdit()
            self.lineStockPrice.setEnabled(False)
            self.lineSTDTimes = QLineEdit()
            self.lineSTDValue = QLineEdit()
            self.lineSTDValue.setEnabled(False)
            self.lineSTDDays = QLineEdit()
            self.lineStartDate = QLineEdit()
            self.lineEndDate = QLineEdit()
            self.comboxType = QComboBox()
            self.comboxType.addItems(self.optionType)
            self.lineLowStrikePrice = QLineEdit()
            self.lineHighStrikePrice = QLineEdit()

            btQry = QPushButton(u"查询")
            btSort = QPushButton(u"排序开关")

            glayout = QGridLayout()
            glayout.addWidget(labelStockCode, 0, 0)
            glayout.addWidget(labelStockPrice, 0 , 1)
            glayout.addWidget(labelSTDTimes, 0 , 2)
            glayout.addWidget(labelSTDValue, 0 ,3)
            glayout.addWidget(labelSTDDays, 0 ,4)


            glayout.addWidget(self.lineStockCode, 1, 0)
            glayout.addWidget(self.lineStockPrice, 1, 1)
            glayout.addWidget(self.lineSTDTimes, 1, 2)
            glayout.addWidget(self.lineSTDValue, 1, 3)
            glayout.addWidget(self.lineSTDDays, 1, 4)
            self.lineStockCode.setMaximumWidth(150)
            self.lineStockPrice.setMaximumWidth(150)
            self.lineSTDTimes.setMaximumWidth(80)
            self.lineSTDValue.setMaximumWidth(150)
            self.lineSTDDays.setMaximumWidth(80)

            glayout.addWidget(lableStartDate, 2, 0)
            glayout.addWidget(labelEndDate, 2, 1)
            glayout.addWidget(labelType, 2,2)
            glayout.addWidget(labelStrikePrice, 2, 3)

            glayout.addWidget(self.lineStartDate, 3, 0)
            glayout.addWidget(self.lineEndDate, 3, 1)
            glayout.addWidget(self.comboxType, 3, 2)
            glayout.addWidget(self.lineLowStrikePrice, 3, 3)
            glayout.addWidget(self.lineHighStrikePrice, 3, 4)

            self.lineStartDate.setMaximumWidth(150)
            self.lineEndDate.setMaximumWidth(150)
            self.lineLowStrikePrice.setMaximumWidth(150)
            self.lineHighStrikePrice.setMaximumWidth(150)

            glayout.addWidget(btQry, 4, 0)
            glayout.addWidget(btSort, 4, 1)

            vbox = QVBoxLayout()
            # 策略状态组件
            self.optionSelectorMonitorWidget = OptionSelectorMonitor(self.optionSelectorEngine, self.eventEngine, \
                                                                     self.mainWindow)
            groupBoxStraMonitor = GroupBoxWithSinglWidget(self.optionSelectorMonitorWidget, u"期权信息")

            vbox.addLayout(glayout)
            vbox.addWidget(groupBoxStraMonitor)
            self.setLayout(vbox)

            btQry.clicked.connect(self.qryOptionList)
            btSort.clicked.connect(self.switchSort)
            self.lineStockCode.returnPressed.connect(self.pressPriceReturn)
            self.optionSelectorMonitorWidget.itemDoubleClicked.connect(self.passOptionSelectorDataToMainWindow)

        except:
            traceback.print_exc()

    def pressPriceReturn(self):
        self.qryStockPrice()
        # self.updateDefaultOptionStrikePrice()

    def cleanPriceRetrun(self):
        self.lineSTDValue.clear()
        self.lineLowStrikePrice.clear()
        self.lineHighStrikePrice.clear()
        self.lineStockPrice.clear()

    def qryStockPrice(self):
        try:
            self.cleanPriceRetrun()

            code = self.lineStockCode.text()
            df = self.optionSelectorEngine.qryMarketSnapshot(code)
            # 设置当前价格
            if len(df) > 0:
                price = df['last_price'][0]
                self.lineStockPrice.setText(str(price))
                # 记录昨收价
                preClosePrice = df['prev_close_price'][0]
            else:
                # error
                return

            #  计算估计近日来的标准差
            numOfDays = self.lineSTDDays.text()
            try:
                numOfDays = int(numOfDays)
            except:
                raise Exception(u"计算天数输入错误 %s" %numOfDays)

            std = self.optionSelectorEngine.calSTD(code, numOfDays)
            if std >= 0:
                # 设置行权价范围
                times = self.lineSTDTimes.text()
                try:
                    times = round(float(times),3)
                except:
                    self.writeLog(u"方差倍数设置不正确")
                    return

                lowPrice = (preClosePrice * (1 - std * times) )
                highPrice = (preClosePrice * ( 1 + std * times) )
                lowPrice = round(lowPrice, 3)
                highPrice = round(highPrice, 3)
                self.lineSTDValue.setText(str(round(std,4)))
                self.lineLowStrikePrice.setText(str(lowPrice))
                self.lineHighStrikePrice.setText(str(highPrice))
            else:
                # 无法计算波动范围
                self.writeLog(u"无法计算标准差 %s %s" %(code, numOfDays))


        except:
            traceback.print_exc()

    def updateDefaultOptionStrikePrice(self):
        try:
            # 默认区间是 0.9 - 1.1 倍股价
            priceStr = self.lineStockPrice.text()
            price = float(priceStr)
            lowPrice = int(price * 0.9)
            highPrice = int(price * 1.1)
            self.lineLowStrikePrice.setText(str(lowPrice))
            self.lineHighStrikePrice.setText(str(highPrice))
        except:
            pass


    def passOptionSelectorDataToMainWindow(self,cell):
        try:
            optionSelectorData = cell.data
            self.mainWindow.accpetOptionData(optionSelectorData, "OptionSprites")
        except:
            traceback.print_exc()

    def switchSort(self):
        self.optionSelectorMonitorWidget.switchSort()

    def qryOptionList(self):
        try:
            # 先查询最新股票价格
            # self.qryStockPrice()
            stockCode = self.lineStockCode.text()
            startDate = self.lineStartDate.text()
            endDate = self.lineEndDate.text()
            optLowPriceStr = self.lineLowStrikePrice.text()
            optHighPriceStr = self.lineHighStrikePrice.text()

            # 检查code，startDate， endDate, lowPrice, highPrice
            # Todo
            try:
                optLowPrice = 0
                optLowPrice = round(float(optLowPriceStr), 3)
            except:
                pass

            try:
                optHighPrice = 0
                optHighPrice = round(float(optHighPriceStr), 3)
            except:
                pass

            optType = self.comboxType.currentText()

            self.optionSelectorEngine.qryOptionList(stockCode, startDate, endDate, optLowPrice, optHighPrice, optType)
            self.updateDisplay()
        except:
            traceback.print_exc()

    def updateDisplay(self):
        try:
            stockCode = self.lineStockCode.text()
            df1 = self.optionSelectorEngine.getOptionDF(stockCode)

            # 查询返回有满足条件的option
            if len(df1) > 0:
                optionDF = df1[self.optionPropertiesList]
                optionDF = optionDF.sort_values(["option_strike_price","strike_time"], ascending=False)
                # 清除原来数据
                self.optionSelectorMonitorWidget.setRowCount(0)
                self.optionSelectorMonitorWidget.clearContents()
                # 更新符合条件的数据
                for index, row in optionDF.iterrows():
                    data = VtOptionSelectorData()
                    data.code = row['code']
                    data.last_price = row['last_price']
                    data.option_type = row['option_type']
                    data.strike_time = row['strike_time']
                    data.option_strike_price = row['option_strike_price']
                    data.option_open_interest = row['option_open_interest']
                    data.volume = row['volume']
                    data.option_delta = row['option_delta']
                    data.option_gamma = row['option_gamma']
                    data.option_vega = row['option_vega']

                    self.optionSelectorMonitorWidget.updateData(data)

        except:
            traceback.print_exc()

    def registerEvent(self):
        pass

    def forUT(self):
        self.lineStockCode.setText("US.AAPL")
        dtToday = datetime.today()
        dtStr = dtToday.strftime("%Y-%m-%d")
        dtEnd = dtToday + timedelta(days=45)
        dtEndStr = dtEnd.strftime("%Y-%m-%d")
        self.lineStartDate.setText(dtStr)
        self.lineEndDate.setText(dtEndStr)
        self.lineLowStrikePrice.setText("160")
        self.lineHighStrikePrice.setText("190")
        self.lineSTDTimes.setText("1.0")
        self.lineSTDDays.setText("30")

    def writeLog(self, content):
        try:
            log = VtLogData()
            log.logContent = content
            log.gatewayName = 'OPTION_SELECTOR_MAIN_WINDOW'
            event = Event(type_=EVENT_LOG)
            event.dict_['data'] = log
            self.eventEngine.put(event)
        except:
            traceback.print_exc()


class OptionSelectorMonitor(BasicMonitor):
    def __init__(self, optionSelectorEngine, eventEngine, mainWindow, parent=None):
        try:
            super(OptionSelectorMonitor, self).__init__(optionSelectorEngine, eventEngine, parent)
            self.optionSelectorEngine = optionSelectorEngine
            self.eventEngine = eventEngine
            self.mainWindow = mainWindow

            d = OrderedDict()
            d["code"] = {'chinese': u"代码", 'cellType': BasicCell}
            d["option_type"] = {'chinese': u"类型", 'cellType': BasicCell}
            d["last_price"] = {'chinese': u"最新价格", 'cellType': FloatCell}
            d["strike_time"] = {'chinese': u"行权日", 'cellType': BasicCell}
            d["option_strike_price"] = {'chinese': u"行权价", 'cellType': FloatCell}
            d["option_open_interest"] = {'chinese': u"未平仓数", 'cellType': NumCell}
            d["volume"] = {'chinese': u"交易量", 'cellType': NumCell}
            d["option_delta"] = {'chinese': u"Delta", 'cellType': FloatCell}
            d["option_gamma"] = {'chinese': u"Gamma", 'cellType': FloatCell}
            d["option_vega"] = {'chinese': u"Vega", 'cellType': FloatCell}

            self.setHeaderDict(d)

            # 不设置datakey， 每次查询都清空table，重新插入
            # self.setDataKey('code')
            self.setFont(BASIC_FONT)
            self.setSaveData(True)
            self.setSorting(False)

            self.initTable()
            self.connectSignal()

            # 打开左边的垂直表头
            self.verticalHeader().setVisible(True)
        except:
            traceback.print_exc()

    def connectSignal(self):
        try:
            pass
        except:
            traceback.print_exc()

    def switchSort(self):
        self.sorting = not self.sorting
        self.setSortingEnabled(self.sorting)

    def passOptionSelectorDataToMainWindow(self):
        try:
            itemList = self.selectedItems()
            optionSelectorData = itemList[0].data
            self.mainWindow.accpetOptionData(optionSelectorData, "StopOrder")
        except:
            traceback.print_exc()

    def initMenu(self):
        """初始化右键菜单"""
        self.menu = QtWidgets.QMenu(self)

        stopOrderAction = QtWidgets.QAction(u"回撤止损赢", self)
        stopOrderAction.triggered.connect(self.passOptionSelectorDataToMainWindow)
        self.menu.addAction(stopOrderAction)

