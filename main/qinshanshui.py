# encoding: UTF-8

# 重载sys模块，设置默认字符串编码方式为utf8
try:
    reload         # Python 2
except NameError:  # Python 3
    from importlib import reload
import sys
reload(sys)
# sys.setdefaultencoding('utf8')

import traceback

# vn.trader模块
from vnpy.event import EventEngine
from vnpy.trader.vtEngine import MainEngine
from vnpy.trader.uiQt import createQApp
from vnpy.trader.uiMainWindow import MainWindow

# 加载底层接口
from vnpy.trader.gateway import futuGateway
from gateway import tradeDllAShareGateway

# 加载上层应用
from vnpy.trader.app import (riskManager, ctaStrategy, spreadTrading)

from app import slipperyGrid, stopOrder, optionSprites, optionSelector, catchLimitUp

#----------------------------------------------------------------------
def main():
    """主程序入口"""
    # 创建Qt应用对象
    qApp = createQApp()
    
    # 创建事件引擎
    ee = EventEngine()
    
    # 创建主引擎
    me = MainEngine(ee)
    
    # 添加交易接口
    me.addGateway(futuGateway)
    me.addGateway(tradeDllAShareGateway)

    # 添加上层应用
    #me.addApp(riskManager)
    # me.addApp(ctaStrategy)
    # me.addApp(spreadTrading)
    me.addApp(stopOrder)
    # me.addApp(slipperyGrid)
    me.addApp(optionSelector)
    me.addApp(optionSprites)
    me.addApp(catchLimitUp)
    
    # 创建主窗口
    mw = MainWindow(me, ee)
    mw.showMaximized()

    # 在主线程中启动Qt事件循环
    sys.exit(qApp.exec_())


if __name__ == '__main__':
    main()
