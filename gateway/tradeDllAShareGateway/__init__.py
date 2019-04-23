# encoding: UTF-8

from __future__ import absolute_import
from vnpy.trader import vtConstant
from .tradeDllAShareGateway import TradeDllAShareGateway

gatewayClass = TradeDllAShareGateway
gatewayName = 'TradeDllAShare'
gatewayDisplayName = u'TradeDllA股交易'
gatewayType = vtConstant.GATEWAYTYPE_INTERNATIONAL
gatewayQryEnabled = True