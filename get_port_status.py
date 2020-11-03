import pandas as pd
import datetime
import sys
import getopt
import traceback
import json
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

# update this to read from .xml
def get_config(file):
  with open(file) as f:
    return f.readlines()[0]

def get_latest_quotes(data):
  parameters = {'start':'1','limit':'100','convert':'USD'}
  headers = {'Accepts': 'application/json','X-CMC_PRO_API_KEY': data,}
  session = Session()
  session.headers.update(headers)

  try:
    response = session.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest', params=parameters)
    data = json.loads(response.text)
    return data
  except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)

def main(argv):
  if len(argv)==4:  
    try:
      (opts,args)=getopt.getopt(argv,"hi:c:")
    except:
      usage()
      sys.exit(1)

    input=""
    config=""

    for opt,arg in opts:
      if opt=="-i":
        input=str(arg)
      elif opt=="-c":
        config=str(arg)
      else:
        usage()
        sys.exit(1)

    property=get_config(config)

    tmp=input.split('.')
    extension=tmp[len(tmp)-1]

    if extension=="csv":
      orders=pd.read_csv(input,header=0)
    elif extension=="json":
      print("process json")
    else:
      print("exit program")    
    
    print(orders)
    
    payload=get_latest_quotes(property)
    #credits=payload['status']['credit_count']
    quotes=payload['data']

    # headers: asset, dt, exchange, price, amt, comment
    invested=0
    updates=pd.DataFrame(columns=['set','prev','rent','diff','cents','val'])
    for index, row in orders.iterrows():
      symbol=row[0].upper()
      price=row[3]
      amt=row[4]          
 
      # get asset price -> inefficient (to limit CMC api calls) 
      for quote in quotes:
        if quote['symbol']==symbol:
          cur_price=quote['quote']['USD']['price']
     
      dif=cur_price-price
      percen=(dif/price)*100
      cur_value=amt*cur_price
      updates=updates.append({'set':symbol,'prev':price,'rent':cur_price,'diff':dif,'cents':percen,'val':cur_value}, ignore_index=True)
   
      if pd.isna(price)==False: 
        invested=invested+(price*amt)

    print() 
    print(updates)

    # current_value of portfolio
    total_val=updates.aggregate(['sum'])['val'][0]

    metrics=pd.DataFrame(columns=('set','amt','val','pi'))
    tokens=updates.set.unique()
    for token in tokens:
      tmp_orders=orders.loc[orders['asset']==token]
      total_amt=tmp_orders.aggregate(['sum'])['amt'][0]
  
      tmp_updates=updates.loc[updates['set']==token]      
      asset_val=tmp_updates.aggregate(['sum'])['val'][0]
      
      percentage=asset_val/total_val

      metrics=metrics.append({'set':token,'amt':total_amt,'val':asset_val,'pi':percentage}, ignore_index=True)
      
    print()
    print(metrics)

    print()
    print("invested value: "+str(invested))
    print("portfolio value: "+str(total_val))
  else:
    usage()

def usage():
  print('''Usage: python get_port_status.py -i input -c config''')

if __name__ == "__main__":
  main(sys.argv[1:])
exit()
