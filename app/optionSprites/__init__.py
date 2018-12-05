# encoding: utf-8

from .optionSpritesEngine import OptionSpritesEngine
from .optionSpritesMainWindow import OptionSpritesMainWindow

appName = 'OptionSprites'
appDisplayName = u'期权精灵'
appEngine = OptionSpritesEngine
appWidget = OptionSpritesMainWindow
appIco = 'sprites.ico'
needMainWindow = False