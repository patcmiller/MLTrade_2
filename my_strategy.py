
import pandas as pd
import numpy as np
import datetime as dt
import os
import matplotlib.pyplot as plt

#############################
## START: HELPER FUNCTIONS ##
def symbol_to_path(symbol, base_dir=os.path.join("..", "data")):
    """Return CSV file path given ticker symbol."""
    return os.path.join(base_dir, "{}.csv".format(str(symbol)))

def get_data(symbols, dates, addSPY=True):
    """Read stock data (adjusted close) for given symbols from CSV files."""
    df = pd.DataFrame(index=dates)
    if addSPY and 'SPY' not in symbols:  # add SPY for reference, if absent
        symbols = ['SPY'] + symbols

    for symbol in symbols:
        df_temp = pd.read_csv(symbol_to_path(symbol), index_col='Date',
                parse_dates=True, usecols=['Date', 'Adj Close'], na_values=['nan'])
        df_temp = df_temp.rename(columns={'Adj Close': symbol})
        df = df.join(df_temp)
        if symbol == 'SPY':  # drop dates SPY did not trade
            df = df.dropna(subset=["SPY"])

    return df

def plot_data(df, title="Stock prices", xlabel="Date", ylabel="Price"):
    """Plot stock prices with a custom title and meaningful axis labels."""
    ax = df.plot(title=title, fontsize=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.show()
## END: HELPER FUNCTIONS ##
###########################

###################################
## GENERATE BOLLINGER BAND CHART ##
def BB_Chart(IBM, SMA, H, L, longs, shorts, BB_Graph):
	if not BB_Graph:
		return None

	BB= pd.concat([H,L],axis=1)
	df= pd.concat([IBM, SMA, BB], axis=1)      
	ax= df.plot(title='Bollinger Band Strategy', color=['blue','gold','teal','teal'])
	ax.set_xlabel('Date')
	ax.set_ylabel('Price')
	lines, trash= ax.get_legend_handles_labels()
	ax.legend(lines, ['IBM','SMA','Bollinger Bands'], loc='best')

	n=0	
	for a in longs:
		if n==0:
			ax.axvline(a,color='g')
			n=1
		else:
			ax.axvline(a,color='k')
			n=0
	n=0
	for a in shorts:
		if n==0:
			ax.axvline(a,color='r')
			n=1
		else:
			ax.axvline(a,color='k')
			n=0
		
	plt.savefig('My_Strategy.png')
	return None
## END: BOLLINGER BAND CHART ##
###############################

## GENERATE SPY CHART ##
def SPX_Chart(orders, end_date, SPX_Graph):

    start_value = 10000
    start_date = orders[0][0]
    dates = pd.date_range(start_date, end_date)
    sf= 252.0
    rfr= 0.0
 
    # GET PORTFOLIO VALUES
    IBM= get_data(['IBM'], dates, addSPY=True)
    IBM= IBM['IBM']

    port_val= IBM.copy()
    stock= 0
    for d in IBM.index:
	k= d.to_datetime().strftime('%Y-%m-%d')
	if k in orders:
	    o= orders[np.where(orders[:,0]==k)][0,2]
	    if o=='SELL':
	    	stock-= 100
		start_value= start_value + IBM[d]*100
	    elif o=='BUY':
		stock+= 100
		start_value= start_value - IBM[d]*100
	if stock!=0:        
		port_val[d]=start_value + IBM[d]*stock
	else:	
		port_val[d]=start_value
    port_val[-1]= start_value + IBM[d]*stock
    
    daily_returns= port_val.copy()
    daily_returns[1:]= (port_val[1:]/port_val[0:-1].values)-1
    daily_returns[0]= 0  

    avg_daily_ret= daily_returns[1:].mean()
    cum_ret= (port_val[-1]/ port_val[0]) - 1
    std_daily_ret= daily_returns[1:].std()

    sharpe_ratio= np.sqrt(sf)*(avg_daily_ret-rfr)/std_daily_ret
    
    # GET $SPX VALUES
    SPX= get_data(['$SPX'], dates, addSPY=True)
    SPX= SPX['$SPX']
    port_val2= (SPX[:]).copy()
    daily_returns2= port_val2.copy()
    daily_returns2[1:]= (port_val2[1:]/port_val2[0:-1].values)-1
    daily_returns2[0]= 0  

    avg_daily_ret_SPY= daily_returns2[1:].mean()
    cum_ret_SPY= (port_val2[-1]/ port_val[0]) - 1
    std_daily_ret_SPY= daily_returns2[1:].std()

    sharpe_ratio_SPY= np.sqrt(sf)*(avg_daily_ret_SPY-rfr)/std_daily_ret_SPY

    # Compare portfolio against $SPX
    print "Date Range: {} to {}".format(start_date, end_date)
    print
    print "Sharpe Ratio of Fund: {}".format(sharpe_ratio)
    print "Sharpe Ratio of $SPX : {}".format(sharpe_ratio_SPY)
    print
    print "Cumulative Return of Fund: {}".format(cum_ret)
    print "Cumulative Return of SPX : {}".format(cum_ret_SPY)
    print
    print "Standard Deviation of Fund: {}".format(std_daily_ret)
    print "Standard Deviation of SPX : {}".format(std_daily_ret_SPY)
    print
    print "Average Daily Return of Fund: {}".format(avg_daily_ret)
    print "Average Daily Return of SPX : {}".format(avg_daily_ret_SPY)
    print
    print "Final Portfolio Value: {}".format(port_val[-1])
    
    if not SPX_Graph:
	return None
    
    df_temp = pd.concat([port_val/port_val.ix[0,:], port_val2/port_val2.ix[0,:]], keys=['Portfolio', 'SPY'], axis=1)      
    ax= df_temp.plot(title='Daily Portfolio Value and $SPX')
    ax.set_xlabel('Date')
    ax.set_ylabel('Normalized Price')
    plt.savefig('MY_SPX.png')
    return None
## END: SPY CHART ##
####################

## LOCATE STOCK LOCATION ##
def stock_location(M,SMA,H,L):
	if M<= SMA and M<= L:
		v_loc= 0
	elif M<= SMA and M>= L:
		v_loc= 1
	elif M>= SMA and M<= H:
		v_loc= 2
	elif M>= SMA and M>= H:
		v_loc= 3
	return v_loc

################################
## COMPUTE BOLLINGER STRATEGY ##
def compute_bollinger_strategy(start_date, end_date, val, BB_Graph, SPX_Graph, stocks= 100):

	syms= ['IBM']
    	# Read in adjusted closing prices for IBM and SPX in date range
	dates = pd.date_range(start_date, end_date)
	prices_all = get_data(syms, dates, addSPY=True)
	IBM = prices_all[syms]  # only IBM

	SPX= get_data(['$SPX'], dates, addSPY=True)
	SPX= SPX['$SPX'] # only SPX
    
	# Compute Rolling mean of last 20 prices, rolling std, and Bollinger Bands
	SMA= pd.rolling_mean(IBM,20)
	SMA= SMA.ix[19:]
	std_20= pd.rolling_std(IBM,20)
	std_20= std_20.ix[19:]	

	BB_High= SMA + 2* std_20
	BB_Low= SMA - 2* std_20

	# v_loc=
	# 0: below SMA, below BB_Low
	# 1: below SMA, above BB_Low
	# 2: above SMA, below BB_High
	# 3: above SMA, above BB_High

	M= IBM[19:]
	Y= SPX[19:]
	longs= []
	shorts= []
	has_stock= 0
	v_loc= [None,None]
	v_loc[1]= stock_location(M.ix[0].values,SMA.ix[0].values,BB_High.ix[0].values,BB_Low.ix[0].values)
	short_or_long= 0
	orders= np.asarray(['Date', 'Symbol', 'Order', 'Shares'])
	stop=0
	
	for i in range(1,len(SMA)):
		v_loc[0]= v_loc[1]
		v_loc[1]= stock_location(M.ix[i].values,SMA.ix[i].values,BB_High.ix[i].values,BB_Low.ix[i].values)

		if v_loc[0]-v_loc[1]== 0:
			continue
		
		if v_loc[0]==0 and v_loc[1]==1 and has_stock==0:
			if short_or_long:
				shorts.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
				short_or_long=0
				has_stock= 0
			else:
				longs.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
				has_stock= 1
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'BUY', 100]))
		if (v_loc[0]==0 or v_loc[0]==1) and (v_loc[1]==2 or v_loc[1]==3) and has_stock==1:
			longs.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
			has_stock= 0
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'SELL', 100]))

		if v_loc[0]==3 and v_loc[1]==2 and has_stock==0:
			if short_or_long:
				longs.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
				short_or_long=0
				has_stock= 0
			else:
				shorts.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
				has_stock= 1
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'SELL', 100]))
		if (v_loc[0]==3 or v_loc[0]==2) and (v_loc[1]==0 or v_loc[1]== 1) and has_stock==1:
			shorts.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
			has_stock= 0
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'BUY', 100]))

		if (Y.ix[i] > BB_High.ix[i].values) and has_stock==0 and short_or_long==0:
			longs.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
			short_or_long= 1
			has_stock= 1
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'BUY', 100]))
			stop= IBM.ix[i].values
		if (Y.ix[i] > BB_High.ix[i].values) and has_stock==1 and M.ix[i].values < stop*0.85:
			longs.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
			has_stock= 0
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'SELL', 100]))

		if Y.ix[i] < BB_Low.ix[i].values and has_stock==0 and short_or_long==0:
			shorts.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
			short_or_long= 1
			has_stock= 1
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'SELL', 100]))
			stop= IBM.ix[i].values
		if Y.ix[i] < BB_Low.ix[i].values and has_stock==1 and M.ix[i].values > stop*1.15:
			shorts.append(M.index[i].to_datetime().strftime('%Y-%m-%d'))
			has_stock= 0
			orders= np.vstack((orders, [M.index[i].to_datetime().strftime('%Y-%m-%d'), 'IBM', 'BUY', 100]))

	orders= orders[1:]
	np.savetxt('my_orders.csv', orders, delimiter=',', fmt='%s')
	BB_Chart(IBM, SMA, BB_High, BB_Low, longs, shorts, BB_Graph)
	SPX_Chart(orders, end_date, SPX_Graph)	

	return None
## END: COMPUTE BOLLINGER STRATEGY ##
#####################################

#######################
## THE MAIN FUNCTION ##
def main():

    start_value = 10000
    start_date = dt.datetime(2007,12,29)
    end_date = dt.datetime(2009,12,29)

    BB_Graph= True
    SPX_Graph= True
    compute_bollinger_strategy(start_date, end_date, start_value, BB_Graph, SPX_Graph)
	
if __name__ == "__main__":
    main()
