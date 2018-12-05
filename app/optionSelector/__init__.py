# encoding: utf-8

from .optionSelectorEngine import OptionSelectorEngine
from .optionSelectorMainWindow import OptionSelectorMainWindow

appName = 'OptionSelector'
appDisplayName = u"期权选择器"
appEngine = OptionSelectorEngine
appWidget = OptionSelectorMainWindow
appIco = 'selector.ico'
needMainWindow = True