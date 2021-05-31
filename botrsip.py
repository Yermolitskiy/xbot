import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET="wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

TRADE_SYMBOL = 'ETHUSDT'
TRADE_QUANTITY = 0.025

"""
RSI SETTINGS
"""
RSI_PERIOD = 3
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

"""
ADX settings
"""
ADX_PERIOD = 14 #14

"""
Kama settings
"""
KAMA1_PERIOD = 3 #12
KAMA2_PERIOD = 3 #24


"""
Stochastic Settings:
"""
SLOWK_OVERBOUGHT = 80
SLOWK_OVERSOLD = 20

FASTK_PERIOD = 14
SLOWK_PERIOD = 3
SLOWK_MATYPE = 0
SLOWD_PERIOD = 3
SLOWD_MATYPE = 0

MAXIMUM = max(RSI_PERIOD, KAMA1_PERIOD, KAMA2_PERIOD, ADX_PERIOD, FASTK_PERIOD, SLOWK_PERIOD, SLOWD_PERIOD)


highs=[]
lows=[]
closes=[]
in_position = False

client = Client(config.API_KEY, config.API_SECRET) #tld='us'
# candles = client.get_klines(symbol=TRADE_SYMBOL, interval=KLINE_INTERVAL_1MINUTE)
# print("len:")
# print(len(candles))
# print("candlesticks:")
#
# for candlestick in candles:
#     print(candlestick)


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)

    except Exception as e:
        print("an exception occured = {}".format(e))
        return False

    return True

def on_open(ws):
    print('opened connection')
def on_close(ws):
    print('closed connection')
def on_message(ws, message):
    global closes, in_position
    print('received message')
    json_message = json.loads(message) #it will take a json string, and it will convert it to python data structure
    pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("candle high at {}".format(high))
        highs.append(float(high))
        print("candle low at {}".format(low))
        lows.append(float(low))
        print("closes")
        print(closes)
        print("highs")
        print(highs)
        print("lows")
        print(lows)

        if len(closes) > MAXIMUM:
            np_closes = numpy.array(closes)
            np_highs = numpy.array(highs)
            np_lows = numpy.array(lows)
            # rsi = talib.RSI(np_closes, RSI_PERIOD)
            adx = talib.ADX(np_highs, np_lows, np_closes, ADX_PERIOD)
            slowk, slowd = talib.STOCH(np_highs, np_lows, np_closes, fastk_period=FASTK_PERIOD, slowk_period=SLOWK_PERIOD, slowk_matype=SLOWK_MATYPE, slowd_period=SLOWD_PERIOD, slowd_matype=SLOWD_MATYPE)

            kama1 = talib.KAMA(np_closes, KAMA1_PERIOD)
            kama2 = talib.KAMA(np_closes, KAMA2_PERIOD)
            # print("all RSis calculated so far")
            # print(rsi)
            # print("all kama1 calculated so far")
            # print(kama1)
            # print("all kama2 calculated so far")
            # print(kama2)
            print("all adx calculated so far")
            print(adx)
            print("all slowk calculated so far")
            print(slowk)
            print("all slowd calculated so far")
            print(slowd)
            # last_kama1 = kama1[-1]
            # last_kama2 = kama2[-1]
            # last_rsi = rsi[-1]
            last_slowk = slowk[-1]
            prelast_slowk = slowk[-2]

            # print("the current rsi is {}".format(last_rsi))
            # print("the current kama1 is {}".format(last_kama1))
            last_adx = adx[-1]
            prelast_adx = adx[-2]
            print("the current adx is {}".format(last_adx))
            print("the previous adx is {}".format(prelast_adx))
            print("the current slowk is {}".format(last_slowk))

            """
            We have all the data that we need.
            Here's a strategy logic:

            1. When slowk > SLOWK_OVERBOUGHT and adx[-1]<adx[-2] - sell signal
            2. When slowk < SLOWK_OVERSOLD and adx[-1]>adx[-2] - buy signal
            """

            if last_slowk<SLOWK_OVERBOUGHT and prelast_slowk>SLOWK_OVERBOUGHT and last_adx>prelast_adx: #last_rsi > RSI_OVERBOUGHT
                if in_position:
                    print("Overbought! Sell! Sell! Sell! Sell!")
                    # Put Binance sell Logic here
                    order_succeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeded:
                        in_position  = False
                else:
                    print("We don't have it so nothing to do here") # or sell logic here.
            if prelast_slowk<SLOWK_OVERSOLD and last_slowk>SLOWK_OVERSOLD and last_adx>prelast_adx: #last_rsi < RSI_OVERSOLD
                if in_position:
                    print("It's oversold, but you already own it, nothing to do!")
                else:
                    print("Buy! Buy! Buy! Buy!")
                    # put binance order logic here
                    order_succeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeded :
                        in_position = True
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
