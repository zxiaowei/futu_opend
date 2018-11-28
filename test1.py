from futuquant import *
SysConfig.set_client_info("MyFutuQuant", 0)
SysConfig.set_all_thread_daemon(True)
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11112)

#
# print(quote_ctx.get_market_snapshot('HK.00700'))
# print(quote_ctx.get_trading_days(Market.HK, start='2018-01-01', end='2018-01-10'))
df1 = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.WARRANT, "HK.00700")
df1 = quote_ctx.get_stock_basicinfo(Market.US, SecurityType.DRVT, 'US.AAPL190621C140000')
# print(quote_ctx.get_multiple_history_kline(['HK.00700','US.JD'], '2018-06-20', '2018-06-25', KLType.K_DAY, AuType.QFQ))
# print(quote_ctx.get_history_kline('HK.00700', start='2017-06-20', end='2017-06-22'))
# print(quote_ctx.get_autype_list(["HK.00700"]))
#
# print(quote_ctx.get_market_snapshot(['US.AAPL', 'HK.00700']))
# print(quote_ctx.get_plate_stock('HK.BK1001'))
#
# print(quote_ctx.get_plate_list(Market.HK, Plate.ALL))
# print(quote_ctx.get_referencestock_list('HK.00700', SecurityReferenceType.WARRANT))
# print(quote_ctx.get_option_chain('US.AAPL', '2018-10-25', '2018-11-18', OptionType.ALL, OptionCondType.ALL))
#
# df1 = quote_ctx.get_market_snapshot("US.AAPL181012C180000")
# print(df1)
quote_ctx.subscribe(['US.TQQQ','US.SQQQ','US..IXIC'], [SubType.ORDER_BOOK, SubType.QUOTE])
df1 = quote_ctx.get_order_book("US.TQQQ")
df1 = quote_ctx.get_order_book("US.SQQQ")
df1 = quote_ctx.get_order_book("US..IXIC")
df1 = quote_ctx.get_stock_quote("US..IXIC")



ret, df1 = quote_ctx.get_referencestock_list("HK.00700", SecurityReferenceType.WARRANT)
list1 = list(df1['code'])
df2 = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.WARRANT, list1)
df3 = quote_ctx.get_market_snapshot(list1[-300:])
ret, df4 = quote_ctx.get_option_chain('US.AAPL', '2018-10-25', '2018-11-18', OptionType.ALL, OptionCondType.ALL)
list2 = list(df4['code'])
df5 = quote_ctx.get_market_snapshot(list2[-300:])

df1 = quote_ctx.get_history_kline('US..IXIC', start='2018-10-22', end='2018-10-25', ktype=KLType.K_1M)


quote_ctx.close()




pwd_unlock = '887886'
hk_trd_ctx = OpenHKTradeContext(host='127.0.0.1', port=11112)
us_trd_ctx = OpenUSTradeContext(host='127.0.0.1', port=11112)
print(hk_trd_ctx.unlock_trade(pwd_unlock))
# print(trd_ctx.place_order(price=700.0, qty=100, code="HK.00700", trd_side=TrdSide.BUY))

df1 = hk_trd_ctx.get_acc_list()
df1 = hk_trd_ctx.accinfo_query(TrdEnv.REAL)


df1 = us_trd_ctx.get_acc_list()
df1 = us_trd_ctx.accinfo_query(TrdEnv.REAL)
df1 = us_trd_ctx.accinfo_query(TrdEnv.SIMULATE)

df2 = hk_trd_ctx.position_list_query()
df3 = us_trd_ctx.position_list_query()


us_trd_ctx.close()
hk_trd_ctx.close()