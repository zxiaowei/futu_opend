# encoding: utf-8

from .catchLimitUpEngine import CatchLimitUpEngine
from .catchLimitUpWindow import CatchLimitUpMainWindow

appName = 'CatchLimitUp'
appDisplayName = u'看板儿狗'
appEngine = CatchLimitUpEngine
appWidget = CatchLimitUpMainWindow
appIco = 'stop.ico'
needMainWindow = False