# encoding: utf-8


from qtpy import QtWidgets, QtCore
from qtpy.QtWidgets import QLabel, QLineEdit, QGridLayout, QCheckBox, QHBoxLayout
from vnpy.event.eventEngine import Event


class SlipperyGridMainWindow(QtWidgets.QWidget):


    signalParam = QtCore.Signal(type(Event()))

    def __init__(self, strategyEngine, eventEngine, parent=None):
        super(SlipperyGridMainWindow, self).__init__(parent)

        self.strategyEngine = strategyEngine
        self.eventEngine = eventEngine

        self.sigFunParam = self.signalParam.emit

        self.strategyEngine.start()

        self.initUi()
        self.registerEvent()

    def initUi(self):
        self.setWindowTitle(u"滑头网格策略")

        labelStockOwner = QLabel(u"正股代码")
        labelStockP = QLabel(u"正向标的代码")
        labelStockN = QLabel(u"负向标的代码")
        labelOnlyOwner = QLabel(u"只正股")
        labelBiDirection = QLabel(u"双向")
        self.lineStockOwner = QLineEdit()
        self.lineStockP = QLineEdit()
        self.lineStockN = QLineEdit()
        self.checkBoxOnlyOwner = QCheckBox()
        self.checkBoxDiDirection = QCheckBox()

        gridTop = QGridLayout()
        gridTop.addWidget(labelStockOwner, 0, 0)
        gridTop.addWidget(self.lineStockOwner, 0, 1)
        gridTop.addWidget(labelStockP, 0 ,2)
        gridTop.addWidget(self.lineStockP, 0, 3)
        gridTop.addWidget(labelStockN, 1 ,2)
        gridTop.addWidget(self.lineStockN, 1, 3)
        gridTop.addWidget(labelOnlyOwner,2,0)
        gridTop.addWidget(self.checkBoxOnlyOwner,2,1)
        gridTop.addWidget(labelBiDirection, 3, 0)
        gridTop.addWidget(self.checkBoxDiDirection, 3, 1)

        self.setLayout(gridTop)


        # 关联UI事件
        self.lineStockOwner.returnPressed.connect(self.qryStockRelationship)

    def qryStockRelationship(self):
        stockOwnerCode = self.lineStockOwner.text()
        if stockOwnerCode in self.strategyEngine.stockOwnership :
            stockPCode = self.strategyEngine.stockOwnership[stockOwnerCode]['positive']
            stockNCode = self.strategyEngine.stockOwnership[stockOwnerCode]['negative']
            self.lineStockP.setText(stockPCode)
            self.lineStockN.setText(stockNCode)

        #注册UI事件处理
        stockList = [stockOwnerCode, stockPCode, stockNCode]
        self.strategyEngine.subscribe(stockList)

    def registerEvent(self):
        pass




