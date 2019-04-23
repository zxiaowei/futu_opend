
import requests
import json
import pandas as pd

ipPort = "http://127.0.0.1:5000"



def connect():
    url = ipPort + "/connect"
    header = {"accept": "application/json", "Content-Type":"application/json"}
    resp = requests.post(url, headers=header, json={"accountId":"20155562"})
    print (resp.text)

def position():
    url = ipPort + "/position"
    header = {"accept": "application/json", "Content-Type":"application/json"}

    resp = requests.post(url, headers=header, json={"accountId":"20155562"})
    df = pd.read_json(resp.text)
    print (df)

def account():
    url = ipPort + "/account"
    header = {"accept": "application/json", "Content-Type":"application/json"}

    resp = requests.post(url, headers=header,json={"accountId":"20155562"})
    df = pd.read_json(resp.text)
    print (df)


def buy():
    url = ipPort + "/sendorder"
    header = {"accept": "application/json", "Content-Type":"application/json"}
    resp = requests.post(url, headers=header,json={"accountId":"20155562", "symbol":"600839", "volume":500, "price":1.03, "tradeDirection":"BUY"})
    respJson = json.loads(resp.text)
    print (respJson)

def sell(symbol, price, volume):
    url = ipPort + "/sendorder"
    header = {"accept": "application/json", "Content-Type":"application/json"}
    resp = requests.post(url, headers=header,json={"accountId":"20155562", "symbol":symbol,"volume":volume, "price":price, "tradeDirection":"SELL"})
    respJson = json.loads(resp.text)
    print (respJson)
    return respJson["orderId"]

def cancelOrder(orderId, symbol):
    url = ipPort + "/cancelorder"
    header = {"accept": "application/json", "Content-Type":"application/json"}
    resp = requests.post(url, headers=header,json={"accountId":"20155562", "symbol":symbol,"orderId":orderId})
    respJson = json.loads(resp.text)
    print (respJson)

def queryOrderStat(orderId,symbol):
    url = ipPort + "/queryOrderState"
    header = {"accept": "application/json", "Content-Type":"application/json"}
    resp = requests.post(url, headers=header,json={"accountId":"20155562", "symbol":symbol,"orderId":orderId})
    respJson = json.loads(resp.text)
    print (respJson)

if __name__ == "__main__":

    symbol = "602421"

    connect()
    # position()
    # account()
    # buy()
    orderId = sell(symbol, 10.18, 100)
    # queryOrderStat(orderId,symbol)
    # cancelOrder(orderId,symbol )