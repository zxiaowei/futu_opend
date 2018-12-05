# encoding: utf-8

from .stopOrderEngine import StopOrderEngine
from .stopOrderMainWindow import StopOrderMainWindow

appName = 'StopOrder'
appDisplayName = u'回撤止损赢'
appEngine = StopOrderEngine
appWidget = StopOrderMainWindow
appIco = 'stop.ico'
needMainWindow = False