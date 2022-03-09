# %% [markdown]
# ## Retrieveing Data

# %%
import requests
import pandas as pd
import time
import json

CURRENT_TIME = round(time.time() * 1000) 

def jsonToDataFrame(json_resp):
    res = json.loads(json_resp)
    df = pd.DataFrame(res['result'])
    return df

def getSymbols():
    json_resp2 = (requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json())
    for j in range(len(json_resp2['symbols'])):

        print(json_resp2['symbols'][j]['symbol'])

def getKlines(pair,interval,startime,endtime=CURRENT_TIME):
    query = { 
    "symbol":pair, 
    "interval": interval,
    "startTime": startime,
    "endTime": endtime,
    "limit":1000
    
    }
    # Add option for endtime
    
    json_resp = (requests.get("https://fapi.binance.com/fapi/v1/klines",params=query).json())
    df = pd.DataFrame(json_resp)
    return df


# %%
# Binance only gives you 1000 ticks at maximum , with this trick I extend that limit.
def dataExtender(pair,interval,initial_date,end_date): 
    list_of_dfs = []

    if interval == '15m':
        time_low = initial_date
        time_high = initial_date + (900000 *1000)

    elif interval == '1m':
        time_low = initial_date
        time_high = initial_date + (60000 *1000)

    if time_high > end_date:
        return getKlines(pair, interval, initial_date,end_date)

    while time_high < end_date:
        df = getKlines(pair, interval, time_low, time_high)
        list_of_dfs.append(df)
        time_low = time_high
        time_high += (60000 *1000)
    
    df = getKlines(pair, interval, time_low, end_date)
    list_of_dfs.append(df)
    result = pd.concat(list_of_dfs)
    
    return result
    

# %% [markdown]
# ## Data Cleaning Aux

# %%
def dateToEpoch(date):
    a = date.split('/')
    timestamp = datetime(int('20' + a[2]),int(a[1]),int(a[0]),0,0).timestamp()
    return int(timestamp * 1000)

def epochToDate(epoch):
    # from datetime import datetime
    # print(datetime.fromtimestamp(int("1518308894652")/1000))
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(epoch/1000))

def timestampToDay(epoch):
    day = time.strftime('%A', time.localtime(epoch))
    return day

def dayDf(date):
    # Use only with month and day. Ex: (04-20)
    temp_list = []
    for j in range(len(df) - 1):
        if date in df['open_time'].iloc[j]:
            temp_list.append(df.iloc[j])

    df = pd.DataFrame(temp_list)
    return df

def timeColumn(df):
    df_list = []
    for j in range(len(df)):
        # df['hour_of_day'].iloc[j] = int(df['open_time'].iloc[j][11:13])
        df_list.append(int(df['open_time'].iloc[j][11:13]))


    return df_list

def typeChanger(df):

    df['open_timestamp'] = df['open_timestamp'].astype('int')
    df['open'] = df['open'].astype('float')
    df['high'] = df['high'].astype('float')
    df['low'] = df['low'].astype('float')
    df['close'] = df['close'].astype('float')
    df['volume'] = df['volume'].astype('float')
    df['number_of_trades'] = df['number_of_trades'].astype('float')

    return df

def vol_amplitude_cat(df):
    vol_amplitude = df['volume'].max() - df['volume'].min()

    bins = [df['volume'].min(), vol_amplitude/4 , vol_amplitude/4*2, vol_amplitude/4*3, df['volume'].max()]
    names = ['Muy Bajo VOL', 'Medio VOL', 'Alto VOL', 'Muy Alto VOL', ]

    df['vol_cat'] = pd.cut(df['volume'], bins, labels=names)

def candleColorColumn(df):
    df['candle_color'] = [0 if df['close'].iloc[j] < df['open'].iloc[j] else 1 for j in range(len(df))]
    df['candle_color_debug'] = ["RED" if df['close'].iloc[j] < df['open'].iloc[j] else "GREEN" for j in range(len(df))]

def open_month_and_year(df):

    result_list = []
    for j in range(len(df)):
        print(df['open_time'].iloc[j][0:4])
        result_list.append(int(df['open_time'].iloc[j][0:4]))

    
    result = pd.concat(result_list,df)

    return result

def tickSize(df):
    df['tick_size'] = df['high'] - df['low']
    df['tick_size_percentage'] = df['tick_size'] * 100 / df['low']

# %% [markdown]
# ## Data Cleaning Main

# %%
def dataCleaning(df):
    columns = {
        0:'open_time',
        6:'close_time',
        1:'open',
        2:'high',
        3:'low',
        4:'close',
        5:'volume',
        8:'number_of_trades'
    }

    df = df.drop(columns=[7,9,10,11])
    df = df.rename(columns = columns)
    
    # df = df.sort_values(by=['time'])
    df['open_timestamp'] = df['open_time']
    df['open_time'] = df['open_time'].apply(epochToDate)
    df['close_time'] = df['close_time'].apply(epochToDate)
    df['day_of_week'] = df['open_timestamp'].apply(timestampToDay) 
    

    # df = open_month_and_year(df)

    first_column = df.pop('close_time')
    # insert column using insert(position,column_name,
    # first_column) function
    df.insert(1, 'close_time', first_column)

    df.insert(2,'hour_of_day', timeColumn(df) )
    # this might not be an optimal approach for large datasets, but for this size it suffices

    # Transforming columns into correct type
    # timeColumn(df)
    typeChanger(df)
    candleColorColumn(df)
    # Sorting
    df = df.sort_values(by=['open_timestamp'])

    return df

# %% [markdown]
# ## Candlestick graph

# %%
import plotly.graph_objects as go

import pandas as pd
from datetime import datetime

def candleGraph(df):
    fig = go.Figure(data=[go.Candlestick(x=df['time'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'])])

    fig.show()

# %%
def dataPipeline(pair,interval,initial_date,end_date,verbose=False):
    if verbose == True:
        print("Retrieving data...")
    df = dataExtender(pair,interval,initial_date, end_date)
    if verbose == True:
        print('Data retrieved succesfully...')
        print('Starting cleaning...')
    df = dataCleaning(df)
    df.reset_index(drop=True ,inplace=True)
    if verbose == True:
        print('Ended cleaning...')
    return df

# %%
def rrrgTick(df):
    df['rrrg'] = [
        1 if 
        df['candle_color'].iloc[j-3] == 0 and 
        df['candle_color'].iloc[j-2] == 0 and 
        df['candle_color'].iloc[j-1] == 0 and 
        df['candle_color'].iloc[j] == 1
        else 0 if
        df['candle_color'].iloc[j-3] == 0 and 
        df['candle_color'].iloc[j-2] == 0 and 
        df['candle_color'].iloc[j-1] == 0 and 
        df['candle_color'].iloc[j] == 0
        else 12
        for j in range(len(df))
        ]

def grrrgTick(df):
    df['grrrg'] = [
        1 if 
        df['candle_color'].iloc[j-4] == 1 and 
        df['candle_color'].iloc[j-3] == 0 and 
        df['candle_color'].iloc[j-2] == 0 and 
        df['candle_color'].iloc[j-1] == 0 and 
        df['candle_color'].iloc[j] == 1
        else 0 if
        df['candle_color'].iloc[j-4] == 1 and 
        df['candle_color'].iloc[j-3] == 0 and 
        df['candle_color'].iloc[j-2] == 0 and 
        df['candle_color'].iloc[j-1] == 0 and 
        df['candle_color'].iloc[j] == 0
        else 12
        for j in range(len(df))
        ]

def rrrTick(df):
    df['rrr'] = [
        1 if 
        df['candle_color'].iloc[j-2] == 0 and 
        df['candle_color'].iloc[j-1] == 0 and 
        df['candle_color'].iloc[j] == 0
        else 0
        for j in range(len(df))
        ]

# %%
def strat1Earnings(df,pattern,initial_balance,verbose=False):
    
    rrrTick(df)

    winable_amount = 1
    winable_percent = 0
    balance = initial_balance
    fee = 0.03
    winners = 0
    loosers = 0
    operation_list = []

    for j in range(len(df)):
        
        if df[pattern].iloc[j-1] == 1 and df[pattern].iloc[j-2] != 1:
            #print(df['open_time'].iloc[j-1])
            # print(winable_percent)
            # print((df['close'].iloc[j] - df['open'].iloc[j]) * 100 / (df['open'].iloc[j])
            round_percent_delta = (df['close'].iloc[j] - df['open'].iloc[j]) * 100 / (df['open'].iloc[j])
            balance += (balance * round_percent_delta / 100) - fee
            
            if round_percent_delta > 0:
                winners += 1
                operation_list.append(('WINNER --- Compra: {} en fecha: {}'.format(df['close'].iloc[j-2],df['open_time'].iloc[j-2]), 'Venta: {} en fecha: {}'.format(df['close'].iloc[j],df['open_time'].iloc[j])))
                # print(df['open_time'].iloc[j-2] , 'WINNER')

            else:
                # print(df['open_time'].iloc[j-2] , 'LOOSER')
                loosers += 1
                operation_list.append(('LOOSER --- Compra: {}'.format(df['close'].iloc[j-2]), 'Venta: {}'.format(df['close'].iloc[j])))
                
    percentage = balance * 100 / initial_balance - 100
        
    winrate = winners / (winners + loosers) * 100
    
    result = [balance - initial_balance, percentage]
    
    if verbose == True:
        print("Pattern: " + pattern)
        print("DF has: {} elements".format(len(df)))
        print("Winners: {} --- Loosers: {} --- Winrate: {}".format(winners,loosers, winrate))
        print("Initial Balance: {} --- End Balance: {} -- Percentage: {} ".format(initial_balance, balance, percentage))     

    return result

def strat2Earnings(df,pattern,initial_balance,verbose=False):
    
    rrrTick(df)
    
    winable_amount = 1
    winable_percent = 0
    balance = initial_balance
    winners = 0
    loosers = 0
    fee = 0.03

    operation_list = []

    for j in range(len(df)):
        
        if df[pattern].iloc[j-2] == 1 and df[pattern].iloc[j-3] != 1:
            # print(winable_percent)
            # print((df['close'].iloc[j] - df['open'].iloc[j]) * 100 / (df['open'].iloc[j])
            round_percent_delta = (df['close'].iloc[j] - df['close'].iloc[j-2]) * 100 / (df['open'].iloc[j])
            balance += (balance * round_percent_delta / 100 ) - fee

            if round_percent_delta > 0:
                winners += 1
                operation_list.append(('WINNER --- Compra: {} en fecha: {}'.format(df['close'].iloc[j-2],df['open_time'].iloc[j-2]), 'Venta: {} en fecha: {}'.format(df['close'].iloc[j],df['open_time'].iloc[j])))
                # print(df['open_time'].iloc[j-2] , 'WINNER')

            else:
                # print(df['open_time'].iloc[j-2] , 'LOOSER')
                loosers += 1
                operation_list.append(('LOOSER --- Compra: {}'.format(df['close'].iloc[j-2]), 'Venta: {}'.format(df['close'].iloc[j])))

    percentage = round(balance * 100 / initial_balance - 100)
    
    winrate = winners / (winners + loosers) * 100
    
    result = [balance - initial_balance, percentage]

    if verbose == True:  
        print("Pattern: " + pattern)
        print("DF has: {} elements".format(len(df)))  
        print("Winners: {} --- Loosers: {} --- Winrate: {}".format(winners,loosers, winrate))
        print("Initial Balance: {} --- End Balance: {} -- Percentage: {} ".format(initial_balance, balance, percentage))     

    return result, operation_list

# %%
def stratsSimulator(initial_date,end_date):
    # initial_date = dateToEpoch("1/1/22")
    # end_date = dateToEpoch("1/3/22")

    initial_date = dateToEpoch(initial_date)
    end_date = dateToEpoch(end_date)

    result_15m = dataPipeline("LUNAUSDT",'15m',initial_date,end_date)
    result_1m = dataPipeline("LUNAUSDT",'1m',initial_date,end_date)

    data_list_1, op_list_1 = strat1Earnings(result_15m,'rrr',1000)
    data_list_2, op_list_2 = strat1Earnings(result_1m,'rrr',1000)
    data_list_3, op_list_3 = strat2Earnings(result_15m,'rrr',1000)
    data_list_4, op_list_4 = strat2Earnings(result_1m,'rrr',1000)

    print("Strat 1: 15m ", data_list_1)
    print("Strat 1: 1m ", data_list_2)
    print("Strat 2: 15m ", data_list_3)
    print("Strat 2: 1m ", data_list_4)
