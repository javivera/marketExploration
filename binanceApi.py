# %% [markdown]
# ## Retrieveing Data

# %%
import requests
import pandas as pd
import time
import json

CURRENT_TIME = round(time.time() * 1000) 

def dateToEpoch(date):
    a = date.split('/')
    timestamp = datetime(int('20' + a[2]),int(a[1]),int(a[0]),0,0).timestamp()
    return int(timestamp * 1000)

def epochToDate(epoch):
    # from datetime import datetime
    # print(datetime.fromtimestamp(int("1518308894652")/1000))
    return time.strftime('%Y-%m-%d %H:%M',time.localtime(epoch/1000))

def jsonToDataFrame(json_resp):
    res = json.loads(json_resp)
    df = pd.DataFrame(res['result'])
    return df

def getSymbols():
    json_resp2 = (requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json())
    for j in range(len(json_resp2['symbols'])):

        print(json_resp2['symbols'][j]['symbol'])

def getKlines(pair,interval,startime,endtime='0'):
    query = { 
    "symbol":pair, 
    "interval": interval,
    "startTime": 1646017200000,
    
    }
    json_resp = (requests.get("https://fapi.binance.com/fapi/v1/klines",params=query).json())
    df = pd.DataFrame(json_resp, dtype='float64')
    return df


# %% [markdown]
# ## Cleaning Data

# %%
def dataCleaning(df):
    columns = {
        0:'time',
        1:'open',
        2:'high',
        3:'low',
        4:'close',
        5:'volume',
        6:'close_time',
        8:'number_of_trades'
    }

    df = df.drop(columns=[7,9,10,11])

    df[0] = df[0].apply(epochToDate)

    df = df.rename(columns = columns)
    df.tail()
    
    return df

# %%
def dataPipeline():
    df = getKlines('LUNAUSDT','15m',1646017200000)
    df = dataCleaning(df)
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

# candleGraph(df)

# %%


# df['close'].rolling(5).mean()
# print(df['volume'].max())

# df['volume'].mean()



# %%


# %%



