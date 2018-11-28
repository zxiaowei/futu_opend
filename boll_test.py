from futuquant import *
import talib
from talib import MA_Type
import matplotlib.pyplot as plt

quote_ctx = OpenQuoteContext(host='10.0.0.2', port=22221)

retCode, df1 = quote_ctx.get_multiple_history_kline("HK.00700,HK.28110",start='2018-11-16',end='2018-11-17', ktype=KLType.K_1M)

closed=df1[0]['close'].values

upper, middle, lower = talib.BBANDS(closed, matype=talib.MA_Type.T3)

# print(upper, middle, lower, closed)

plt.plot(upper)
plt.plot(middle)
plt.plot(lower)
plt.plot(closed)
plt.grid()
plt.show()

quote_ctx.close()