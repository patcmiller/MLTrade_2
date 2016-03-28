
import pandas as pd
import numpy as np
import datetime as dt
import os
from util import get_data, plot_data

def compute_portvals(orders_file = "./orders/orders.csv", start_val = 1000000):

    orders_df= pd.read_csv(orders_file, index_col='Date', parse_dates=True, na_values=['nan'])  
    orders_df.sort_index(inplace=True)
    orders_df.index= pd.DatetimeIndex(orders_df.index).normalize()  
    
    sd= orders_df.index[0]
    ed= orders_df.index[-1]
    syms= pd.unique(orders_df.Symbol.ravel()).tolist()
    syms2= list(syms)
    syms2.append('$SPX')
    allocs= [0]*len(syms)

    # Read in adjusted closing prices for given symbols, date range
    dates = pd.date_range(sd, ed)
    prices_all = get_data(syms2, dates, addSPY=True)
    prices = prices_all[syms]  # only portfolio symbols

    portvals= pd.DataFrame(prices.index, columns=['Date'])
    portvals.index= portvals['Date']
    portvals.rename(columns={'Date':'Portfolio Value'}, inplace=True)
    portvals['Portfolio Value']= 0.0
    portvals.index= pd.DatetimeIndex(portvals.index).normalize()

    df_row_count= -1
    for i, row in prices.iterrows():
        values= (prices.ix[i]).tolist()
       	
        if i in orders_df.index:
            sv= start_val
            al= list(allocs)

            for a in range(orders_df.index.value_counts()[i]):
                df_row_count+= 1

                r= orders_df.ix[df_row_count]
                sym= r['Symbol']
                buy_sell= r['Order']
                shares= r['Shares']

                val= (prices.ix[i])[sym]
                allocs_index= syms.index(sym)
	
                if buy_sell=='BUY':
                    al[allocs_index]+= shares
                    sv-= shares*val
		
                elif buy_sell=='SELL':
                    al[allocs_index]-= shares
                    sv+= shares*val
	    
            leverage= (np.sum(np.abs(np.multiply(al, values))))/(np.sum(np.multiply(al, values)) + sv)
            if leverage<= 2.0:
                allocs= al
                start_val= sv
	   	        
        portvals.ix[i]['Portfolio Value']= np.sum(np.multiply(allocs, values)) + start_val

    return portvals

def test_code():
    of = "./orders/orders3.csv"
    sv = 1000000

    # Process orders
    portvals = compute_portvals(orders_file = of, start_val = sv)
    if isinstance(portvals, pd.DataFrame):
        portvals = portvals[portvals.columns[0]] # just get the first column
    else:
        "warning, code did not return a DataFrame"
    
    # Get portfolio stats
    start_date = portvals.index[0]
    end_date = portvals.index[-1]

    sf= 252.0
    rfr= 0.0

    # GET PORTFOLIO VALUES
    port_val= (portvals[:]).copy()
    daily_returns= port_val.copy()
    daily_returns[1:]= (port_val[1:]/port_val[0:-1].values)-1
    daily_returns[0]= 0  

    avg_daily_ret= daily_returns[1:].mean()
    cum_ret= (port_val[-1]/ port_val[0]) - 1
    std_daily_ret= daily_returns[1:].std()

    sharpe_ratio= np.sqrt(sf)*(avg_daily_ret-rfr)/std_daily_ret


    # GET $SPX VALUES
    dates = pd.date_range(start_date, end_date)
    SPX= get_data(['$SPX'], dates, addSPY=True)
    SPX= SPX['$SPX']
    
    port_val= (SPX[:]).copy()
    daily_returns= port_val.copy()
    daily_returns[1:]= (port_val[1:]/port_val[0:-1].values)-1
    daily_returns[0]= 0  

    avg_daily_ret_SPY= daily_returns[1:].mean()
    cum_ret_SPY= (port_val[-1]/ port_val[0]) - 1
    std_daily_ret_SPY= daily_returns[1:].std()

    sharpe_ratio_SPY= np.sqrt(sf)*(avg_daily_ret_SPY-rfr)/std_daily_ret_SPY

    # Compare portfolio against $SPX
    print "Date Range: {} to {}".format(start_date, end_date)
    print
    print "Sharpe Ratio of Fund: {}".format(sharpe_ratio)
    print "Sharpe Ratio of SPY : {}".format(sharpe_ratio_SPY)
    print
    print "Cumulative Return of Fund: {}".format(cum_ret)
    print "Cumulative Return of SPY : {}".format(cum_ret_SPY)
    print
    print "Standard Deviation of Fund: {}".format(std_daily_ret)
    print "Standard Deviation of SPY : {}".format(std_daily_ret_SPY)
    print
    print "Average Daily Return of Fund: {}".format(avg_daily_ret)
    print "Average Daily Return of SPY : {}".format(avg_daily_ret_SPY)
    print
    print "Final Portfolio Value: {}".format(portvals[-1])

if __name__ == "__main__":
    test_code()
