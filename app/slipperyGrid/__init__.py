# encoding: utf-8

from .strategyEngine import StrategyEngine
from .slipperyGridMainWindow import SlipperyGridMainWindow

appName = 'SlipperyGrid'
appDisplayName = u'滑头网格策略'
appEngine = StrategyEngine
appWidget = SlipperyGridMainWindow
appIco = 'grid.ico'