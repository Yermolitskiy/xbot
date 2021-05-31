import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

"""
above you can see the libraries, that I often used in my trading bots.
please use google search in order to find details on how to install them.

In this code, I'm not using talib and numpy.

Also the config file consists of my API key data, is not here as well. please use your own, and if you are not going to make any trades,
As I do here, just for educational purposes, we don't need it. The data will be loaded from the public web socket.
"""


SOCKET="wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

TRADE_SYMBOL = 'ETHUSDT'
TRADE_QUANTITY = 0.025


# parameters for the Periods and a total length of the list:
LIST_LENGTH = 9
PERIODOS=3

# "Total", empty lists generated:
highs=[]
lows=[]
closes=[]
opens=[]
volumes=[]
in_position = False
price = 0
take_profit = 0

#Generated lists for the system

list_of_closes=[]
list_of_opens=[]
list_of_highs=[]
list_of_lows=[]
list_of_volumes=[]

#Lists with counts:

period_range_list=[]
period_close_list=[]
period_open_list=[]
period_low_list=[]
period_high_list=[]
period_middle_list=[]

period_list_of_volumes=[]
period_top_tail_range=[]
period_tail_range=[]
period_body_range=[]

# this is used for executing trades, but you can remove this line in order to see how it collect info and works with it.
client = Client(config.API_KEY, config.API_SECRET) #tld='us'

# Function that we use, to shorten the lists.
def shorten(lst,max_len):
    while len(lst)>max_len:
        lst.pop(0)
# function that we use for a "Total" list
def sort_return_low(lst):
    if len(lst)==LIST_LENGTH:
        elem = min(lst)
    else:
        elem = float(0)
    return elem

#Only if you are executing orders, order function:
def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)

    except Exception as e:
        print("an exception occured = {}".format(e))
        return False

    return True

def newlen(lst_lngth,period):
    len = int(float(lst_lngth)/float(period))
    return len

# Collection of nested lists(periods, that we work with)
def new_collection(lst_orig,lst_generated):

    close_col={}
    if int(len(lst_orig))==int(LIST_LENGTH):
        for i in range(PERIODOS):
            close_col[i]=lst_orig[(int(newlen(LIST_LENGTH,PERIODOS)*i)):(int(newlen(LIST_LENGTH,PERIODOS)*(i+1)))]
            lst_generated.append(close_col[i])
            shorten(lst_generated,PERIODOS)
        else:
            pass
# taking a needed price data from the periods:
def new_period_collection(lst_orig,lst_generated,function):
    for i in lst_orig:
        lis=function(i)
        lst_generated.append(lis)
        shorten(lst_generated,PERIODOS)

def new_oc_collection(lst_orig,lst_generated,position):
    for i in lst_orig:
        lis=(i)[position]
        lst_generated.append(lis)
        shorten(lst_generated,PERIODOS)
# defining a price range within a periods
def period_range_lists(lst_one,lst_two):
    if lst_one:
        for i in range(PERIODOS):
            elem = float(lst_one[i])-float(lst_two[i])
            period_range_list.append(elem)
            shorten(period_range_list,PERIODOS)
    else:
        pass

# function to find a top tail size
def period_toptail_range():
    if period_open_list:
        for i in range(PERIODOS):
            if period_open_list[i]>period_close_list[i]:
                toptail_range=period_high_list[i]-period_open_list[i]
            else:
                toptail_range=period_high_list[i]-period_close_list[i]
            period_top_tail_range.append(toptail_range)
            shorten(period_top_tail_range,PERIODOS)
    else:
        pass

# function to find a tail size
def period_tailf_range():
    if period_open_list:
        for i in range(PERIODOS):
            if period_open_list[i]>period_close_list[i]:
                tail_range=period_close_list[i]-period_low_list[i]
            else:
                tail_range=period_open_list[i]-period_low_list[i]
            period_tail_range.append(tail_range)
            shorten(period_tail_range,PERIODOS)
    else:
        pass
def period_bodyf_range():
    if period_open_list:
        for i in range(PERIODOS):
            if period_open_list[i]>period_close_list[i]:
                body_range=period_open_list[i]-period_close_list[i]
            else:
                body_range=period_close_list[i]-period_open_list[i]
            period_body_range.append(body_range)
            shorten(period_body_range,PERIODOS)
    else:
        pass
def middle_point(lst_low,lst_high):
    for i in range(len(lst_low)):
        mid = (lst_low[i]+lst_high[i])/2
        period_middle_list.append(mid)
        shorten(period_middle_list,PERIODOS)


"""
System logic elements
"""

    #period down, is about list points, that are consecutively  loosing in price
def logic_periods_up(lst):
    k=0
    if len(lst)==PERIODOS:
        if all(lst[i]<lst[i+1] for i in range(len(lst)-1)):
            k = 1
    return k

def logic_periods_down(lst):
    k=0
    if len(lst)==PERIODOS:
        if all((lst[i]>lst[i+1]) for i in range(len(lst)-1)) :
            k = 1
    return k

# bear candles 3 consecutive
def logic_bear_consecutive(lst_cl,lst_op):
    t = 0
    if all((lst_cl[i]<lst_op[i]) for i in range(len(lst_cl))):
        t=1
    return t
# lower tail is longer then upper
def logic_element_tail(lst_l_tail,lst_u_tail):
    t = 0
    if lst_l_tail[-1]<lst_u_tail[-1]:
        t = 1
    return t
# lower tail is longer then the body
def logic_element_btail(lst_l_tail,lst_body_range):
    t = 0
    if lst_l_tail[-1]>lst_body_range[-1]:
        t = 1
    return t
# We can put all the conditions here, with the use of "and" operator, and when condition is met, we can use it as a trigger to open a position.
def entry_complex(lst_cls,lstvol):
    if logic_periods_down(period_middle_list)==1 :
        status = 1
    else:
        status = 0
    return status

#Websocket usage:
def on_open(ws):
    print('opened connection')
def on_close(ws):
    print('closed connection')
def on_message(ws, message):
    global closes, in_position
    print('received message')
    json_message = json.loads(message) #it will take a json string, and it will convert it to python data structure
    pprint.pprint(json_message)
    #Defining variables for the data that we are going to take from API
    candle = json_message['k']
    is_candle_closed = candle['x']
    open = candle['o']
    close = candle['c']
    high = candle['h']
    low = candle['l']
    volume = candle['v']
    range = round(float(high)-float(low),2)





    # We are using only a closing price for our system.
    if is_candle_closed:
        """
        Generating original lists to work with:
        """
        # Appending lists that we have defined earlier.
        print("candle closed at {}".format(close))
        closes.append(float(close))
        shorten(closes,LIST_LENGTH)
        print("candle opened at {}".format(open))
        opens.append(float(open))
        shorten(opens,LIST_LENGTH)
        print("candle high at {}".format(high))
        highs.append(float(high))
        shorten(highs,LIST_LENGTH)
        print("candle low at {}".format(low))
        lows.append(float(low))
        shorten(lows,LIST_LENGTH)
        print("candle volume is {}".format(volume))
        volumes.append(float(volume))
        shorten(volumes,LIST_LENGTH)

        """
        printing original lists:
        """
        print("closes")
        print(closes)
        print("opens")
        print(opens)
        print("highs")
        print(highs)
        print("lows")
        print(lows)
        print("volumes")
        print(volumes)
        """
        Generating lists of periods for calculations
        """
        #Opens:
        new_collection(opens,list_of_opens)
        #Highs:
        new_collection(highs,list_of_highs)
        #lows:
        new_collection(lows,list_of_lows)
        #Closes:
        new_collection(closes,list_of_closes)
        #volumes
        new_collection(volumes,list_of_volumes)


        #Title:
        print("list of lists, for further calculations and analysis:")

        #length:
        print("length of one period:")
        print(newlen(LIST_LENGTH,PERIODOS))

        print("List of opens:")
        print(list_of_opens)

        print("List of highs:")
        print(list_of_highs)

        print("List of lows:")
        print(list_of_lows)

        print("List of closes:")
        print(list_of_closes)

        print("List of volumes:")
        print(list_of_volumes)

        """
        lists of period calculations:
        """
        #title:
        print("List of period calculations:")

        #list of period opens:
        new_oc_collection(list_of_opens,period_open_list,0)
        print("list of period opens: ")
        print(period_open_list)

        #list of period max:
        new_period_collection(list_of_highs,period_high_list,max)
        print("list of period max:")
        print(period_high_list)

        #list of period min:
        new_period_collection(list_of_lows,period_low_list,min)
        print("list of period min:")
        print(period_low_list)

        #list of period closes:
        new_oc_collection(list_of_closes,period_close_list,-1)
        print("list of period closes: ")
        print(period_close_list)

        #list of periods/accumulated volume
        new_period_collection(list_of_volumes,period_list_of_volumes,sum)
        print("list of period volumesums:")
        print(period_list_of_volumes)

        #list of period ranges
        period_range_lists(period_high_list,period_low_list)
        print("Period Range List:")
        print(period_range_list)

        middle_point(period_low_list,period_high_list)
        print("Period Middle Point:")
        print(period_middle_list)

        period_toptail_range()
        print("period top tale range List:")
        print(period_top_tail_range)

        period_tailf_range()
        print("period tale range List:")
        print(period_tail_range)

        period_bodyf_range()
        print("period body range List:")
        print(period_body_range)
        print("")
        # logic_periods_up(period_list_of_volumes)
        print("   !!!   !!!   !!!   time for volume entry logic")
        print(logic_periods_up(period_list_of_volumes))
        print("")
        # logic_periods_down(period_close_list)
        print("!!!   !!!   !!!   time for closes logic")
        print(logic_periods_down(period_close_list))
        print("")
        # logic_periods_down(period_middle_list)
        print("!!! !!! !!! time for midpoint lowering logic")
        print(logic_periods_down(period_middle_list))
        print("")
        print("")
        # logic_element_tail(period_tail_range, period_top_tail_range)
        print("!!!   !!!   !!!   tail is longer then the top tail")
        print(logic_element_tail(period_tail_range, period_top_tail_range))
        print("")

        # logic_element_btail(period_tail_range,period_body_range)
        print("!!!   !!!   !!!   tail is longer then the body")
        print(logic_element_btail(period_tail_range, period_body_range))
        print("")

        # logic_bear_consecutive(period_close_list,period_open_list)
        print("!!!   !!!   !!!   consecutive bearish bars:")
        print(logic_bear_consecutive(period_close_list,period_open_list))
        print("")

        # entry_complex(period_close_list,period_list_of_volumes)
        print("!!!   !!!   !!!   status if the position shall be opened: ")
        print(entry_complex(period_close_list,period_list_of_volumes))
        """
        Trading functionality.
        This is just a sample of the code, please don't use it and comment it out for a training purposes, unless you modify the code your way.
        """
        if float(close)>take_profit:
            if in_position:
                print("Sell!")
                # sell Logic here
                order_succeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                if order_succeded:
                    in_position  = False
            else:
                print("don't have anything to sell") #sell logic here.
        if entry_complex(period_close_list,period_list_of_volumes):
            if in_position:
                print("Already in position")
            else:
                print("Buy! Buy! Buy! Buy!")
                # order logic here
                order_succeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                if order_succeded :
                    in_position = True
                    price = float(close)
                    take_profit = float(close)/float(100)+float(close)
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
