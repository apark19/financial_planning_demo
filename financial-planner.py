import os 
import requests
import pandas as pd
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from MCForecastTools import MCSimulation
import datetime
import sys
import getopt
import traceback
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import numpy as np

def main(argv):
    config=""

    (opts,args)=getopt.getopt(argv,"hc:")    
    for opt,arg in opts:
        if opt=="-c":
            config=str(arg)
        else:
            usage()

    if (config==None or config==""):
        print(str(datetime.datetime.utcnow())+"|main|config is invalid, config="+str(config))
        usage()
        sys.exit(1)

    try:
        btc_url="https://api.alternative.me/v2/ticker/Bitcoin/?convert=USD"
        eth_url="https://api.alternative.me/v2/ticker/Ethereum/?convert=USD"

        response_data=requests.get(btc_url).json()
        btc_price=response_data['data']['1']['quotes']['USD']['price']
        my_btc=1.2

        response_data=requests.get(eth_url).json()
        eth_price=response_data['data']['1027']['quotes']['USD']['price']
        my_eth=5.3
 
        btc_sum=btc_price*my_btc
        eth_sum=eth_price*my_eth

        print(str(datetime.datetime.utcnow())+"|main|current BTC holdings: $"+str(btc_sum))
        print(str(datetime.datetime.utcnow())+"|main|current ETH holdings: $"+str(eth_sum))

        if load_dotenv(config)==True:
            spy_amt=200
            agg_amt=50
            alpaca_id=os.getenv("ALPACA_API_ID")
            alpaca_key=os.getenv("ALPACA_API_KEY")

            alp=tradeapi.REST(alpaca_id,alpaca_key,api_version="v2")
            dt_format=pd.Timestamp("2020-10-26",tz="America/New_York").isoformat()
            timeframe="1D"
            tickers=["SPY","AGG"]
 
            alp_frame=alp.get_barset(tickers,timeframe,start=dt_format,end=dt_format).df

            spy_price=float(alp_frame['SPY']['close'])
            agg_price=float(alp_frame['AGG']['close'])

            spy_sum=spy_amt*spy_price
            agg_sum=agg_amt*agg_price

            print(str(datetime.datetime.utcnow())+"|main|current SPY holdings: $"+str(spy_sum))
            print(str(datetime.datetime.utcnow())+"|main|current AGG holdings: $"+str(agg_sum))

            crypto_total=btc_sum+eth_sum
            stock_total=spy_sum+agg_sum
            data=[['crypto',crypto_total],['stock',stock_total]]
            savings_frame=pd.DataFrame(data,columns=['asset_type','dollar_amt'])
            #print(savings_frame)      

            savings_frame.set_index('asset_type',inplace=True)
            #savings_frame.plot.pie(y='dollar_amt',title="Current Savings")
            #plt.show()

            monthly_income=12000
            savings_total=savings_frame['dollar_amt'].sum()
            if (savings_total>(monthly_income*3)):
                print(str(datetime.datetime.utcnow())+"|main|emergency fund threshold has been exceeded")
            elif (savings_total==monthly_income):
                print(str(datetime.datetime.utcnow())+"|main|emergency fund has been reached")
            else:
                diff=(monthly_income*3)-savings_total
                print(str(datetime.datetime.utcnow())+"|main|$"+str(diff)+" more needed for emergency fund")

        start_dt=pd.Timestamp("2015-10-01",tz="America/New_York").isoformat()
        end_dt=pd.Timestamp("2020-10-01",tz="America/New_York").isoformat()
        timeframe="1D"
        tickers=["AGG","SPY"]
        hist_frame=alp.get_barset(tickers,timeframe,start=start_dt,end=end_dt).df
        print(hist_frame)
 
        MC_total=MCSimulation(portfolio_data=hist_frame,weights=[.4,.6],num_simulation=1000,num_trading_days=252*30)
        print(MC_total.calc_cumulative_return())
        #line_plot=MC_total.plot_simulation()
        #plt.show()
        
        #dist_plot=MC_total.plot_distribution()
        #plt.show()
    
        sim_stats=MC_total.summarize_cumulative_return()
        print(sim_stats)
 
        initial_investment=20000
        ci_lower=round(sim_stats[8]*initial_investment,2)
        ci_upper=round(sim_stats[9]*initial_investment,2)
        print(str(datetime.datetime.utcnow())+"""|main|There is a 95% chance that an initial investment of $"""+str(initial_investment)+""" in the porfolio over the next 30 years will end within the range of $"""+str(ci_lower)+"-$"+str(ci_upper))

        initial_investment*=1.5
        ci_lower=round(sim_stats[8]*initial_investment,2)
        ci_upper=round(sim_stats[9]*initial_investment,2)
        print(str(datetime.datetime.utcnow())+"""|main|If the initial investment were increased by 50%, the portfolio over the next 30 years will end within the range of $"""+str(ci_lower)+"-$"+str(ci_upper))

    except:
        traceback.print_exc()
        pass


def usage():
    print("Usage: python financial_planner.py -c env_file")

if __name__=="__main__":
    main(sys.argv[1:])
