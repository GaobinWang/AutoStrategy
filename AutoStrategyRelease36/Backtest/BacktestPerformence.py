# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 18:36:11 2016

###############################################################################
#                                                                             #
#          For the backtest of a series of trading signals(1,0,-1)            #                                                                 
#                                 Zhou, Mao                                   #
#                           Mao (2017) Python Code                            #
#                                Feb 8, 2017                                  #
#                           copy right Mao ZHOU 2017                          #
#                                                                             #
###############################################################################


@author: mao
"""
import pandas as pd
import numpy as np
import os
import scipy as sp
import sys
import math
import datetime
from collections import Counter
from itertools import compress
import sklearn


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    
from AutoStrategy.Feature import features

#importlib.reload(features)
#importlib.reload(cvxopt)



# Prediction Error is to evalute the goodness of fit 
# Prediction is a dataframe with ['Date','yhat']
# Actual is a dataframe with ['Date','y']
class Prediction_Error:
    # will merge actual value with the predicted value using key 'Date'
    def __init__(self,Prediction, Actual):
        self.Prediction=Prediction
        self.Actual=Actual
        self.Prediction['yhat']=self.Prediction['yhat'].astype(float)
        self.Actual['y']=self.Actual['y'].astype(float)
        self.EvalMatrix=self.Prediction.merge(self.Actual, on='Date')
        
    
    # calculate the mse value for prediction and realized value
    def mse(self):
        mse=sklearn.metrics.mean_squared_error(self.EvalMatrix['y'],self.EvalMatrix['yhat'])
        return mse
        





## combine value and date
# mainly to combine value after backtest (either for compound or single)
# the value always start from 1, i.e. the position is the last time point before trading
# however, the date and time is from the first day of trading
# when it's a operation, we use _ to seperate each word, say getdata_RosefinchSQL
# when it's a value, we use Capital Letter to seperate each word 
# date is a numpy array with datetime object in it
# value is a numeric value

class combine_date_value:
    
    def __init__(self,date,value):
         # to omit the first value 1
        try:
            self.value=value[1:].as_matrix()
        except:
            self.value=value[1:]
            print ('value does not need to be convert to numpy array, it is already is! \n')
         
        try:
            self.date=date[:len(self.value)].as_matrix()
        except:
            self.date=date[:len(self.value)]
            print ('dates do not need to be convert to numpy array, it is already is! \n')
        
    def date_and_value(self, include_first=True,colnames=['date','value']):
        if include_first==True:
            Datetime_Op=features.Datetime_Operation()
            PrevDay=Datetime_Op.change_date(self.date[0],target='day',by_n=-1)
            self.date=np.insert(self.date,0,PrevDay)
            self.value=np.insert(self.value,0,1)
            self.datevalue=pd.DataFrame([self.date,self.value]).transpose()
            self.datevalue.columns=colnames
        else:
            self.datevalue=pd.DataFrame([self.date,self.value]).transpose()
            self.datevalue.columns=colnames





    

#date_val=combine_date_value(TimestampSignal.ix[:,0],value)
#date_val.date_and_value(include_first=True)
#compounddata=date_val.datevalue
#simpledata=data




class Returns_calculation:
    
    # returns is a data frame with first row being date, second row being Returns
    def __init__(self,returns):
        self.returns=returns
        self.returns.columns=['Date', 'Returns']
    
    # merge_by_date is to sum over returns of the same date
    def merge_by_date(self):
        MergedReturns=self.returns.groupby(self.returns['Date'])
        MergedReturns=MergedReturns.sum()
        MergedReturns['Date']=MergedReturns.index
        self.returns=MergedReturns
        
    
    # impute_zero_returns is to compare the trade record with the trading dates
    # to find the trading dates with zero returns and fill it in 
    # tradedates are a pandas series
    def impute_zero_returns(self,tradedates):
        if (type(tradedates) is np.ndarray):
            tradedates=tradedates.reshape(len(tradedates),1)
            tradedates=pd.DataFrame(tradedates)
            tradedates.columns=['Date']      
        try:
            self.returns=tradedates.merge(self.returns, on='Date',how='left')
            self.returns=self.returns.fillna(0)     
        except:
            print ('Insert 0 failed \n')
    
    # add up the returns together to calculate the simple returns 
    def returns_to_Simplevalues(self):
        Datetime_Op=features.Datetime_Operation()
        self.SimpleValue=np.cumsum(np.insert(self.returns['Returns'].as_matrix(),0,1))


    # multiply up the returns to get compound values
    def returns_to_Compoundvalues(self):
        Datetime_Op=features.Datetime_Operation()
        self.CompoundValue=np.cumprod(np.insert(self.returns['Returns'].as_matrix()+1,0,1))

        
        
#ReturnsManipulation=Returns_calculation(datevalues) 
#ReturnsManipulation.merge_by_date()
#ReturnsManipulation.impute_zero_returns(tradedates)  
#ReturnsManipulation.returns_to_Simplevalues()


# first column is date
# second column is accumulated value (either simple interest or compound interest)
# the import must be a pandas data frame
class Eval_performance:
    # second column is accumulated value (either simple interest or compound interest)
    # the import must be a pandas data frame
    # simple_interest is for clarifying if the input is in simple interest form
    # if the input data has number of row n
    # then self.date, self.SimpleValue, self.CompoundValue, elf.SimpleDrawback, self.CompoundDrawback
    # all have length=n
    # and self.returns has length n-1 (we don't have returns before trading, correspond to 1 in value)
    def __init__(self, data, simple_interest):
        self.date=data.ix[:,0].as_matrix()
        self.simple_interest=simple_interest
        if self.simple_interest==True:
            self.SimpleValue=data.ix[:,1].as_matrix()
            self.simple_to_compound()
        else:
            self.CompoundValue=data.ix[:,1].as_matrix()
            self.compound_to_simple()
            
        self.drawdown(choice_simple_interest=True)
        self.drawdown(choice_simple_interest=False)
        

    # to calculate the profit or loss for every transactions 
    # return is in percentage
    # simple_interest is for clarifying if the input is in simple interest form
    def calculate_returns(self):
        if self.simple_interest==True:
            self.returns=np.diff(self.SimpleValue)
        else:
            self.returns=np.diff(self.CompoundValue)/self.CompoundValue[0:(len(self.CompoundValue)-1)]
     

       
    # convert a compound interest base to a simple interest base        
    def compound_to_simple(self):
        self.calculate_returns()
        self.SimpleValue=np.cumsum(np.insert(self.returns,0,1))
     
     
    # convert a simple interest base to a compound interest base     
    def simple_to_compound(self):
        self.calculate_returns()
        self.CompoundValue=np.cumprod(np.insert(self.returns+1,0,1))
    
    
    # find the start date of the transaction flow
    # which correspond to the value after 1
    def start_day(self):
        Datetime_Op=features.Datetime_Operation()
        StartDay=Datetime_Op.change_date(min(self.date),target='day',by_n=1)
        return StartDay
     
     
     
    # find the end date of the transaction flow
    def end_day(self):
        return max(self.date)
        
    
    # find returns(profit or loss) from timestamp1 to timestamp2 
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1 
    def select_return(self, timestamp1, timestamp2):
        if pd.Timestamp(timestamp1).date()<self.start_day():
            raise Exception("Please input a date after or equal to " + str(self.start_day()))
            
        if pd.Timestamp(timestamp2).date()>self.end_day():
            raise Exception("Please input a date before or equal to " + str(self.end_day()))
            
        DateIndex=(self.date>=pd.Timestamp(timestamp1).date()) & (self.date<=pd.Timestamp(timestamp2).date())
        
        # this step is to eliminate the date before trading date
        ReturnIndex=DateIndex[1:len(DateIndex)]
        return self.returns[ReturnIndex]


    
    # find Simple Value (accumulated profit or loss, with simple interest) from timestamp1 to timestamp2 
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1     
    def select_SimpleValue(self, timestamp1, timestamp2):
        if pd.Timestamp(timestamp1).date()<min(self.date):
            raise Exception("Please input a date after or equal to" + str(min(self.date)))
            
        if pd.Timestamp(timestamp2).date()>max(self.date):
            raise Exception("Please input a date before or equal to" + str(max(self.date)))
            
        DateIndex=(self.date>=pd.Timestamp(timestamp1).date()) & (self.date<=pd.Timestamp(timestamp2).date())
        return self.SimpleValue[DateIndex]
      
      
      
      
    # find Compound Value (accumulated profit or loss, with compound interest) from timestamp1 to timestamp2 
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1           
    def select_CompoundValue(self, timestamp1, timestamp2):
        if pd.Timestamp(timestamp1).date()<min(self.date):
            raise Exception("Please input a date after or equal to" + str(min(self.date)))
            
        if pd.Timestamp(timestamp2).date()>max(self.date):
            raise Exception("Please input a date before or equal to" + str(max(self.date)))
            
        DateIndex=(self.date>=pd.Timestamp(timestamp1).date()) & (self.date<=pd.Timestamp(timestamp2).date())
        return self.CompoundValue[DateIndex]        
        
        
        
    # find date from timestamp1 to timestamp2 
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1           
    def select_date(self, timestamp1, timestamp2):
        if pd.Timestamp(timestamp1).date()<min(self.date):
            raise Exception("Please input a date after or equal to" + str(min(self.date)))
            
        if pd.Timestamp(timestamp2).date()>max(self.date):
            raise Exception("Please input a date before or equal to" + str(max(self.date)))
            
        DateIndex=(self.date>=pd.Timestamp(timestamp1).date()) & (self.date<=pd.Timestamp(timestamp2).date())
        return self.date[DateIndex]                
        
    
    # calculate the return for every year
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1      
    def Return_by_year(self):
        DateReturn=pd.DataFrame([self.date[1:],self.returns]).transpose()
        DateReturn.columns=['Tradedates','returns']
        
        # convert numpy.float(64) to float(64)
        # otherwise a error will raised when
        # YearlyMeanStd=GroupByYear.agg({'returns':[np.mean,np.std]})
        try:
            DateReturn['returns']=DateReturn['returns'].apply(lambda x:x.item())
        except:
            print ('No need to apply the operation from numpy.float64 to float64!\n')
        
        # create year index and group
        DateReturn['year']=DateReturn['Tradedates'].apply(lambda x:x.year)
        GroupByYear=DateReturn.groupby(DateReturn['year'])
        
        # aggregate returns according to year
        try:
            YearlySum=GroupByYear.agg({'returns':np.sum})
        except:
            EveryYearSum=[]
            for name, group in GroupByYear:
                EveryYearSum.append(np.sum(group['returns']))
            YearlySum=pd.DataFrame(EveryYearSum)
            YearlySum.columns=['returns']
            YearlySum=YearlySum.set_index(DateReturn['year'].unique())
        return YearlySum
    
    
    
    # calculate the sharpe ratio from timestamp1 to timestamp2 
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1 
    def Sharpe_Ratio(self, timestamp1, timestamp2):
        Returns=self.select_return(timestamp1, timestamp2)
        AvgReturn=np.mean(Returns)*np.sqrt(252)
        StdReturn=np.std(Returns)
        return AvgReturn/StdReturn



    # calculate the sharpe ratio for all time period 
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1            
    def Sharpe_Ratio_all(self):
        AvgReturn=np.mean(self.returns)*np.sqrt(252)
        StdReturn=np.std(self.returns)
        return AvgReturn/StdReturn       
        
        
    # calculate the sharpe ratio for every year
    # also return yearly mean and standard deviation for returns
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1            
    def Sharpe_Ratio_by_year(self):
        DateReturn=pd.DataFrame([self.date[1:],self.returns]).transpose()
        DateReturn.columns=['Tradedates','returns']
        
        # convert numpy.float(64) to float(64)
        # otherwise a error will raised when
        # YearlyMeanStd=GroupByYear.agg({'returns':[np.mean,np.std]})
        try:
            DateReturn['returns']=DateReturn['returns'].apply(lambda x:x.item())
        except:
            print ('No need to apply the operation from numpy.float64 to float64!\n')
        
        # create year index and group
        DateReturn['year']=DateReturn['Tradedates'].apply(lambda x:x.year)
        GroupByYear=DateReturn.groupby(DateReturn['year'])
        
        # aggregate returns according to year
        try:
            YearlyMeanStd=GroupByYear.agg({'returns':[np.mean,np.std]})
        except:
            EveryYearMean=[]
            EveryYearStd=[]
            for name, group in GroupByYear:
                EveryYearMean.append(np.mean(group['returns']))
                EveryYearStd.append(np.std(group['returns']))
                
            YearlyMeanStd=pd.DataFrame([EveryYearMean,EveryYearStd]).transpose()
            YearlyMeanStd=YearlyMeanStd.set_index(DateReturn['year'].unique())
        SharpeRatioYearly=YearlyMeanStd.ix[:,0]*np.sqrt(252)/YearlyMeanStd.ix[:,1]
        return [YearlyMeanStd,SharpeRatioYearly]



    def Sharpe_Ratio_by_month(self):
        DateReturn=pd.DataFrame([self.date[1:],self.returns]).transpose()
        DateReturn.columns=['Tradedates','returns']
        
        # convert numpy.float(64) to float(64)
        # otherwise a error will raised when
        # YearlyMeanStd=GroupByYear.agg({'returns':[np.mean,np.std]})
        try:
            DateReturn['returns']=DateReturn['returns'].apply(lambda x:x.item())
        except:
            print ('No need to apply the operation from numpy.float64 to float64!\n')
        
        # create year index and group
        DateReturn['month']=DateReturn['Tradedates'].apply(lambda x:x.month)
        GroupByMonth=DateReturn.groupby(DateReturn['month'])
        
        # aggregate returns according to year 
        try:
            MonthlyMeanStd=GroupByMonth.agg({'returns':[np.mean,np.std]})
        except:
            EveryMonthMean=[]
            EveryMonthStd=[]
            for name, group in GroupByMonth:
                EveryMonthMean.append(np.mean(group['returns']))
                EveryMonthStd.append(np.std(group['returns']))
                
            MonthlyMeanStd=pd.DataFrame([EveryMonthMean,EveryMonthStd]).transpose()
            MonthlyMeanStd=MonthlyMeanStd.set_index(DateReturn['month'].unique())
        SharpeRatioMonthly=MonthlyMeanStd.ix[:,0]*np.sqrt(252)/MonthlyMeanStd.ix[:,1]
        
        return [MonthlyMeanStd,SharpeRatioMonthly]
        
        
        
        
        
    # calculate the drawdown for single data point
    # simple_interest is for clarifying if the input is in simple interest form
    def drawdown_single_point(self, pos, choice_simple_interest):
        if choice_simple_interest==True:
            # pos+1 is because we want to incorporate the current time point
            value_prior=self.SimpleValue[:(pos+1)]
            DrawdownSinglePoint=np.max(value_prior)-self.SimpleValue[pos]
        else:
            # pos+1 is because we want to incorporate the current time point
            value_prior=self.CompoundValue[:(pos+1)]
            DrawdownSinglePoint=(np.max(value_prior)-self.CompoundValue[pos])/np.max(value_prior)
        return DrawdownSinglePoint
    
    
    
    # calculate the drawdown for all the data point
    # choice_simple_interest is for clarifying if the input is in simple interest form    
    def drawdown(self,choice_simple_interest):
        if choice_simple_interest==True:
            self.SimpleDrawback=[]
            for i in range(len(self.date)):
                DrawdownSinglePoint=self.drawdown_single_point(i,choice_simple_interest=True)
                self.SimpleDrawback.append(DrawdownSinglePoint)
     
        if choice_simple_interest==False:
            self.CompoundDrawback=[]
            for i in range(len(self.date)):
                DrawdownSinglePoint=self.drawdown_single_point(i,choice_simple_interest=False)
                self.CompoundDrawback.append(DrawdownSinglePoint)


    # calculate the simple drawdown for every year
    # timestamp1 is a string, so is timestamp2 
    # timestamp2 is greater than timestamp1      
    def SimpleDrawback_by_year(self):
        DateSimpleDrawback=pd.DataFrame([self.date,self.SimpleDrawback]).transpose()
        DateSimpleDrawback.columns=['Tradedates','SimpleDrawback']
        
        # convert numpy.float(64) to float(64)
        # otherwise a error will raised when
        # YearlyMeanStd=GroupByYear.agg({'returns':[np.mean,np.std]})
        try:
            DateSimpleDrawback['SimpleDrawback']=DateSimpleDrawback['SimpleDrawback'].apply(lambda x:x.item())
        except:
            print ('No need to apply the operation from numpy.float64 to float64!\n')
        
        # create year index and group
        DateSimpleDrawback['year']=DateSimpleDrawback['Tradedates'].apply(lambda x:x.year)
        GroupByYear=DateSimpleDrawback.groupby(DateSimpleDrawback['year'])
        
        # aggregate returns according to year
        try:
            YearlySimpleDrawback=GroupByYear.agg({'SimpleDrawback':np.max})
        except:
            EveryYearMax=[]
            for name, group in GroupByYear:
                EveryYearMax.append(np.max(group['SimpleDrawback']))
            YearlySimpleDrawback=pd.DataFrame(EveryYearMax)
            YearlySimpleDrawback=YearlySimpleDrawback.set_index(DateSimpleDrawback['year'].unique())
        return YearlySimpleDrawback

    
    # calculate the max drawdown for all the data point
    # choice_simple_interest is for clarifying if the input is in simple interest form      
    def max_drawdown(self,choice_simple_interest):
        if choice_simple_interest==True:
            return np.max(self.SimpleDrawback)
            
        if choice_simple_interest==False:
            return np.max(self.CompoundDrawback)
            
            
    # find the winning rate of the strategy
    def win_rate(self):
        return sum(self.returns>0)/sum(self.returns!=0)
    
    
    # find the Profit/Loss ratio
    def profit_and_loss_ratio(self):
        AvgProfit=np.mean(self.returns[self.returns>0])
        AvgLoss=np.mean(self.returns[self.returns<0])
        return np.abs(AvgProfit/AvgLoss)
           
    
    def trading_index_finder(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions!=0)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions==-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
            
            if (actions.iloc[actionindex1]==-1):
                actionindex2=np.where(actions==1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  
    

    # find the first set of transaction: buy and then sell
    # i.e. find the first example of pair 1,-1
    # if either actionindex1=='end' or actionindex2=='end', then we shouldn't preceed forward
    # action is a munpy array or a pandas series
    def trading_index_finder_longonly(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions==1)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions==-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0] 
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  
    
    
    # an actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
    def Holding_Period(self, actionlist, Type):
        try:
            self.TradingTimeIntv
        except:
            self.TradingTimeIntv=[]
            
            while (len(actionlist)>0):
                
                # find the first set of transaction: buy and then sell, or short and then cover
                if Type=='LongShort':
                    [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
                
                if Type=='LongOnly':
                    [actionindex1,actionindex2]=self.trading_index_finder_longonly(actionlist['Prediction'])
                    
                # that is the end of a loop, break out of the loop
                if ((actionindex1=='end') or (actionindex2=='end')):
                    break
                
                
                [Datetime1,Action1]=actionlist[['DATETIME','Prediction']].iloc[actionindex1]
                [Datetime2,Action2]=actionlist[['DATETIME','Prediction']].iloc[actionindex2]
                
                
                self.TradingTimeIntv.append(([Datetime1,Action1],[Datetime2,Action2]))
                
                # update the actionlist
                actionlist=actionlist[actionlist['DATETIME']>Datetime2]
                print (Datetime2)
            
            self.Type=Type
        return self.TradingTimeIntv
            
    
    def generate_holding_time(self):
        try:
            self.holdingperiod
        except:         
            self.holdingperiod=[]
            for timeinvt in self.TradingTimeIntv:
                if self.Type=='LongOnly':
                    if timeinvt[0][1]==1 and timeinvt[1][1]==-1 and timeinvt[0][0]<timeinvt[1][0]:
                        self.holdingperiod.append(timeinvt[1][0]-timeinvt[0][0])
                        
                if self.Type=='LongShort':
                    if timeinvt[0][1]*timeinvt[1][1]==-1 and timeinvt[0][0]<timeinvt[1][0]:
                        self.holdingperiod.append(timeinvt[1][0]-timeinvt[0][0])         
        return self.holdingperiod
    
    
    def avg_holding_period(self, actionlist, Type):
        self.Holding_Period(actionlist, Type)
        self.generate_holding_time()
        return np.mean(self.holdingperiod)
            

    def max_holding_period(self, actionlist, Type):
        self.Holding_Period(actionlist, Type)
        self.generate_holding_time()
        return np.max(self.holdingperiod)

    def min_holding_period(self, actionlist, Type):
        self.Holding_Period(actionlist, Type)
        self.generate_holding_time()
        return np.min(self.holdingperiod)

            
#evalperf=Eval_performance(compounddata,simple_interest=False)           
#evalperf.end_day()
#evalperf.start_day()
#evalperf.select_return('2007-06-18','2007-11-19')
#evalperf.select_SimpleValue('2007-06-18','2007-11-19')
#evalperf.select_CompoundValue('2007-06-18','2007-11-19')
#evalperf.select_date('2007-06-18','2007-11-19')
#evalperf.Sharpe_Ratio('2007-06-18','2007-11-19')
#evalperf.Sharpe_Ratio_all()
#evalperf.Sharpe_Ratio_by_year()
#evalperf.max_drawdown(simple_interest=False)
#evalperf.Sharpe_Ratio_by_month()
#evalperf.win_rate()
#evalperf.profit_and_loss_ratio() 
#evalperf=Eval_performance(date_val.datevalue,simple_interest=True) 
#evalperf.Holding_Period(backtestMins.actionlist, Type='LongOnly')     
#evalperf.generate_holding_time()
#evalperf.avg_holding_period(backtestMins.actionlist, Type='LongOnly')   
#evalperf.max_holding_period(backtestMins.actionlist, Type='LongOnly')
#evalperf.min_holding_period(backtestMins.actionlist, Type='LongOnly')

     
#
#sql_query="""select * from [GPDB].[dbo].[c_oneminute_history] WHERE id_stock=134 ORDER BY date_trade"""
#onemin=features.IOdata()
#onemin.getdata_RosefinchSQL(sql_query,to_data_frame=True)
#oneminss=features.split_mins_data(onemin.SQLdata)
#oneminss.add_date_time()
#TimestampPrice=oneminss.data[['DATETIME','Date','Time','close']]
#TimestampSignal=pd.read_csv('prediction.csv',sep='\t')
#TimestampSignal=TimestampSignal.ix[:,[1,2]]
#Datetime_Op=features.Datetime_Operation()
#TimestampSignal['Date']=Datetime_Op.str_to_date(TimestampSignal['Date'])




# the class is for backtest

# TimestampSignal is a data frame ['Date','Prediction']
# first column is timestamp 2016-07-12 dtype: datetime64[ns]
# the second column is a prediction value [float64]

# TimestampPrice is a data frame ['DATETIME','Date','Time','close']
# first column is DATETIME 2016-07-14 15:00:00 dtype: datetime64[ns]
# second column is Date 2016-07-14 dtype: datetime.date
# second column is Time 15:00:00 dtype: datetime.time
# the fourth column is a prediction value [float64]

# opencost,closecost,closecost2 are all numeric scalar
# output is a value calculate by simple interest 
class backtest_minutes:
    
    def __init__(self,TimestampSignal,TimestampPrice,opencost,closecost,closecost2):
        self.TimestampSignal=TimestampSignal
        self.TimestampPrice=TimestampPrice
        self.opencost=opencost
        self.closecost=closecost
        self.closecost2=closecost2
        
    
    # calculate the returns from long operations
    # given open price, close price, cost of open the position, cost for close the position
    def long(self,openprice,closeprice,opencost,closecost):
        return ((closeprice*(1-closecost))/(openprice*(1+opencost))-1)


    # calculate the returns from short operations
    # given open price, close price, cost of open the position, cost for close the position        
    def short(self,openprice,closeprice,opencost,closecost):
        nominator=openprice*(1-opencost)-closeprice*(1+closecost)
        denominator=openprice*(1-opencost)
        return (nominator/denominator)
   
   
   
    # r is the stoploss criteria
    # tradep is a numpy array, stands for trading price
    # opencost is the cost for open 
    # closecost is the normal close cost
    # closecost2 is the intraday cost
    
    # intraday_long_with_stoploss and intraday_short_with_stoploss 
    # tries to calculate the returns for intraday
    # if stoploss happens, then we use the next minutes bar as the price for closing the position
    # if the stoploss did not happen, then we use the last element of tradep as 
    # the price for closing the position
    # it will return the returns of that trade(transaction)
    def intraday_long_with_stoploss(self,r,tradep,opencost,closecost,closecost2):
        minr=tradep[tradep<tradep[0]*(1-r)]
        if len(minr)!=0: # stoploss occured
            print ("long stoploss occured! "+str(minr['DATETIME'].iloc[0]) +"\n")
            return self.long(tradep[0],minr[0],opencost,closecost2)
        else:
            return self.long(tradep[0],tradep[-1],opencost,closecost)  
    
    
    
    def intraday_short_with_stoploss(self,r,tradep,opencost,closecost,closecost2):
        maxr=tradep[tradep>tradep[0]*(1+r)]
        if len(maxr)!=0: # stoploss occured
            print ("short stoploss occured! "+str(maxr['DATETIME'].iloc[0]) +"\n")
            return self.short(tradep[0],maxr[0],opencost,closecost2)
        else:
            return self.short(tradep[0],tradep[-1],opencost,closecost) 
    
    
    
    
    # rstoploss is the long stoploss criteria
    # rstopwin is the short stoploss criteria
    # DTtradep is a pandas dataframe, stands for datetime and trading price
    # the first column of DTtradep is a 'DATETIME', which is a timestamp object
    # the second column s a 'close', which is a float64 object
    # opencost is the cost for open 
    # closecost is the normal close cost
    # closecost2 is the intraday cost
    
    # crossday_long_with_stoploss and crossday_short_with_stoploss 
    # tries to calculate the returns for any time (intraday or not)
    # e.g. the returns between '2010-09-10 13:47:00' and '2010-09-20 09:56:00'
    # if stoploss happens, then we use the next minutes bar as the price for closing the position
    # if the stoploss did not happen, then we use the last element of tradep as 
    # the price for closing the position
    
    # the function returns two values
    # (1) a dataframe with first column being datetime.date, it can be duplicated.
    # as many transactions can be made on a single day. 
    # e.g. many times of stoploss, close the position at a day open. reopen in the mid of the day
    # second column being returns of a set of these transactions
    # (2) the second value is the ending datetime 
    
    def crossday_long_with_stoploss_stopwin(self,rstoploss,rstopwin,DTtradep,opencost,closecost,closecost2):
        minr=np.where(DTtradep['close']<DTtradep['close'].iloc[0]*(1-rstoploss))[0]
        maxr=np.where(DTtradep['close']>DTtradep['close'].iloc[0]*(1+rstopwin))[0]
        
        if (len(minr)!=0 & len(maxr)!=0):
            rstop=np.min([maxr,minr])
        elif (len(minr)!=0 & len(maxr)==0):
            rstop=minr
        elif (len(minr)==0 & len(maxr)!=0):
            rstop=maxr
        else:
            rstop=[]
        
        
        tradingvalue=[]
        if len(rstop)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(rstop[0]+1)]
            interdates=interprice['Date'].unique()
            print ("long stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)<2):
            tradingvalue.append(self.long(interprice['close'].iloc[0],interprice['close'].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice['close'].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,opencost,0))       

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate            
            closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
            closethatday=interprice['close'].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]
        
        return [datevalues,endperiod]
    
    
    
    def crossday_short_with_stoploss_stopwin(self,rstoploss,rstopwin,DTtradep,opencost,closecost,closecost2):
        maxr=np.where(DTtradep['close']>DTtradep['close'].iloc[0]*(1+rstoploss))[0]
        minr=np.where(DTtradep['close']<DTtradep['close'].iloc[0]*(1-rstopwin))[0]
        
        if (len(minr)!=0 & len(maxr)!=0):
            rstop=np.min([maxr,minr])
        elif (len(minr)!=0 & len(maxr)==0):
            rstop=minr
        elif (len(minr)==0 & len(maxr)!=0):
            rstop=maxr
        else:
            rstop=[]
        
        
        tradingvalue=[]
        if len(maxr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(maxr[0]+1)]
            interdates=interprice['Date'].unique()
            print ("short stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)<2):
            tradingvalue.append(self.short(interprice['close'].iloc[0],interprice['close'].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice['close'].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.short(closeprev,closethatday,opencost,0))       

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.short(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate            
            closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
            closethatday=interprice['close'].as_matrix()[-1]
            tradingvalue.append(self.short(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]

        return [datevalues,endperiod]     
    
    
    

    
    # r is the stoploss criteria, r is the loss from opening point
    # DTtradep is a pandas dataframe, stands for datetime and trading price
    # the first column of DTtradep is a 'DATETIME', which is a timestamp object
    # the second column s a 'close', which is a float64 object
    # opencost is the cost for open 
    # closecost is the normal close cost
    # closecost2 is the intraday cost
    
    # crossday_long_with_stoploss and crossday_short_with_stoploss 
    # tries to calculate the returns for any time (intraday or not)
    # e.g. the returns between '2010-09-10 13:47:00' and '2010-09-20 09:56:00'
    # if stoploss happens, then we use the next minutes bar as the price for closing the position
    # if the stoploss did not happen, then we use the last element of tradep as 
    # the price for closing the position
    
    # the function returns two values in list form
    # (1) a dataframe with first column being datetime.date, it can be duplicated.
    # as many transactions can be made on a single day. 
    # e.g. many times of stoploss, close the position at a day open. reopen in the mid of the day
    # second column being returns of a set of these transactions
    # (2) the second value is the ending datetime 
    
    def crossday_long_with_stoploss(self,r,DTtradep,opencost,closecost,closecost2,openprice='close',closeprice='close'):
        minr=np.where(DTtradep['low']<DTtradep[openprice].iloc[0]*(1-r))[0]
        tradingvalue=[]
        if len(minr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(minr[0]+1)]
            interdates=interprice['Date'].unique()
            print ("long stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
            STOPLOSS=True
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
            STOPLOSS=False
            
        # if this is a intraday trade
        if (len(interdates)<2):
            if STOPLOSS==True:
                tradingvalue.append(-r)
            else:
                tradingvalue.append(self.long(interprice[openprice].iloc[0],interprice[closeprice].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice[openprice].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,opencost,0))    
            
            #if tradingvalue[0]<0:
            #    opennextday=interprice['close'][interprice['Date']==interdates[1]].as_matrix()[0]
            #    tradingvalue.append(self.long(closethatday,opennextday,0,closecost))      
            #    datevalues=pd.DataFrame([interdates[:2],tradingvalue]).transpose()
            #    datevalues.columns=['Date','Returns']     
            #    endperiod=interprice['DATETIME'][interprice['Date']==interdates[1]].iloc[0]-datetime.timedelta(minutes=1)
            #    return [datevalues,endperiod] 

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,0))
            
            if STOPLOSS==True:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice[openprice].as_matrix()[0]*(1-r)
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            else:                 
                # get the last day of trading return 
                # because the cost of closing, we have to do that seperate            
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
                closethatday=interprice[closeprice].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]
        
        return [datevalues,endperiod]
    
    
        
    def crossday_short_with_stoploss(self,r,DTtradep,opencost,closecost,closecost2,openprice='close',closeprice='close'):
        maxr=np.where(DTtradep['high']>DTtradep['close'].iloc[0]*(1+r))[0]
        tradingvalue=[]
        if len(maxr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(maxr[0]+1)]
            interdates=interprice['Date'].unique()
            print ("short stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
            STOPLOSS=True
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
            STOPLOSS=False
        
        # if this is a intraday trade
        if (len(interdates)<2):
            if STOPLOSS==True:
                tradingvalue.append(-r)
            else:               
                tradingvalue.append(self.short(interprice[openprice].iloc[0],interprice[closeprice].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice[openprice].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.short(closeprev,closethatday,opencost,0))      
            
            #if tradingvalue[0]<0:
            #    opennextday=interprice['close'][interprice['Date']==interdates[1]].as_matrix()[0]
            #    tradingvalue.append(self.short(closethatday,opennextday,0,closecost))      
            #    datevalues=pd.DataFrame([interdates[:2],tradingvalue]).transpose()
            #    datevalues.columns=['Date','Returns']     
            #    endperiod=interprice['DATETIME'][interprice['Date']==interdates[1]].iloc[0]-datetime.timedelta(minutes=1)
            #    return [datevalues,endperiod] 

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.short(closeprev,closethatday,0,0))
                
            if STOPLOSS==True:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice[openprice].as_matrix()[0]*(1-r)
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            else: 
                # get the last day of trading return 
                # because the cost of closing, we have to do that seperate            
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
                closethatday=interprice[closeprice].as_matrix()[-1]
                tradingvalue.append(self.short(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]

        return [datevalues,endperiod]     
    
    
    
    
    # r is the stoploss criteria, moving stop, that is, loss from the highest value
    # when ATR is True, a column called ATR must be given, and r is a multiplier to ATR
    # DTtradep is a pandas dataframe, stands for datetime and trading price
    # the first column of DTtradep is a 'DATETIME', which is a timestamp object
    # the second column s a 'close', which is a float64 object
    # opencost is the cost for open 
    # closecost is the normal close cost
    # closecost2 is the intraday cost
    
    # crossday_long_with_stoploss and crossday_short_with_stoploss 
    # tries to calculate the returns for any time (intraday or not)
    # e.g. the returns between '2010-09-10 13:47:00' and '2010-09-20 09:56:00'
    # if stoploss happens, then we use the next minutes bar as the price for closing the position
    # if the stoploss did not happen, then we use the last element of tradep as 
    # the price for closing the position
    
    # the function returns two values
    # (1) a dataframe with first column being datetime.date, it can be duplicated.
    # as many transactions can be made on a single day. 
    # e.g. many times of stoploss, close the position at a day open. reopen in the mid of the day
    # second column being returns of a set of these transactions
    # (2) the second value is the ending datetime 
    
    def crossday_long_with_movingstoploss(self,r,DTtradep,opencost,closecost,closecost2,ATR):
        if ATR==True:
           # find the index for moving stoploss
            for i in range(len(DTtradep['close'])):
                minr=np.where(DTtradep['close'].astype(float).iloc[i:]<float(DTtradep['close'].iloc[i])-DTtradep['ATR'].iloc[i:]*r)[0]
                if len(minr)!=0:
                    minr=minr+i
                    break  
        else:
            for i in range(len(DTtradep['close'])):
                minr=np.where(DTtradep['close'].astype(float).iloc[i:]<float(DTtradep['close'].iloc[i])*(1-r))[0]
                if len(minr)!=0:
                    minr=minr+i
                    break  

        
        tradingvalue=[]
        if len(minr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(minr[0]+1)]
            interdates=interprice['Date'].unique()
            print ("long stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)<2):
            tradingvalue.append(self.long(interprice['close'].iloc[0],interprice['close'].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice['close'].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,opencost,0))       

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate            
            closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
            closethatday=interprice['close'].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]
        
        return [datevalues,endperiod]
    
    
        
    def crossday_short_with_movingstoploss(self,r,DTtradep,opencost,closecost,closecost2,ATR):
        if ATR==True:
            # find the index for moving stoploss
            for i in range(len(DTtradep['close'])):
                maxr=np.where(DTtradep['close'].iloc[i:]>float(DTtradep['close'].iloc[i])+DTtradep['ATR'].iloc[i:]*r)[0]
                if len(maxr)!=0:
                    maxr=maxr+i
                    break   
        else:  # find the index for moving stoploss
            for i in range(len(DTtradep['close'])):
                maxr=np.where(DTtradep['close'].iloc[i:]>DTtradep['close'].iloc[i]*(1+r))[0]
                if len(maxr)!=0:
                    maxr=maxr+i
                    break

            
        tradingvalue=[]
        if len(maxr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(maxr[0]+1)]
            interdates=interprice['Date'].unique()
            print ("short stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)<2):
            tradingvalue.append(self.short(interprice['close'].iloc[0],interprice['close'].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice['close'].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.short(closeprev,closethatday,opencost,0))       

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.short(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate            
            closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
            closethatday=interprice['close'].as_matrix()[-1]
            tradingvalue.append(self.short(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]

        return [datevalues,endperiod]         
    
    
    
    
    
    
    # find the first set of transaction: buy and then sell, or short and then cover 
    # i.e. find the first example of pair 1,-1 or -1,1
    # if either actionindex1=='end' or actionindex2=='end', then we shouldn't preceed forward
    # action is a munpy array or a pandas series
    def trading_index_finder(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions!=0)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions==-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
            
            if (actions.iloc[actionindex1]==-1):
                actionindex2=np.where(actions==1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  
    

    # find the first set of transaction: buy and then sell
    # i.e. find the first example of pair 1,-1
    # if either actionindex1=='end' or actionindex2=='end', then we shouldn't preceed forward
    # action is a munpy array or a pandas series
    def trading_index_finder_longonly(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions==1)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions==-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0] 
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  
        
    
    # adjust the contract IC/IF like ex-divide
    # 'id_stock', 'stockcode', 'changedate', 'id_stock_mapped',
    #  'stockcode_mapped', 'month'
    def contract_adjust_factor(self, RolloverDate):
        onemin=features.IOdata()
        AdjustFactor=[]
        for i in range(1,len(RolloverDate)):
            # get the id_stock_mapped after 
            id_stock_mapped_after=RolloverDate['id_stock_mapped'].iloc[i]
            sql_query="""SELECT * FROM [GPDB].[dbo].[c_oneminute_history] where id_stock=""" + str(id_stock_mapped_after)
            onemin.getdata_RosefinchSQL(sql_query,to_data_frame=True)
            ChangeAfter=onemin.SQLdata

            # get the id_stock_mapped before
            id_stock_mapped_before=RolloverDate['id_stock_mapped'].iloc[(i-1)]
            sql_query="""SELECT * FROM [GPDB].[dbo].[c_oneminute_history] where id_stock=""" + str(id_stock_mapped_before)
            onemin.getdata_RosefinchSQL(sql_query,to_data_frame=True)
            ChangeBefore=onemin.SQLdata

            # get the respect price at the day before rolling over
            RolloverPriceAfter=ChangeAfter[ChangeAfter['date_trade']<=RolloverDate['changedate'].iloc[i].date()]['val_close'].iloc[-1]
            RolloverPriceBefore=ChangeBefore[ChangeBefore['date_trade']<=RolloverDate['changedate'].iloc[i].date()]['val_close'].iloc[-1]
            multiplier=float(RolloverPriceBefore/RolloverPriceAfter)
            
            AdjustFactor.append([RolloverDate['changedate'].iloc[i].date(),multiplier])
            
            AdjustFactor=pd.DataFrame(AdjustFactor)
            AdjustFactor.columns=['Date','Factor']
            
        return AdjustFactor

    
    # find the close prices that needed to be adjusted 
    # contract['Close'][contract['Date']>=RolloverDate[i].date()]*multiplier    
    # adjust the contract from very begining using the contract adjust factor
    def contract_adjust(self, AdjustFactor):
        for i in range(len(AdjustFactor)):
            self.TimestampPrice['close'][self.TimestampPrice['Date'] >= AdjustFactor['Date'].iloc[i]]=\
            self.TimestampPrice['close'][self.TimestampPrice['Date'] >= AdjustFactor['Date'].iloc[i]]*AdjustFactor['Factor'].iloc[i]
        
            

    
    # input, KnownState is a dataframe with four columns 
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    # find the 25 75 quantile for a set of prediction 
    def get_quantile_by_time(self,KnownState,quantile1=25,quantile2=75):
        Qall=[]
        TimestampLevels=KnownState['Time'].unique()
        for Tstamp in TimestampLevels:
            Qall.append(np.percentile(KnownState['Prediction'][KnownState['Time']==Tstamp],
                                      [quantile1, quantile2]).reshape(1,2))
        return np.concatenate(Qall)
    
    # input, KnownState is a dataframe with four columns (Sort by Date and Time)
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    # find the quantile for each element 
    # return a [Date Time Percentile] object
    def get_percentile_by_time(self,KnownState):
        Pall=pd.DataFrame()
        TimestampLevels=KnownState['Time'].unique()
        DatestampLevels=KnownState['Date'].unique()
        for Tstamp in TimestampLevels:
            TKnownState=KnownState['Prediction'][KnownState['Time']==Tstamp]
            Tpctile=[sp.stats.percentileofscore(TKnownState,a,'rank') for a in TKnownState]
            Tpct=pd.DataFrame({'Date':DatestampLevels,'Time':[Tstamp]*len(Tpctile),'Prediction':Tpctile})
            Pall=Pall.append(Tpct)
        Pall=Pall.sort_values(by=['Date','Time'])
        return Pall[['Date','Time','Prediction']]
        
    
    # input, TimestampSignal is a dataframe with four columns 
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    # startn is the days that we get started 
    # generate an actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
    # for example, if we are standing at 2007-07-05, then we using all the data backing to the first day of our prediction
    # and then we use all the Predictions between the first day and 2007-07-04 to calculate a 25 75 quantile
    # and then we examine if the 2007-07-05 is greater than the upper 25 quantile, if yes, write 1
    # similiarly ,if the 2007-07-05 is smaller than the lower 25 quantile, if yes, write -1
    # the output is DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(1,0,-1)
    def actionlist_generator(self, startn=13, lookbackn=None, Timeeffect=True):
        self.actionlist=[]
        stepsize=round(self.TimestampSignal.shape[0]/len(self.TimestampSignal['Date'].unique()))
        
        # remove the Date that has different stepsize 
        if Timeeffect==True:
            for Date in self.TimestampSignal['Date'].unique():
                if sum(self.TimestampSignal['Date']==Date)!= stepsize:
                    self.TimestampSignal=self.TimestampSignal[self.TimestampSignal['Date']!=Date]
                    print (str(Date)+" has been removed because of missing data(prediction)!\n")
                
        startpoint=startn*stepsize
        endpoint=int(self.TimestampSignal.shape[0]/stepsize)*stepsize-stepsize
        for i in range(startpoint,(endpoint+1),stepsize):
            if lookbackn==None:
                KnownState=self.TimestampSignal[:i]
            else:
                lookbackn=lookbackn*stepsize
                KnownState=self.TimestampSignal[(i-lookbackn):i]
            
            Qall=self.get_quantile_by_time(KnownState,quantile1=25,quantile2=75)
            
            if Timeeffect==False:
                Qall=np.mean(Qall, axis=0)
                
            # find that day (both prediction and mins data)
            PredictionThatday=self.TimestampSignal[i:(i+stepsize)]
            print (PredictionThatday['Date'].iloc[0])
            PredictionThatday=PredictionThatday['Prediction'].copy().as_matrix()
            
            if Timeeffect==False:
                # if we will need to do anything that day
                PredictionThatday[PredictionThatday<Qall[0]]=-1
                PredictionThatday[PredictionThatday>Qall[1]]=1 
                PredictionThatday[(PredictionThatday>Qall[0]) &
                (PredictionThatday<Qall[1])]=0
            else:
                 # if we will need to do anything that day
                PredictionThatday[PredictionThatday<Qall[:,0]]=-1
                PredictionThatday[PredictionThatday>Qall[:,1]]=1 
                PredictionThatday[(PredictionThatday>Qall[:,0]) &
                (PredictionThatday<Qall[:,1])]=0
         
            self.actionlist.append(PredictionThatday)
            
        self.actionlist=np.concatenate(self.actionlist)
        DATETIME=self.TimestampSignal[['DATETIME','Date','Time']][startpoint:(endpoint+stepsize)]
        DATETIME['Prediction']=self.actionlist
        self.actionlist=DATETIME
     
     
     
    # input, TimestampSignal is a dataframe with four columns 
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    # startn is the days that we get started 
    # lookbackn is how many days we might want to look back, None means we look from start to end
    # generate a Percnetile list for Predictions
    # for example, if we are standing at 2007-07-05, then we using all the data backing to the first day of our prediction
    # and then we use all the Predictions to find the quantiles for the prediction 2007-07-05
    # the output is DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(1,0,-1)
    def actionlist_generator_percentile(self, startn=13, lookbackn=None):
        self.actionlist=[]
        stepsize=round(self.TimestampSignal.shape[0]/len(self.TimestampSignal['Date'].unique()))
        startpoint=startn*stepsize
        endpoint=int(self.TimestampSignal.shape[0]/stepsize)*stepsize
        
        for i in range(startpoint,endpoint,stepsize):
            if lookbackn==None:
                KnownState=self.TimestampSignal[:i]
            else:
                lookbackn=lookbackn*stepsize
                KnownState=self.TimestampSignal[(i-lookbackn):i]
            Pall=self.get_percentile_by_time(KnownState)         
            self.actionlist.append(Pall[Pall['Date']==Pall['Date'].iloc[-1]])
            print ('Current date under process is '+ str(Pall['Date'].iloc[-1]) + '!\n')
           
        self.actionlist=pd.concat(self.actionlist)
        Datetime_Op=features.Datetime_Operation()
        self.actionlist['DATETIME']=Datetime_Op.combine_datetime(self.actionlist['Date'],self.actionlist['Time'])
        self.actionlist=self.actionlist[['DATETIME','Date', 'Time', 'Prediction']]
        return self.actionlist
        
        
   
    # the function missing imputation is to imput missing TimestampSignal 
    # with the most recent available prediction 
    def missingdata_imputation(self):
        for date in self.TimestampSignal['Date'].unique():
            if sum(self.TimestampSignal['Date']==date)!=len(self.TimestampSignal['Time'].unique()):
                print (date)
                missingdate=date
        
                timelevels=self.TimestampSignal['Time'][self.TimestampSignal['Date']==missingdate]
                signal=self.TimestampSignal['Prediction'][self.TimestampSignal['Date']==missingdate].iloc[-1]
                timelevelsall=self.TimestampSignal['Time'].unique()
                timelevelsmissing=timelevelsall[~np.in1d(timelevelsall,timelevels)]

                Datecol=[missingdate]*len(timelevelsmissing)
                Timecol=timelevelsmissing.tolist()
                Predictioncol=[signal]*len(timelevelsmissing)

                Datetime_Op=features.Datetime_Operation()
                DATETIMEcol=Datetime_Op.combine_datetime(pd.Series(Datecol),pd.Series(Timecol))

                missingrows=pd.DataFrame([Datecol,Timecol,DATETIMEcol,Predictioncol]).transpose()
                missingrows.columns=self.TimestampSignal.columns

                self.TimestampSignal=self.TimestampSignal.append(missingrows)
                missingdate=None
                
        self.TimestampSignal=self.TimestampSignal.sort_values(by=['Date','Time'])
    
    

    # to decide whether we should go long/short at a specific position
    # timepoint is a string or datetime.time object, stands for the time opening the position
    # r is the stoploss criteria
    # endtime is the time of ending this intraday trade
    def Intraday_once_mins(self,timepoint,r, endtime):
        values=[]
        values.append(1)
        AllDate=self.TimestampPrice['Date'].unique()
        
        try:
            actionlist=self.actionlist
        except:
            self.actionlist=self.actionlist_generator(startn=13, lookbackn=None)
        
        #actionlist['Prediction']=actionlist['Prediction']/100
        #actionlist['Prediction'][actionlist['Prediction']>0.65]=1
        #actionlist['Prediction'][actionlist['Prediction']<0.35]=-1
        #actionlist['Prediction'][(actionlist['Prediction']!=1) & (actionlist['Prediction']!=-1)]=0
       
        for i in range(len(actionlist)-1):
            
            # get the date
            dates=actionlist['Date'].iloc[i]
            #datesNext=AllDate[np.where(AllDate==dates)[0]+1][0]
        
            # get the prediction
            signal=actionlist['Prediction'].iloc[i]
            # signal=signal.as_matrix()[0]
        
            # get the price of that day
            closeThatday=self.TimestampPrice[self.TimestampPrice['Date']==dates]
            closeThatday=features.within_day_price_features(closeThatday)
            closeThatday=closeThatday.get_close_price(timepoint,endtime)
            closeThatday=closeThatday.astype(float)
            
            # to see if there are 2% more volitility 
            # minr is for stoploss of long
            # maxr is for stoploss of short
            
            # if stoploss occurs, the stoploss will happen at end of last minutes
            # say the stoploss criteria is reached at 11:16, then we use the close price of 11:16
            minr=closeThatday[closeThatday<closeThatday[0]*(1-r)]
            maxr=closeThatday[closeThatday>closeThatday[0]*(1+r)]
            
            # if stoploss occurs, the stoploss will happen at end of last minutes
            # say the stoploss criteria is reached at 11:16, then we use the close price of 11:15
            # minr=closeThatday[np.where(closeThatday<closeThatday[0]*(1-r))[0]-1]
            # maxr=closeThatday[np.where(closeThatday>closeThatday[0]*(1-r))[0]-1]
        
            # get the price of next day
            #closeNextday=self.TimestampPrice[self.TimestampPrice['Date']==datesNext]
            #closeNextday=features.within_day_price_features(closeNextday)
            #closeNextday=closeNextday.get_close_price('09:31:00','15:00:00')
            #closeNextday=closeNextday.astype(float)
        
            # combine the price of that day and the next day
            #closeAll=np.append(closeThatday,closeNextday[0])
            closeAll=closeThatday
        
            if signal>0:
                if len(minr)!=0: # stoploss occured
                    values.append(values[-1]+self.long(closeAll[0],minr[0],self.opencost,self.closecost2))
                else:
                    values.append(values[-1]+self.long(closeAll[0],closeAll[-1],self.opencost,self.closecost))
                
            if signal<0:
                if len(maxr)!=0: # stoploss occured
                    values.append(values[-1]+self.short(closeAll[0],maxr[0],self.opencost,self.closecost2))
                else:
                    values.append(values[-1]+self.short(closeAll[0],closeAll[-1],self.opencost,self.closecost))
                
                
            if signal==0: # virtually do nothing       
                values.append(values[-1])         
            
            
        return values    

    

    def day_once_1115_to_1115_mins(self,timepoint,r):
        values=[]
        values.append(1)
        AllDate=self.TimestampPrice['Date'].unique()
       
        for i in range(len(self.TimestampSignal['Date'])-1):
            
            # get the date
            dates=self.TimestampSignal['Date'][i]
            datesNext=AllDate[np.where(AllDate==dates)[0]+1][0]
        
            # get the prediction
            signal=self.TimestampSignal['Prediction'][i]
            # signal=signal.as_matrix()[0]
        
            # get the price of that day
            closeThatday=self.TimestampPrice[self.TimestampPrice['Date']==dates]
            closeThatday=features.within_day_price_features(closeThatday)
            closeThatday=closeThatday.get_close_price(timepoint,'15:00:00')
            closeThatday=closeThatday.astype(float)
        
            # get the price of next day
            closeNextday=self.TimestampPrice[self.TimestampPrice['Date']==datesNext]
            closeNextday=features.within_day_price_features(closeNextday)
            closeNextday=closeNextday.get_close_price('11:15:00','11:16:00')
            closeNextday=closeNextday.astype(float)
            
            # combine the price of that day and the next day
            closeAll=np.append(closeThatday,closeNextday[0])
            
            # to see if there are 2% more volitility 
            # minr is for stoploss of long
            # maxr is for stoploss of short
            minr=closeAll[closeAll<closeAll[0]*(1-r)]
            maxr=closeAll[closeAll>closeAll[0]*(1+r)]
        

        
            if signal>0:
                if len(minr)!=0: # stoploss occured
                    values.append(values[-1]+self.long(closeAll[0],minr[0],self.opencost,self.closecost2))
                else:
                    values.append(values[-1]+self.long(closeAll[0],closeAll[-1],self.opencost,self.closecost))
                
            if signal<0:
                if len(maxr)!=0: # stoploss occured
                    values.append(values[-1]+self.short(closeAll[0],maxr[0],self.opencost,self.closecost2))
                else:
                    values.append(values[-1]+self.short(closeAll[0],closeAll[-1],self.opencost,self.closecost))
                
                
            if signal==0: # virtually do nothing       
                values.append(values[-1])         
            
            
        return values    






    # to make decision every 30 mins
    # input, TimestampSignal is a dataframe with four columns 
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    def Intraday_halfhour_mins(self,r):
        values=[]
        values.append(1)
        AllDate=self.TimestampPrice['Date'].unique()

        for i in range(91,self.TimestampSignal.shape[0],7):
            
            print (values[-1])
            # get known prediction
            KnownState=self.TimestampSignal[:i]
        
            # calculate quantile for previous predictions 
            Qall=pd.DataFrame(self.get_quantile_by_time(KnownState,quantile1=25,quantile2=75))
        
            # find that day (both prediction and mins data)
            PredictionThatday=self.TimestampSignal[i:(i+7)]
            PredictionThatday=PredictionThatday.sort(columns='Time', ascending=True)    
        
            # get the date
            # dates is a datetime object
            dates=PredictionThatday['Date'].iloc[0]
            datesNext=AllDate[np.where(AllDate==dates)[0]+1][0]
        
            # get the price of that day
            closeThatday=self.TimestampPrice[self.TimestampPrice['Date']==dates]
            closeThatday['close']=closeThatday['close'].astype(float)
        
            # get the price of next day
            closeNextday=self.TimestampPrice[self.TimestampPrice['Date']==datesNext]
            closeNextday=features.within_day_price_features(closeNextday)
            closeNextday=closeNextday.get_close_price('09:31:00','09:31:00')
            closeNextday=closeNextday.astype(float)
        
        
            # if we will need to do anything that day
            PredictionThatday['Prediction'][(PredictionThatday['Prediction']>Qall.ix[:,0]) &
            (PredictionThatday['Prediction']<Qall.ix[:,1])]=0
                          
            LongIndex=np.where(PredictionThatday['Prediction']>0)[0]
            ShortIndex=np.where(PredictionThatday['Prediction']<0)[0]
        
        
            # if no operation
            if (all(PredictionThatday['Prediction']==0)):
                values.append(values[-1])   
                continue
            
            
            # only long operation happens
            if ( (len(LongIndex)!=0) & (len(ShortIndex)==0) ):
                tradep=closeThatday['close'][closeThatday['Time']>PredictionThatday['Time'].iloc[LongIndex[0]]]
                tradep=tradep.as_matrix()
                minr=tradep[tradep<tradep[0]*(1-r)]
            
                if len(minr)!=0: # stoploss occured
                    values.append(values[-1]+self.long(tradep[0],minr[0],self.opencost,self.closecost2))
                    print ("long stoploss occured! "+str(dates) +"\n")
                else:
                    values.append(values[-1]+self.long(tradep[0],closeNextday[0],self.opencost,self.closecost))
                continue


            # only short operation happens
            if ( (len(LongIndex)==0) & (len(ShortIndex)!=0) ):
                tradep=closeThatday['close'][closeThatday['Time']>PredictionThatday['Time'].iloc[ShortIndex[0]]]
                tradep=tradep.as_matrix()
                maxr=tradep[tradep>tradep[0]*(1+r)]
            
                if len(maxr)!=0: # stoploss occured
                    values.append(values[-1]+self.short(tradep[0],maxr[0],self.opencost,self.closecost2))
                    print ("short stoploss occured! "+str(dates) +"\n")
                else:
                    values.append(values[-1]+self.short(tradep[0],closeNextday[0],self.opencost,self.closecost))
                continue
    

            # if first long then short operation happens
            if ( (len(LongIndex)!=0) & (len(ShortIndex)!=0) & (LongIndex[0]<ShortIndex[0]) ):
                tradep=closeThatday['close'][(closeThatday['Time']<PredictionThatday['Time'].iloc[ShortIndex[0]]) &
                                         (closeThatday['Time']>PredictionThatday['Time'].iloc[LongIndex[0]])]
    
                tradep=tradep.as_matrix()
                minr=tradep[tradep<tradep[0]*(1-r)]
                print ("first long then short occured! "+str(dates) +"\n")
                
                if len(minr)!=0: # stoploss occured
                    values.append(values[-1]+self.long(tradep[0],minr[0],self.opencost,self.closecost2))
                    print ("first long then short stoploss occured! "+str(dates) +"\n")
                else:
                    values.append(values[-1]+self.long(tradep[0],tradep[-1],self.opencost,self.closecost2))
                continue
    
            # if first short then long operation happens
            if ( (len(LongIndex)!=0) & (len(ShortIndex)!=0) & (ShortIndex[0]<LongIndex[0]) ):
                tradep=closeThatday['close'][(closeThatday['Time']<PredictionThatday['Time'].iloc[LongIndex[0]]) &
                                         (closeThatday['Time']>PredictionThatday['Time'].iloc[ShortIndex[0]])]
            
                tradep=tradep.as_matrix()
                maxr=tradep[tradep>tradep[0]*(1+r)]
                print ("first short then long occured! "+str(dates) +"\n")
                
                if len(maxr)!=0: # stoploss occured
                    values.append(values[-1]+self.short(tradep[0],maxr[0],self.opencost,self.closecost2))
                    print ("first short then long stoploss occured! "+str(dates) +"\n")
                else:
                    values.append(values[-1]+self.short(tradep[0],tradep[-1],self.opencost,self.closecost2))
                continue
            
            
    
        return values
   
   
   
    # to make decision every 30 mins and the dicided if we need to hold the position for another day
    # r is how much percentage rate do we need to do stoploss 
    # Type is LongOnly ShortOnly LongShort 
    def crossday_fixedstoploss_mins_value_everyday(self,r,Type='LongShort'):
        self.datevalues=pd.DataFrame()
        PriceSelector=features.cross_day_price_feature(self.TimestampPrice)
    
        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
        try:
            actionlist=self.actionlist
        except:
            self.actionlist_generator(startn=13, Timeeffect=False)
            actionlist=self.actionlist
        

        while (len(actionlist)>0):
            
            # find the first set of transaction: buy and then sell, or short and then cover
            if Type=='LongShort':
                [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
            
            if Type=='LongOnly':
                [actionindex1,actionindex2]=self.trading_index_finder_longonly(actionlist['Prediction'])
                
            # that is the end of a loop, break out of the loop
            if ((actionindex1=='end') or (actionindex2=='end')):
                break
            
            
            [Datetime1,Action1]=actionlist[['DATETIME','Prediction']].iloc[actionindex1]
            [Datetime2,Action2]=actionlist[['DATETIME','Prediction']].iloc[actionindex2]
            
                
            # get the trading price 
            DTtradep=PriceSelector.get_datetime_close_price(Datetime1,Datetime2)
            DTtradep['close']=DTtradep['close'].astype(float)
        
            
            if (Action1==1):
                if Type=='LongOnly' or Type=='LongShort':
                    payoff=self.crossday_long_with_stoploss(r,DTtradep,self.opencost,self.closecost,self.closecost2)
                    self.datevalues=self.datevalues.append(payoff[0]) 
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].unique(),[0]*len(DTtradep['Date'].unique())]).transpose()
                    payoffvalue.colnames=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['DATETIME'].iloc[-1]]


            if (Action1==(-1)):
                if Type=='ShortOnly' or Type=='LongShort':
                    payoff=self.crossday_short_with_stoploss(r,DTtradep,self.opencost,self.closecost,self.closecost2)
                    self.datevalues=self.datevalues.append(payoff[0])
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].unique(),[0]*len(DTtradep['Date'].unique())]).transpose()
                    payoffvalue.colnames=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['DATETIME'].iloc[-1]]                    
            
            # update the actionlist
            actionlist=actionlist[actionlist['DATETIME']>payoff[1]]
            print (payoff[1])
            
        return self.datevalues




   

    # actionlist is not given in this case
    def crossday_movingstoploss_mins_value_everyday(self,r,ATR):
        datevalues=pd.DataFrame()
        PriceSelector=features.cross_day_price_feature(self.TimestampPrice)
        
        
        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
        try:
            actionlist=self.actionlist
        except:
            self.actionlist_generator(startn=13)
            actionlist=self.actionlist
        
        
        while (len(actionlist)>0):
            
            # find the first set of transaction: buy and then sell, or short and then cover 
            [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
            
            # that is the end of a loop, break out of the loop
            if ((actionindex1=='end') or (actionindex2=='end')):
                break
            
            [Datetime1,Action1]=actionlist[['DATETIME','Prediction']].iloc[actionindex1]
            [Datetime2,Action2]=actionlist[['DATETIME','Prediction']].iloc[actionindex2]
            
            # get the trading price 
            DTtradep=PriceSelector.get_datetime_close_price(Datetime1,Datetime2)
            DTtradep['close']=DTtradep['close'].astype(float)
        
            
            if (Action1==1):
                payoff=self.crossday_long_with_movingstoploss(r,DTtradep,self.opencost,self.closecost,self.closecost2,ATR)
                datevalues=datevalues.append(payoff[0])
            
            if (Action1==(-1)):
                payoff=self.crossday_short_with_movingstoploss(r,DTtradep,self.opencost,self.closecost,self.closecost2,ATR)
                datevalues=datevalues.append(payoff[0])
            
            # update the actionlist
            actionlist=actionlist[actionlist['DATETIME']>payoff[1]]
            
        return datevalues

        



    # actionlist is not given in this case
    def crossday_stoploss_stopwin_mins_value_everyday(self,rstoploss,rstopwin,actionlist):
        datevalues=pd.DataFrame()
        PriceSelector=features.cross_day_price_feature(self.TimestampPrice)
        
        while (len(actionlist)>0):
            
            # find the first set of transaction: buy and then sell, or short and then cover 
            [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
            
            # that is the end of a loop, break out of the loop
            if ((actionindex1=='end') or (actionindex2=='end')):
                break
            
            [Datetime1,Action1]=actionlist[['DATETIME','Prediction']].iloc[actionindex1]
            [Datetime2,Action2]=actionlist[['DATETIME','Prediction']].iloc[actionindex2]
            
            # get the trading price 
            DTtradep=PriceSelector.get_datetime_close_price(Datetime1,Datetime2)
            DTtradep['close']=DTtradep['close'].astype(float)
        
            
            if (Action1==1):
                payoff=self.crossday_long_with_stoploss_stopwin(rstoploss,rstopwin,DTtradep,self.opencost,self.closecost,self.closecost2)
                datevalues=datevalues.append(payoff[0])
            
            if (Action1==(-1)):
                payoff=self.crossday_short_with_stoploss_stopwin(rstoploss,rstopwin,DTtradep,self.opencost,self.closecost,self.closecost2)
                datevalues=datevalues.append(payoff[0])
            
            # update the actionlist
            actionlist=actionlist[actionlist['DATETIME']>payoff[1]]
            
        return datevalues        
        
        

#backtestMins=backtest_minutes(TimestampSignal,TimestampPrice,opencost=1.5/10000,closecost=1.5/10000,closecost2=23/10000)
#backtestMins.actionlist_generator()
#backtestMins.actionlist=backtestMins.actionlist[np.in1d(backtestMins.actionlist['Date'],ICmain['Date'].unique())]
#backtestMins.actionlist=backtestMins.actionlist[15176:]

#value=backtestMins.Intraday_once_mins(timepoint='11:16:00',r=0.02)
#value=backtestMins.day_once_1115_to_1115_mins(timepoint='11:16:00',r=0.025)
#rollingfactor=backtestMins.contract_adjust_factor(RolloverDate)
#backtestMins.contract_adjust(rollingfactor)
#backtestMins.Intraday_halfhour_mins(r=0.02)
#
#date_val=combine_date_value(TimestampSignal.iloc[:(TimestampSignal.shape[0]-1),0],value)
#date_val.date_and_value(include_first=True)
#
#evalperf=Eval_performance(date_val.datevalue,simple_interest=True) 
#evalperf.CompoundValue
#evalperf.SimpleValue
#evalperf.CompoundDrawback
#evalperf.SimpleDrawback
#evalperf.returns
#
#evalperf.end_day()
#evalperf.start_day()
#evalperf.select_return('2007-06-18','2007-11-19')
#evalperf.select_SimpleValue('2007-06-18','2007-11-19')
#evalperf.select_CompoundValue('2007-06-18','2007-11-19')datevalues=backtestMins.crossday_halfhour_mins_value_everyday(r=0.04)
#evalperf.select_date('2007-06-18','2007-11-19')
#evalperf.Sharpe_Ratio('2007-06-18','2007-11-19')
#evalperf.Sharpe_Ratio_all()
#evalperf.Sharpe_Ratio_by_year()
#evalperf.max_drawdown(choice_simple_interest=False)
#evalperf.max_drawdown(choice_simple_interest=True)
#evalperf.Sharpe_Ratio_by_month()





# the input is a dataframe
# consist of ['Date','Code','Prediction']
# make a long short portfolio based on Prediction
class Portfolio_Selection:
    def __init__(self,TimestampSignal):
        self.TimestampSignal=TimestampSignal

    # split each day by the datetime.date
    def split_by_day(self):
        self.oneday=[]
        for dates in self.TimestampSignal['Date'].unique():
            self.oneday.append(self.TimestampSignal[self.TimestampSignal['Date']==dates])

    # select stock according to certain quantile
    # quantile1 is the number of upper quantile, say 0.25
    # quantile2 is the number of lower quantile, say 0.75
    # the return is a dataframe of action portfolio
    def select_security_by_quantile(self, quantile1=0.25,quantile2=0.75):
        self.TradingSignal=pd.DataFrame()
        for onedaypred in self.oneday:
            Topn=math.ceil(len(onedaypred)*quantile1)
            bottomn=math.ceil(len(onedaypred)*(1-quantile2))
            onedaypred=onedaypred.sort('Prediction')
            LongShortpred=pd.DataFrame()
            LongPortfolio=onedaypred.iloc[:Topn]
            LongPortfolio['Prediction']=-1
            ShortPortfolio=onedaypred.iloc[-bottomn:]
            ShortPortfolio['Prediction']=1
            NoActionPortfolio=onedaypred.iloc[Topn:-bottomn]
            NoActionPortfolio['Prediction']=0
            LongShortpred=LongShortpred.append(LongPortfolio)
            LongShortpred=LongShortpred.append(ShortPortfolio)
            LongShortpred=LongShortpred.append(NoActionPortfolio)
            self.TradingSignal=self.TradingSignal.append(LongShortpred)       
        return self.TradingSignal
    
    # split the trading signal by security
    # return a list of dataframe, each dataframe is made of [Date,Code,Prediction]
    def split_by_security(self):
        ListofSecurity=[]
        for securitycode in self.TradingSignal['Code'].unique():
            security=self.TradingSignal[self.TradingSignal['Code']==securitycode]
            security=security.sort('Date')
            ListofSecurity.append(security)
        return ListofSecurity
        
        
        
#PortfolioSelection=Portfolio_Selection(TimestampSignal)
#PortfolioSelection.split_by_day()
#TradingSignal=PortfolioSelection.select_security_by_quantile(quantile1=0.25,quantile2=0.75)
#ListofSecurity=PortfolioSelection.split_by_security()


# to make decision every 30 mins and the dicided if we need to hold the position for another day
#def crossday_halfhour_mins(r):
#    values=[]
#    Tradingddate=[]
#    values.append(1)
#    PriceSelector=features.cross_day_price_feature(TimestampPrice)
#    
#    # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
#    actionlist=actionlist_generator(TimestampSignal, startn=13)
#
#    while (len(actionlist)>0):
#            
#        # find the first set of transaction: buy and then sell, or short and then cover 
#        [actionindex1,actionindex2]=trading_index_finder(actionlist['Prediction'])
#            
#        # that is the end of a loop, break out of the loop
#        if ((actionindex1=='end') or (actionindex2=='end')):
#            break
#            
#        [Datetime1,Date1,Action1]=actionlist[['DATETIME','Date','Prediction']].iloc[actionindex1]
#        [Datetime2,Date2,Action2]=actionlist[['DATETIME','Date','Prediction']].iloc[actionindex2]
#            
#        # add timestamp
#        Tradingddate.append(Date2)
#        # get the trading price 
#        tradep=PriceSelector.get_close_price(Datetime1,Datetime2).as_matrix().astype(float)
#        
#        # if it's a intraday trade, then we use the intraday cost
#        if (Date1==Date2):
#            if (Action1==1):
#                values.append(values[-1]+long_with_stoploss(r,tradep,opencost,closecost2))
#            
#            if (Action1==(-1)):
#                values.append(values[-1]+short_with_stoploss(r,tradep,opencost,closecost2))
#            
#            
#        if (Date1!=Date2):
#            if (Action1==1):
#                values.append(values[-1]+long_with_stoploss(r,tradep,opencost,closecost))
#            
#            if (Action1==(-1)):
#                values.append(values[-1]+short_with_stoploss(r,tradep,opencost,closecost))
#
#        actionlist=actionlist[(actionindex2+1):]
#            
#    return [Tradingddate,values]    


#payoff=crossday_short_with_stoploss(r,DTtradep,opencost,closecost,closecost2)
#values=crossday_halfhour_mins_value_everyday(r=0.03)


# using QT days for backtest
# Timestampprice is a dataframe containing Date and Price(Open, High, Low, Close)
class backtest_days:

    def __init__(self,TimestampSignal,TimestampPrice,opencost,closecost):
        self.TimestampSignal=TimestampSignal
        self.TimestampPrice=TimestampPrice
        self.opencost=opencost
        self.closecost=closecost

        
    
    # calculate the returns from long operations
    # given open price, close price, cost of open the position, cost for close the position
    def long(self,openprice,closeprice,opencost,closecost):
        return ((closeprice*(1-closecost))/(openprice*(1+opencost))-1)


    # calculate the returns from short operations
    # given open price, close price, cost of open the position, cost for close the position        
    def short(self,openprice,closeprice,opencost,closecost):
        nominator=openprice*(1-opencost)-closeprice*(1+closecost)
        denominator=openprice*(1-opencost)
        return (nominator/denominator)
    
    
    
    
    
    # input, KnownState is a dataframe with two columns 
    # Date(datetime.date), Prediction(float64)
    # find the 25 75 quantile for a set of prediction 
    def get_quantile_by_time(self,KnownState,quantile1=25,quantile2=75):
        Q=np.percentile(KnownState['Prediction'],[quantile1, quantile2]).reshape(1,2)
        return np.concatenate(Q)
     
     
    # generate a actionlist of 0 and 1    
    def actionlist_generator(self,startpoint):
        self.actionlist=pd.DataFrame()
        endpoint=self.TimestampSignal.shape[0]
        for i in range(startpoint,endpoint):
            KnownState=self.TimestampSignal[:i]
            Q=self.get_quantile_by_time(KnownState,quantile1=25,quantile2=75)
            
            # find that day (both prediction and mins data)
            PredictionThatday=self.TimestampSignal[i:(i+1)]
            print (PredictionThatday['Date'].iloc[0])
            PredictionValueThatday=PredictionThatday['Prediction'].copy().as_matrix()[0]
        
            # if we will need to do anything that day
            if PredictionValueThatday<Q[0]:
                SignalThatday=-1
            elif PredictionValueThatday>Q[1]:
                SignalThatday=1
            else:
                SignalThatday=0
         
            self.actionlist=self.actionlist.append(pd.DataFrame([PredictionThatday['Date'].iloc[0],SignalThatday]).transpose())

        self.actionlist=pd.DataFrame(self.actionlist)
        self.actionlist.columns=['Date','Prediction']
    
    
    
    
    # find the first set of transaction: buy and then sell, or short and then cover 
    # i.e. find the first example of pair 1,-1 or -1,1
    # if either actionindex1=='end' or actionindex2=='end', then we shouldn't preceed forward
    # action is a munpy array or a pandas series
    def trading_index_finder(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions!=0)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions==-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
            
            if (actions.iloc[actionindex1]==-1):
                actionindex2=np.where(actions==1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  



    # find the first set of transaction: buy and then sell, or short and then cover 
    # i.e. find the first example of pair 1,-1 or -1,1
    # if either actionindex1=='end' or actionindex2=='end', then we shouldn't preceed forward
    # action is a munpy array or a pandas series
    def trading_index_finder_timeout(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions!=0)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions!=1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
            
            if (actions.iloc[actionindex1]==-1):
                actionindex2=np.where(actions!=-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  


    # find the discontinuous point of Date
    # return a dataframe of Trading Start Period
    def find_start_of_trading_time(self):
        TradingPeriodStart=[]
        for i in range(1,len(self.TimestampPrice['Date'])):
            if (self.TimestampPrice['Date'].iloc[i]!=self.TimestampPrice['Date'].iloc[i-1]+datetime.timedelta(days=1)):
                TradingPeriodStart.append(self.TimestampPrice['Date'].iloc[i-1])          
        TradingPeriodStart=pd.DataFrame(TradingPeriodStart)
        TradingPeriodStart.columns=['Date']
        return TradingPeriodStart
    
    
    # reconstruct the data to make a weekly prediction 
    # weekly backtest
    # only select the trading days at the end of the week
    # reminder: everyday's preidction is extend to predict to next five days 
    def reconstruct_data_to_weekly(self):
        TradingPeriodStart=self.find_start_of_trading_time()
        self.actionlist=TradingPeriodStart.merge(self.actionlist, on='Date')
    
    
    # calculate the intraday long with stoploss
    # DTtrade is a dataframe with column ['Date','open','high','low','close']
    # r is the rate of stoploss
    # opencost and closecost is the cost of trading cost 
    def crossday_long_with_stoploss(self,r,DTtradep,opencost,closecost,openprice='close',closeprice='close'):
        STOPLOSS=False
        minr=np.where(DTtradep['low'].iloc[1:]<DTtradep[openprice].iloc[0]*(1-r))[0]
        tradingvalue=[]
        if len(minr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(minr[0]+2)]
            interdates=interprice['Date'].unique()
            print ("long stoploss occured! "+str(interprice['Date'].iloc[-1]) +"\n")
            STOPLOSS=True
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)==1):
            print ("Intraday trade cannot be proceed, since this is a long term cross day trade!\n")
            datevalues=pd.DataFrame([interdates,0]).transpose()
            datevalues.columns=['Date','Returns']
            endperiod=interprice['Date'].iloc[-1]
            return [datevalues,endperiod]
        
        
        # if this is a one day trade 
        if (len(interdates)==2):
            if STOPLOSS==True:
                tradingvalue.append(-r)
            else:
                tradingvalue.append(self.long(interprice[openprice].iloc[0],interprice[closeprice].iloc[-1],opencost,closecost))
            
        
    
        # if this is not a intraday trade, and this is a two day trade
        if (len(interdates)==3):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice[openprice].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[1]].as_matrix()[0]
            tradingvalue.append(self.long(closeprev,closethatday,opencost,0))       
            
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate    
            if STOPLOSS==True:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice['close'].as_matrix()[0]*(1-r)
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))       
            else:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice[closeprice].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
        
    
        # if this is not a intraday trade, this is a three day trade 
        if (len(interdates)>3):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice[openprice].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[1]].as_matrix()[0]
            tradingvalue.append(self.long(closeprev,closethatday,opencost,0))       
    
            for i in range(2,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[0]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[0]
                tradingvalue.append(self.long(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate    
            if STOPLOSS==True:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice['close'].as_matrix()[0]*(1-r)
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))       
            else:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice[closeprice].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates[1:],tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['Date'].iloc[-1]
        
        return [datevalues,endperiod]
    




    # calculate the intraday long with stoploss
    # DTtrade is a dataframe with column ['Date','open','high','low','close','twap']
    # r is the rate of stoploss
    # opencost and closecost is the cost of trading cost 
    def crossday_short_with_stoploss(self,r,DTtradep,opencost,closecost,openprice='close',closeprice='close'):
        STOPLOSS=False
        maxr=np.where(DTtradep['high'].iloc[1:]>DTtradep[openprice].iloc[0]*(1+r))[0]
        tradingvalue=[]
        if len(maxr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(maxr[0]+2)]
            interdates=interprice['Date'].unique()
            print ("short stoploss occured! "+str(interprice['Date'].iloc[-1]) +"\n")
            STOPLOSS=True
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)==1):
            print ("Intraday trade cannot be proceed, since this is a long term cross day trade!\n")
            datevalues=pd.DataFrame([interdates,0]).transpose()
            datevalues.columns=['Date','Returns']
            endperiod=interprice['Date'].iloc[-1]
            return [datevalues,endperiod]
        
        # if this is a one day trade 
        if (len(interdates)==2):
            if STOPLOSS==True:
                tradingvalue.append(-r)
            else:
                tradingvalue.append(self.short(interprice[openprice].iloc[0],interprice[closeprice].iloc[-1],opencost,closecost))
            
        
    
        # if this is not a intraday trade, and this is a two day trade
        if (len(interdates)==3):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice[openprice].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[1]].as_matrix()[0]
            tradingvalue.append(self.short(closeprev,closethatday,opencost,0))       
            
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate    
            if STOPLOSS==True:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice['close'].as_matrix()[0]*(1+r)
                tradingvalue.append(self.short(closeprev,closethatday,0,closecost))       
            else:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice[closeprice].as_matrix()[-1]
                tradingvalue.append(self.short(closeprev,closethatday,0,closecost))  
        
    
        # if this is not a intraday trade, this is a three day trade 
        if (len(interdates)>3):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice[openprice].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[1]].as_matrix()[0]
            tradingvalue.append(self.short(closeprev,closethatday,opencost,0))       
    
            for i in range(2,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[0]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[0]
                tradingvalue.append(self.short(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate    
            if STOPLOSS==True:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice['close'].as_matrix()[0]*(1+r)
                tradingvalue.append(self.short(closeprev,closethatday,0,closecost))       
            else:
                closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[0]
                closethatday=interprice[closeprice].as_matrix()[-1]
                tradingvalue.append(self.short(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates[1:],tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['Date'].iloc[-1]
        
        return [datevalues,endperiod]



    # to make decision every 30 mins and the dicided if we need to hold the position for another day
    # r is how much percentage rate do we need to do stoploss 
    # Type is LongOnly ShortOnly LongShort 
    def crossday_fixedstoploss_days_value_weekly_Timeout(self,r,Type='LongOnly'):
        datevalues=pd.DataFrame()
    
        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
        try:
            actionlist=self.actionlist
        except:
            self.actionlist_generator(startpoint=100)
            self.reconstruct_data_to_weekly()
            actionlist=self.actionlist
        

        while (len(actionlist)>1):
            
            # find the first set of transaction: buy and then sell, or short and then cover 
            [actionindex1,actionindex2]=self.trading_index_finder_timeout(actionlist['Prediction'])
            
            # that is the end of a loop, break out of the loop
            if (actionindex1=='end'):
                break
            
            if (actionindex2=='end'):
                [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
                [Date2,Action2]=actionlist[['Date','Prediction']].iloc[-1]
                
            if ((actionindex1!='end') & (actionindex2!='end')):
                [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
                [Date2,Action2]=actionlist[['Date','Prediction']].iloc[actionindex2]
            

            
            Date1=self.TimestampPrice['Date'].iloc[np.where(self.TimestampPrice['Date']>Date1)[0][0]]
            Date2=self.TimestampPrice['Date'].iloc[np.where(self.TimestampPrice['Date']>Date2)[0][0]]
            
            # get the trading price 
            DTtradep=self.TimestampPrice[(self.TimestampPrice['Date']>=Date1) & (self.TimestampPrice['Date']<=Date2)]
        
            
            if (Action1==1):
                if Type=='LongOnly' or Type=='LongShort':
                    payoff=self.crossday_long_with_stoploss(r,DTtradep,self.opencost,self.closecost,openprice='close',closeprice='close')
                    datevalues=datevalues.append(payoff[0]) 
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:].as_matrix(),[0]*(len(DTtradep['Date'])-1)]).transpose()
                    payoffvalue.columns=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]


            if (Action1==(-1)):
                if Type=='ShortOnly' or Type=='LongShort':
                    payoff=self.crossday_short_with_stoploss(r,DTtradep,self.opencost,self.closecost,openprice='close',closeprice='close')
                    datevalues=datevalues.append(payoff[0])
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:].as_matrix(),[0]*(len(DTtradep['Date'])-1)]).transpose()
                    payoffvalue.columns=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]                    
            
            # update the actionlist
            actionlist=actionlist[actionlist['Date']>=payoff[1]]
            print (payoff[1])
            
        return datevalues


    # to make decision every 30 mins and the dicided if we need to hold the position for another day
    # r is how much percentage rate do we need to do stoploss 
    # Type is LongOnly ShortOnly LongShort 
    def crossday_fixedstoploss_days_value_everyday(self,r,Type='LongOnly', Timeout=True):
        datevalues=pd.DataFrame()
    
        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
        try:
            actionlist=self.actionlist
        except:
            self.actionlist_generator(startpoint=100)
            actionlist=self.actionlist
        

        while (len(actionlist)>1):
            
            # find the first set of transaction: buy and then sell, or short and then cover 
            if Timeout:
                [actionindex1,actionindex2]=self.trading_index_finder_timeout(actionlist['Prediction'])
            else:
                [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
            
            # that is the end of a loop, break out of the loop
            if (actionindex1=='end'):
                break
            
            if (actionindex2=='end'):
                [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
                [Date2,Action2]=actionlist[['Date','Prediction']].iloc[-1]
                
            if ((actionindex1!='end') & (actionindex2!='end')):
                [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
                [Date2,Action2]=actionlist[['Date','Prediction']].iloc[actionindex2]
            

            
            #Date1=self.TimestampPrice['Date'].iloc[np.where(self.TimestampPrice['Date']>Date1)[0][0]]
            #Date2=self.TimestampPrice['Date'].iloc[np.where(self.TimestampPrice['Date']>Date2)[0][0]]
            
            # get the trading price 
            DTtradep=self.TimestampPrice[(self.TimestampPrice['Date']>=Date1) & (self.TimestampPrice['Date']<=Date2)]
        
            
            if (Action1==1):
                if Type=='LongOnly' or Type=='LongShort':
                    payoff=self.crossday_long_with_stoploss(r,DTtradep,self.opencost,self.closecost,openprice='close')
                    datevalues=datevalues.append(payoff[0]) 
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:].as_matrix(),[0]*(len(DTtradep['Date'])-1)]).transpose()
                    payoffvalue.columns=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]


            if (Action1==(-1)):
                if Type=='ShortOnly' or Type=='LongShort':
                    payoff=self.crossday_short_with_stoploss(r,DTtradep,self.opencost,self.closecost,openprice='close')
                    datevalues=datevalues.append(payoff[0])
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:].as_matrix(),[0]*(len(DTtradep['Date'])-1)]).transpose()
                    payoffvalue.columns=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]                    
            
            # update the actionlist
            actionlist=actionlist[actionlist['Date']>=payoff[1]]
            print (payoff[1])
            
        return datevalues



    # to make decision every 30 mins and the dicided if we need to hold the position for another day
    # r is how much percentage rate do we need to do stoploss 
    # Type is LongOnly ShortOnly LongShort 
    def crossday_fixedstoploss_days_value_bidaily_Next_N_days(self,r=0.1,Type='LongOnly',nextn=1, openprice='open',closeprice='close'):
        datevalues=pd.DataFrame()
    
        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
        try:
            actionlist=self.actionlist
        except:
            self.actionlist_generator(startpoint=100)
            self.actionlist=self.actionlist[::(nextn+1)]
            actionlist=self.actionlist
        

        while (len(actionlist)>1):
            
            # find the first set of transaction: buy and then sell, or short and then cover 
            # get the index for the first nonzero
            try:
                actionindex1=np.where(actionlist['Prediction']!=0)[0][0]
            except:
                break

            [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
            
            # get the trading price
            try:
                DTtradep=self.TimestampPrice[(self.TimestampPrice['Date']>=Date1)].iloc[:(nextn+1)]
            except:
                break
        
            if (Action1==1):
                if Type=='LongOnly' or Type=='LongShort':
                    payoff=self.crossday_long_with_stoploss(r,DTtradep,self.opencost,self.closecost,openprice=openprice,closeprice=closeprice)
                    datevalues=datevalues.append(payoff[0]) 
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:].as_matrix(),[0]*(len(DTtradep['Date'])-1)]).transpose()
                    payoffvalue.columns=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]


            if (Action1==(-1)):
                if Type=='ShortOnly' or Type=='LongShort':
                    payoff=self.crossday_short_with_stoploss(r,DTtradep,self.opencost,self.closecost,openprice='open')
                    datevalues=datevalues.append(payoff[0])
                else:
                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:].as_matrix(),[0]*(len(DTtradep['Date'])-1)]).transpose()
                    payoffvalue.columns=['Date','Returns']
                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]                    
            
            # update the actionlist
            actionlist=actionlist[actionlist['Date']>=payoff[1]]
            print (payoff[1])
            
        return datevalues








# backtest the stock based on minutes bar
class backtest_minutes_stock:
    
    # DateStocklist is a dataframe contains at least ['Date','Code']
    # it is the stock code selected at certain date 
    # TimestampPrice is a data frame ['DATETIME','Date','Time','close']
    # TimestampSignal is a data frame ['Date','Prediction']
    # 'DATETIME' is a datetime.datetime object
    # TimestampPriceFolder='C:\\Users\Administrator\Desktop\Shanghaiinese\StockCTA\\data\\'
    def __init__(self,TimestampSignal,TimestampPriceFolder,DateStocklist,opencost,closecost):
        self.TimestampSignal=TimestampSignal
        self.TimestampPriceFolder=TimestampPriceFolder
        self.DateStocklist=DateStocklist
        self.opencost=opencost
        self.closecost=closecost

    # calculate the returns from long operations
    # given open price, close price, cost of open the position, cost for close the position
    def long(self,openprice,closeprice,opencost,closecost):
        return ((closeprice*(1-closecost))/(openprice*(1+opencost))-1)


    # calculate the returns from short operations
    # given open price, close price, cost of open the position, cost for close the position        
    def short(self,openprice,closeprice,opencost,closecost):
        nominator=openprice*(1-opencost)-closeprice*(1+closecost)
        denominator=openprice*(1-opencost)
        return (nominator/denominator)
    
    # detect if there is a limit-up for that single stock 
    # the input is a datetime and close object 
    # i.e must contain ['DATETIME','close']
    # the return will be a bool
    # either True(there is a limit up) or False, there isn't any limit up
    def detect_limit_up(self, TimestampPrice, timestamp1):
        BoolTime=TimestampPrice['DATETIME']<timestamp1.date()
        Prevclose=float(TimestampPrice['close'][BoolTime].as_matrix()[-1])
        Currentclose=float(TimestampPrice[TimestampPrice['DATETIME']==timestamp1]['close'].as_matrix()[0])
        if ((Currentclose/Prevclose)-1)>0.0995:
            return True
        else:
            return False
        
    # calculate the profolio value at a given date
    # Date is datetime.date() object 
    # VolumnWeighted is based on equal volumn
    # MoneyWeight is based on equal amt
    def portfolio_value(self, timestamp1, timestamp2, VolumeWeighted=True):
        portfolio=self.DateStocklist['Code'][self.DateStocklist['Date']==timestamp1.date()]
        portfolio=portfolio.as_matrix().tolist()
        # if there is no stock in the portfolio list
        if len(portfolio)==0:
            print ("Warning: No Stock is selected!\n")
            return [np.nan]
        
        # store all stock close in it
        stockcloses=[]
        saver_loader=features.IOdata() 
        for code in portfolio:  
            try:
                code=code.replace('.','_')
                saver_loader.Load_file(self.TimestampPriceFolder+code+'.pkl')
                
                # Determine if there is a limit up for that single stock
                # if yes, omit that stock 
                if self.detect_limit_up(saver_loader.object_to_load,timestamp1):
                    continue

                stock=features.cross_day_price_feature(saver_loader.object_to_load)
                stockclose=stock.get_datetime_close_price(timestamp1,timestamp2)
                
                # if volume weighted, then normalize everything starting from 1
                if VolumeWeighted==False:
                    stockclose['close']=stockclose['close']/stockclose['close'].iloc[0]
                stockcloses.append(stockclose)
            except:
                print (code+" missing!\n") # if nothing is retrieved 
          
        # find the most common length and stick to it.
        L=[len(x) for x in stockcloses]
        (most_common,num_most_common) = [x for x in Counter(L).most_common() if x[0]!=0][0]
        stockcloses=list(compress(stockcloses,[len(x)==most_common for x in stockcloses]))
        
        # the combo value needed to be done
        combovalue=[x['close'] for x in stockcloses]
        combovalue=np.sum(np.array(combovalue), axis=0)
        DTcombovalue=stockcloses[0][['Date','Time','DATETIME']]
        DTcombovalue['close']=combovalue/combovalue[0]
        return DTcombovalue
        
    


    # input, KnownState is a dataframe with four columns 
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    # find the 25 75 quantile for a set of prediction 
    def get_quantile_by_time(self,KnownState,quantile1=25,quantile2=75):
        Qall=[]
        TimestampLevels=KnownState['Time'].unique()
        for Tstamp in TimestampLevels:
            Qall.append(np.percentile(KnownState['Prediction'][KnownState['Time']==Tstamp],
                                      [quantile1, quantile2]).reshape(1,2))
        return np.concatenate(Qall)
    
    
    
    
    # input, TimestampSignal is a dataframe with four columns 
    # DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(float64)
    # startn is the days that we get started 
    # generate an actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
    # for example, if we are standing at 2007-07-05, then we using all the data backing to the first day of our prediction
    # and then we use all the Predictions between the first day and 2007-07-04 to calculate a 25 75 quantile
    # and then we examine if the 2007-07-05 is greater than the upper 25 quantile, if yes, write 1
    # similiarly ,if the 2007-07-05 is smaller than the lower 25 quantile, if yes, write -1
    # the output is DATETIME(pd.timestamp), Date(datetime.date), Time(datetime.time), Prediction(1,0,-1)
    def actionlist_generator(self, startn=13):
        self.actionlist=[]
        stepsize=round(self.TimestampSignal.shape[0]/len(self.TimestampSignal['Date'].unique()))
        startpoint=startn*stepsize
        endpoint=int(self.TimestampSignal.shape[0]/stepsize)*stepsize-stepsize
        for i in range(startpoint,(endpoint+1),stepsize):
            KnownState=self.TimestampSignal[:i]
            Qall=self.get_quantile_by_time(KnownState,quantile1=25,quantile2=75)
            
            # find that day (both prediction and mins data)
            PredictionThatday=self.TimestampSignal[i:(i+stepsize)]
            print (PredictionThatday['Date'].iloc[0])
            PredictionThatday=PredictionThatday['Prediction'].copy().as_matrix()
        
             # if we will need to do anything that day
            PredictionThatday[PredictionThatday<Qall[:,0]]=-1
            PredictionThatday[PredictionThatday>Qall[:,1]]=1 
            PredictionThatday[(PredictionThatday>Qall[:,0]) &
            (PredictionThatday<Qall[:,1])]=0
         
            self.actionlist.append(PredictionThatday)
            
        self.actionlist=np.concatenate(self.actionlist)
        DATETIME=self.TimestampSignal[['DATETIME','Date','Time']][startpoint:(endpoint+stepsize)]
        DATETIME['Prediction']=self.actionlist
        self.actionlist=DATETIME
    
    
    
    # find the first set of transaction: buy and then sell, or short and then cover 
    # i.e. find the first example of pair 1,-1 or -1,1
    # if either actionindex1=='end' or actionindex2=='end', then we shouldn't preceed forward
    # action is a munpy array or a pandas series
    def trading_index_finder(self,actions):
        # get the index for the first nonzero
        try:
            actionindex1=np.where(actions==1)[0][0]
        except:
            actionindex1='end'
            actionindex2='end'      
            
        try:
            if (actions.iloc[actionindex1]==1):
                actionindex2=np.where(actions==-1)[0]
                actionindex2=actionindex2[actionindex2>actionindex1][0]
        except:
            actionindex2='end'       
            
        return [actionindex1,actionindex2]  
        
        
    # the function returns two values in list form
    # (1) a dataframe with first column being datetime.date, it can be duplicated.
    # as many transactions can be made on a single day. 
    # e.g. many times of stoploss, close the position at a day open. reopen in the mid of the day
    # second column being returns of a set of these transactions
    # (2) the second value is the ending datetime   
    # the DTtradep must be a dataframe ['Date','Time','DATETIME','close'] 
    def crossday_long_with_stoploss(self,r,DTtradep,opencost,closecost,closecost2):
        minr=np.where(DTtradep['close']<DTtradep['close'].iloc[0]*(1-r))[0]
        tradingvalue=[]
        if len(minr)!=0: # stoploss occured
            # get the rows before the stoploss time
            interprice=DTtradep[:(minr[0]+1)]
            interdates=interprice['Date'].unique()
            print ("long stoploss occured! "+str(interprice['DATETIME'].iloc[-1]) +"\n")
        else: # if no stoploss happens 
            interprice=DTtradep
            interdates=interprice['Date'].unique()
        
        # if this is a intraday trade
        if (len(interdates)<2):
            tradingvalue.append(self.long(interprice['close'].iloc[0],interprice['close'].iloc[-1],opencost,closecost2))
        
        # if this is not a intraday trade
        if (len(interdates)>=2):
            # get the first day of trading return 
            # because the cost of opening, we have to do that seperate
            closeprev=interprice['close'].iloc[0]
            closethatday=interprice['close'][interprice['Date']==interdates[0]].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,opencost,0))    

            for i in range(1,len(interdates)-1):
                #  get the close price previous day
                closeprev=interprice['close'][interprice['Date']==interdates[(i-1)]].as_matrix()[-1]
                # get the close price today
                closethatday=interprice['close'][interprice['Date']==interdates[i]].as_matrix()[-1]
                tradingvalue.append(self.long(closeprev,closethatday,0,0))
                
            # get the last day of trading return 
            # because the cost of closing, we have to do that seperate            
            closeprev=interprice['close'][interprice['Date']==interdates[len(interdates)-2]].as_matrix()[-1]
            closethatday=interprice['close'].as_matrix()[-1]
            tradingvalue.append(self.long(closeprev,closethatday,0,closecost))  
            
        datevalues=pd.DataFrame([interdates,tradingvalue]).transpose()
        datevalues.columns=['Date','Returns']
        
        endperiod=interprice['DATETIME'].iloc[-1]
        
        return [datevalues,endperiod]
        
        
    # calculate the long short combo
    # actionlist is not given in this case
    # assume we can only do long, but currently permit close the long position intraday
    # to make decision every 30 mins and the decided if we need to hold the position for another day
    # r is how much percentage rate do we need to do stoploss 
    # Type is LongOnly ShortOnly LongShort 
    def crossday_fixedstoploss_mins_value_everyday(self, r):
        self.datevalues=[]
    
        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
        try:
            actionlist=self.actionlist
        except:
            self.actionlist_generator(startn=13)
            actionlist=self.actionlist
        

        while (len(actionlist)>0):
            
            # find the first set of transaction: buy and then sell, or short and then cover 
            [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
            
            # that is the end of a loop, break out of the loop
            if ((actionindex1=='end') or (actionindex2=='end')):
                break
            
            [Datetime1,Action1]=actionlist[['DATETIME','Prediction']].iloc[actionindex1]
            [Datetime2,Action2]=actionlist[['DATETIME','Prediction']].iloc[actionindex2]
            
            if (Datetime1.date()==Datetime2.date()):
                [Datetime2,Action2]=actionlist[['DATETIME','Prediction']][(actionlist['Date']>Datetime2.date()) & 
                (actionlist['Prediction']==-1)].iloc[0]
            
            # get the trading price
            try:
                tradep=self.portfolio_value(Datetime1,Datetime2,False)
            except:
                actionlist=actionlist[actionlist['DATETIME']>Datetime2]
                print (str(Datetime2)+" error!\n")
                continue
            
            # if no portfolio value is there, go to next loop
            if len(tradep)==1:
                actionlist=actionlist[actionlist['DATETIME']>Datetime2]
                continue
                
            #tradep['close']=tradep['close'].astype(float)
        
            if (Action1==1):
                payoff=self.crossday_long_with_stoploss(r,tradep,self.opencost,self.closecost,self.closecost)
                self.datevalues.append(payoff[0]) 
            
            # update the actionlist
            actionlist=actionlist[actionlist['DATETIME']>payoff[1]]
            print (payoff[1])
            
        return self.datevalues



#BacktestMinutesStock=backtest_minutes_stock(TimestampSignal,TimestampPriceFolder,DateStocklist,opencost,closecost)
#BacktestMinutesStock.actionlist_generator()
#BacktestMinutesStock.actionlist=BacktestMinutesStock.actionlist[5050:]
#BacktestMinutesStock.actionlist=BacktestMinutesStock.actionlist[:-801]
#BacktestMinutesStock.crossday_fixedstoploss_mins_value_everyday(0.05)
#datevalues=pd.concat(BacktestMinutesStock.datevalues)
#np.cumsum(datevalues.iloc[:,1])
#
#TimestampPriceFolder='/home/mao/Documents/DataAdjusted/'
#DateStocklist=datestocklist
#opencost,closecost=1/1000,1/1000





# backtest the stock based on daily bar
# only used for alpha like method. i.e. long only
class backtest_daily_stock:
    
    # DateStocklist is a dataframe contains at least ['Date','Code'], 'Weight' is optional
    # it is the stock code selected at certain date 
    # 'DATETIME' is a datetime.datetime object
    # DailyData is a dictionary containing the [open, high, low, close, volumn, amount]
    # the KEY of DailyData MUST BE THE SAME AS the CODE in DateStocklist 
    def __init__(self,DateStocklist,DailyData,opencost,closecost):
        self.DailyData=DailyData
        self.DateStocklist=DateStocklist
        self.opencost=opencost
        self.closecost=closecost
        
        for code in self.DailyData.keys():
            self.DailyData[code]=self.DailyData[code].sort_values(by='Date')
        
        if ('Weight' in DateStocklist.columns):
            self.Weight=True
        else:
            self.Weight=False

    # calculate the returns from long operations
    # given open price, close price, cost of open the position, cost for close the position
    def long(self,openprice,closeprice,opencost,closecost):
        return ((closeprice*(1-closecost))/(openprice*(1+opencost))-1)
        
        
    # detect if there is a limit-up for that single stock 
    # the input is a datetime and close object 
    # i.e must contain ['DATETIME','close','low']
    # the return will be a bool
    # either True(there is a limit up) or False, there isn't any limit up
    def detect_limit_up(self, TimestampPrice, timestamp1):
        BoolTime=TimestampPrice['Date']<timestamp1
        Prevclose=float(TimestampPrice['close'][BoolTime].as_matrix()[-1])
        Currentclose=float(TimestampPrice[TimestampPrice['Date']==timestamp1]['low'].as_matrix()[0])
        return ((Currentclose/Prevclose)-1)>0.0995


    # calculate the portfolio value from one time to another time
    # timestamp1 and timestamp2 are two datetime.date object
    def portfolio_value(self, timestamp1, timestamp2, VolumeWeighted=True):
        portfolio=self.DateStocklist['Code'][self.DateStocklist['Date']==timestamp1]
        portfolio=portfolio.as_matrix().tolist()
        # if there is no stock in the portfolio list
        if len(portfolio)==0:
            print ("Warning: No Stock is selected!\n")
            return [np.nan]
        
        # store all stock price in stockprice
        stockprices=[]
        for code in portfolio:  
            try:
                TimestampPrice=self.DailyData[code]
                
                # Determine if there is a limit up for that single stock
                # if yes, omit that stock 
                if self.detect_limit_up(TimestampPrice,timestamp1):
                    continue

                stockprice=TimestampPrice[(TimestampPrice['Date']>=timestamp1) & \
                (TimestampPrice['Date']<=timestamp2)]
                
                # all the other features are price related
                stockpriceDate=stockprice['Date']
                stockprice=stockprice.drop(['Date','volumn','amt'], axis=1)
                
                
                # if volume weighted, then normalize everything starting from 1
                if VolumeWeighted==False:
                    stockpriceOHLC=stockprice/stockprice['open'].iloc[0]
                    stockpriceOHLC['Code']=code
                    stockpriceOHLC['Date']=stockpriceDate
                    stockprices.append(stockpriceOHLC)
                else:
                    stockprice['Code']=code
                    stockprice['Date']=stockpriceDate
                    stockprices.append(stockprice)
            except:
                print (code+" missing!\n") # if nothing is retrieved 
          


        
        # the control the position
        if self.Weight==True:
            for i in range(len(stockprices)):
                W=self.DateStocklist['Weight'][(self.DateStocklist['Date']==stockprices[i]['Date'].iloc[0]) & \
                (self.DateStocklist['Code']==stockprices[i]['Code'].iloc[0])].as_matrix().tolist()[0] 
                stockprices[i]=stockprices[i]*W
        

        # find the most common length and stick to it.
        #L=[len(x) for x in stockprices]
        #(most_common,num_most_common) = [x for x in Counter(L).most_common() if x[0]!=0][0]
        #stockprices=list(compress(stockprices,[len(x)==most_common for x in stockprices]))

       
        # find the portfolio level price
        #combovalue=[x[['open','high','low','close']] for x in stockprices]
        #combovalueconcat=pd.DataFrame()
        #for value in combovalue:
            #value=value.reset_index(drop=True)
            #combovalueconcat=pd.concat((combovalueconcat,value))
        
        #combovalueconcat=combovalueconcat.astype(float)
        #meanvalue=combovalueconcat.groupby(combovalueconcat.index).mean()  
        

        combovalueconcat=pd.DataFrame()
        for value in stockprices:
            value=value.reset_index(drop=True)
            combovalueconcat=pd.concat((combovalueconcat,value))
        
        colnames=combovalueconcat.columns - set(['Code','Date'])
        combovalueconcat[colnames]=combovalueconcat[colnames].astype(float)
        combovaluegrouped=combovalueconcat.groupby('Date')
        meanvalue=combovaluegrouped[colnames].agg(np.mean)        
        
        # add date in it
        meanvalue=meanvalue.reset_index()
        
        return meanvalue
    

    
    # calculate the cost for portfolio rebalancing given two portfolios(numpy array)
    # portfolio1 and portfolio2 are two dataframe with ['Date','Code']
    # return a list of two items, opencost adjuster and close cost adjuster 
    def rebalancing_cost_coff(self, portfolio1, portfolio2):
        if self.Weight==True:
            portfolio=portfolio1.merge(portfolio2, on='Code', how='outer')
            portfolio=portfolio.fillna(value=0)
            portfolio['chg']=portfolio['Weight_x']-portfolio['Weight_y']
            
            # calculate the Opencost Adjuster
            OpencostAdjuster=abs(portfolio['chg'][portfolio['chg']<0].sum())/portfolio['Weight_y'].sum()
            # calculate the Closecost Adjuster
            ClosecostAdjuster=portfolio['chg'][portfolio['chg']>0].sum()/portfolio['Weight_x'].sum()
        else:
            OpencostAdjuster=np.mean(~np.in1d(portfolio2,portfolio1))
            ClosecostAdjuster=np.mean(~np.in1d(portfolio1,portfolio2))
        return [OpencostAdjuster,ClosecostAdjuster]

        
    # calculate the cost for portfolio rebalancing given two portfolios(numpy array)
    # timestamp1, timestamp2 are two datetime.date object
    def rebalancing_cost_with_time(self, timestamp1, timestamp2):
        if self.Weight==True:
            portfolio1=self.DateStocklist[['Code','Weight']][self.DateStocklist['Date']==timestamp1]
            portfolio2=self.DateStocklist[['Code','Weight']][self.DateStocklist['Date']==timestamp2]
        else:
            portfolio1=self.DateStocklist['Code'][self.DateStocklist['Date']==timestamp1].as_matrix()
            portfolio2=self.DateStocklist['Code'][self.DateStocklist['Date']==timestamp2].as_matrix()
        return self.rebalancing_cost_coff(portfolio1, portfolio2)
    
        

       
    # calculate the payoff of the portfoilo overtime
    def crossday_fixedstoploss_days_value_everyday(self,VolumeWeighted):
        
        self.datevalues=[]
        
        Dates=self.DateStocklist['Date'].unique()
        Dates=sorted(Dates)
        
        for i in range(len(Dates)-1):
            # get the trading price
            try:
                tradep=self.portfolio_value(Dates[i],Dates[i+1],VolumeWeighted)
                [OpencostAdjuester,ClosecostAdjuester]=self.rebalancing_cost_with_time(Dates[i],Dates[i+1])
            except:
                print (str(Dates[i])+" error!\n")
                i=i+1
                continue
            
            # if no portfolio value is there, go to next loop
            if len(tradep)==1:
                print (str(Dates[i])+" error!\n")
                i=i+1
                continue
            
            payoff=self.long(tradep['last30Mean'].iloc[0],tradep['close'].iloc[-1],
                             OpencostAdjuester*self.opencost,
                             ClosecostAdjuester*self.closecost)
            
            print (str(Dates[i])+" succeed!\n")
            self.datevalues.append([Dates[i+1],payoff])
            
        return self.datevalues



#BacktestDailyStock=backtest_daily_stock(DateStocklist,DailyData,1.5/1000,1.5/1000)
#BacktestDailyStock.rebalancing_cost_with_time(timestamp1, timestamp2)
#BacktestDailyStock.portfolio_value(timestamp1, timestamp2, False)
#BacktestDailyStock.crossday_fixedstoploss_days_value_everyday(VolumeWeighted=True)
#datevalues=pd.DataFrame(BacktestDailyStock.datevalues)
#datevalues.columns=['Date','Return']
#datevalues['CumSum']=datevalues['Return'].cumsum()
#datevalues.plot()

#timestamp1, timestamp2=datetime.date(2016,2,29),datetime.date(2016,3,7)
#BacktestDailyStock.portfolio_value(timestamp1, timestamp2,True)









# the input is a transaction series with date and value in simple interest
# we will assume the simple interest will always be starting from 1 
# normally it is used to calculate the result after hedge, so on a daily basis
class Hedged_Daily:
    def __init__(self, TimestampValue):
        self.TimestampValue=TimestampValue
        self.TimestampValue.columns=['Date','Value']
    
    
    # HedgedUnderlyingDaily is some underlying for hedge  
    def hedged_daily(self, HedgedUnderlyingDaily):
        HedgedUnderlyingDaily['Returns']=self.Compound_to_Return(HedgedUnderlyingDaily['close'])
        self.TimestampValue['ValueReturns']=self.TimestampValue['Value'].diff(periods=1)
        
        StartDate=min(self.TimestampValue['Date'].iloc[0],HedgedUnderlyingDaily['Date'].iloc[0])
        EndDate=max(self.TimestampValue['Date'].iloc[-1],HedgedUnderlyingDaily['Date'].iloc[-1])
        
        HedgedUnderlyingDaily=HedgedUnderlyingDaily[(HedgedUnderlyingDaily['Date']>=StartDate) \
        & (HedgedUnderlyingDaily['Date']<=EndDate)]
        self.TimestampValue=self.TimestampValue[(self.TimestampValue['Date']>=StartDate) & (self.TimestampValue['Date']<=EndDate)]
        
        hedgeddaily=self.TimestampValue[['Date','ValueReturns']].merge(HedgedUnderlyingDaily[['Date','Returns']],on='Date')
        RelativeReturn=hedgeddaily['ValueReturns']-hedgeddaily['Returns']
        RelativeReturn=pd.DataFrame([hedgeddaily['Date'].as_matrix(),RelativeReturn.as_matrix()]).transpose()
        RelativeReturn.columns=['date','value']
        RelativeReturn['value'].iloc[0]=1
        RelativeReturn['value']=np.cumsum(RelativeReturn['value'])
        return RelativeReturn
        
        
    # value is a price series, in compound calculation of value
    def Compound_to_Return(self, value):
        SimpleReturn=value.diff(periods=1)[1:].as_matrix()/value[:-1].as_matrix()
        SimpleReturn=np.insert(SimpleReturn,0,np.nan)
        return SimpleReturn

















# to manually set signal according to certain criteria
class Signal_Filter:
    def __init__(self):
        pass
    
    # halt a position if already decline or increase by certain percent campare to today's open
    # TimestampSignal has columns as ['Date', 'Prediction', 'Time', 'DATETIME']
    # TimestampPrice ['Date', 'Time', 'DATETIME', 'open', 'high', 'low', 'close', 'amt', 'volumn']
    # direction == 1 is moving up
    # direction == -1 is moving down
    # TimestampSignal['Prediction'] is either 1 or -1
    def already_move_by_n_pct(self, TimestampPrice, TimestampSignal, direction, bypct):
        unopen=[]
        for date in TimestampSignal['Date'].unique():
            IntradaySignal=TimestampSignal[TimestampSignal['Date']==date]
            if direction==1:
                OpenPos=np.where(IntradaySignal['Prediction']==1)
                if len(OpenPos)==0:
                    continue
                else: 
                    OpenDateTime=IntradaySignal['DATETIME'].iloc[OpenPos]
                    IntradayPrice=TimestampPrice[TimestampPrice['Date']==date]
                    OpenPrices=IntradayPrice[['DATETIME','close']][np.in1d(IntradayPrice['DATETIME'],OpenDateTime)]
                    moveby=OpenPrices['close']/IntradayPrice['close'].iloc[0]-1
                    unopenDATETIME=OpenPrices['DATETIME'][(moveby>bypct).as_matrix()]
                    if len(unopenDATETIME)!=0:
                        unopen.append(unopenDATETIME)
            elif direction==-1:
                OpenPos=np.where(IntradaySignal['Prediction']==-1)
                if len(OpenPos)==0:
                    continue
                else: 
                    OpenDateTime=IntradaySignal['DATETIME'].iloc[OpenPos]
                    IntradayPrice=TimestampPrice[TimestampPrice['Date']==date]
                    OpenPrices=IntradayPrice[['DATETIME','close']][np.in1d(IntradayPrice['DATETIME'],OpenDateTime)]
                    moveby=OpenPrices['close']/IntradayPrice['close'].iloc[0]-1
                    unopenDATETIME=OpenPrices['DATETIME'][(moveby<bypct).as_matrix()]
                    if len(unopenDATETIME)!=0:
                        unopen.append(unopenDATETIME)
            else:
                print ('Please enter a direction of either 1 or -1 !\n')
                
        # set the open signal to which from today's open has already move by certain percent        
        unopen=pd.concat(unopen)
        TimestampSignal['Prediction']=TimestampSignal['Prediction'][np.in1d(TimestampSignal['DATETIME'],unopen)]=0
        return TimestampSignal




# a class to construct the portfolio  
class Stock_Portfolio_Construction:
    
    def __init__(self):
        pass
    
    
    # TimestampSignalStock is a dataframe with ['Date','Code','Prediction'] 
    # quantile is like [0.2,0.9] 
    # Date is a datetime.date object 
    # return a dataframe containing Date and Code and Prediction
    def Select_n_Quantile(self, TimestampSignalStock, Date, quantile, port):
        
        if (quantile[0]>=quantile[1]):
            return None
        
        TimestampSignalStock.columns=['Date','Code','Prediction']
        TimestampSignalStock=TimestampSignalStock.sort_values(by='Date')
        TimestampSignalStockDate=TimestampSignalStock[TimestampSignalStock['Date']==Date]

        TimestampSignalStockDate=TimestampSignalStockDate[np.in1d(TimestampSignalStockDate['Code'], port)]        
        TimestampSignalStockDate=TimestampSignalStockDate.sort_values(by='Prediction')
   
        startpoint=int(len(TimestampSignalStockDate)*quantile[0])
        endpoint=int(len(TimestampSignalStockDate)*quantile[1])
        
        return TimestampSignalStockDate[startpoint:endpoint]
        
        
    # TimestampSignalStock is a dataframe with ['Date','Code','Prediction'] 
    # to make change to last n quantile stock and use certain quantile to fill in
    # BeginPort is the portfolio we start with, Begindate is the date we shart with
    # BeginPort must be in the prediction range of TimestampSignalStock
    # quantilein is the quantile range that we let the new stock to be in
    # quantileout is the quantile range that we let the old stock to be out  
    def Rolling_Change_Worst(self, TimestampSignalStock, BeginPort, Begindate, quantilein, quantileout, inpadding, outpadding):
        
        Portfolio=dict()
        Portfolio[Begindate]=BeginPort
        
        if (quantilein[0]>=quantilein[1]):
            return None
            
        if (quantileout[0]>=quantileout[1]):
            return None
            
        TimestampSignalStock.columns=['Date','Code','Prediction']
        TimestampSignalStock=TimestampSignalStock.sort_values(by='Date') 
        
        TimestampSignalStock=TimestampSignalStock[[TimestampSignalStock['Date']>=Begindate]]
        
        for date in TimestampSignalStock['Date'].unique():
            OutPort=self.Select_n_Quantile(TimestampSignalStock, date, quantileout, BeginPort)
            
            TimestampSignalStockToday=TimestampSignalStock[[TimestampSignalStock['Date']==date]]
            Port = list(set(TimestampSignalStockToday['Date']) - set(BeginPort))
            
            InPort=self.Select_n_Quantile(TimestampSignalStock, date, quantilein, Port)
            
            if len(OutPort)==len(InPort):
                BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code']))    
            
            # the number of stock moves out is bigger than move in
            # that is we should only truncate and find some of the stocks from InPort
            elif len(OutPort)<len(InPort):
                if inpadding=='small':
                    InPort=InPort.sort_values(by='Prediction')[:len(OutPort)]
                    BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code'])) 
                    
                elif inpadding=='large':
                    InPort=InPort.sort_values(by='Prediction')[(-len(OutPort)+1):]
                    BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code'])) 
                    
                elif inpadding=='center':
                    InPort=InPort.sort_values(by='Prediction')
                    startpoint=(len(InPort)//2)-(len(OutPort)//2)
                    InPort=InPort[startpoint:(startpoint+len(OutPort))]
                    BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code']))
                    
                else:
                    print ('small/large/center must be inputed!\n')
            
            # the number of stock move in is bigger than move out
            # that is we should only truncate and find some of the stocks from OutPort
            elif len(OutPort)>len(InPort):
                if outpadding=='small':
                    OutPort=OutPort.sort_values(by='Prediction')[:len(InPort)]
                    BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code'])) 
                    
                elif inpadding=='large':
                    OutPort=OutPort.sort_values(by='Prediction')[(-len(OutPort)+1):]
                    BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code'])) 

                elif inpadding=='center':
                    OutPort=OutPort.sort_values(by='Prediction')
                    startpoint=(len(OutPort)//2)-(len(InPort)//2)
                    OutPort=OutPort[startpoint:(startpoint+len(InPort))]
                    BeginPort=list(set(BeginPort) - set(OutPort['Code']) - set(InPort['Code'])) 
                    
                else:
                    print ('small/large/center must be inputed!\n')
                
            Portfolio[date]=BeginPort
        return Portfolio


    # to select the stocks that rise less, by choose the less rised ones
    # DateStocklist is a dataframe with columns ['Date','Code']
    # IntradayReturnData must have a ['Date', 'Code', 'PriceChange']
    # n is the n lowest stock with value of Pricechange  
    def select_the_intraday_less_rised(self, DateStocklist ,IntradayReturnData, n):
        CodeDateReturn=DateStocklist.merge(IntradayReturnData, on=['Date','Code'])
        CodeDateReturnGrouped=CodeDateReturn.groupby('Date')
        CodeDateReturn=CodeDateReturnGrouped.apply(lambda x: x.sort_values(by='PriceChange').head(n))
        CodeDateReturn.index.names = ['Index',None]
        CodeDateReturn=CodeDateReturn.reset_index(drop=True)
        return CodeDateReturn[['Date','Code']]



#    # to make decision every 30 mins and the dicided if we need to hold the position for another day
#    # r is how much percentage rate do we need to do stoploss 
#    # Type is LongOnly ShortOnly LongShort 
#    # main contract Rolling forward 
#    def crossday_fixedstoploss_days_value_everyday_Timeout_Rolling(self,r,Type='LongShort'):
#        datevalues=pd.DataFrame()
#    
#        # generate a actionlist of 1(buy,cover), 0(maintain the position before), -1(short,sell)
#        try:
#            actionlist=self.actionlist
#        except:
#            self.actionlist_generator(startpoint=100)
#            self.reconstruct_data_to_weekly()
#            actionlist=self.actionlist
#        
#
#        while (len(actionlist)>1):
#            
#            # find the first set of transaction: buy and then sell, or short and then cover 
#            [actionindex1,actionindex2]=self.trading_index_finder(actionlist['Prediction'])
#            
#            # that is the end of a loop, break out of the loop
#            if (actionindex1=='end'):
#                break
#            
#            if (actionindex2=='end'):
#                [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
#                [Date2,Action2]=actionlist[['Date','Prediction']].iloc[-1]
#                
#            if ((actionindex1!='end') & (actionindex2!='end')):
#                [Date1,Action1]=actionlist[['Date','Prediction']].iloc[actionindex1]
#                [Date2,Action2]=actionlist[['Date','Prediction']].iloc[actionindex2]
#            
#
#            
#            Date1=self.TimestampPrice['Date'].iloc[np.where(self.TimestampPrice['Date']>Date1)[0][0]]
#            Date2=self.TimestampPrice['Date'].iloc[np.where(self.TimestampPrice['Date']>Date2)[0][0]]
#            
#            # get the trading price 
#            DTtradep=self.TimestampPrice[(self.TimestampPrice['Date']>=Date1) & (self.TimestampPrice['Date']<=Date2)]
#        
#            
#            if (Action1==1):
#                if Type=='LongOnly' or Type=='LongShort':
#                    payoff=self.crossday_long_with_stoploss(r,DTtradep,self.opencost,self.closecost)
#                    datevalues=datevalues.append(payoff[0]) 
#                else:
#                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:],[0]*(len(DTtradep['Date'])-1)]).transpose()
#                    payoffvalue.colnames=['Date','Returns']
#                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]
#
#
#            if (Action1==(-1)):
#                if Type=='ShortOnly' or Type=='LongShort':
#                    payoff=self.crossday_short_with_stoploss(r,DTtradep,self.opencost,self.closecost)
#                    datevalues=datevalues.append(payoff[0])
#                else:
#                    payoffvalue=pd.DataFrame([DTtradep['Date'].iloc[1:],[0]*len(DTtradep['Date']-1)]).transpose()
#                    payoffvalue.colnames=['Date','Returns']
#                    payoff=[payoffvalue,DTtradep['Date'].iloc[-1]]                    
#            
#            # update the actionlist
#            actionlist=actionlist[actionlist['Date']>=payoff[1]]
#            print (payoff[1])
#            
#        return datevalues





 

#backtestdays=backtest_days(TimestampSignal,TimestampPrice,1.5/10000,1.5/10000,23/10000)
##Q=backtestdays.get_quantile_by_time(TimestampSignal[:100],quantile1=25,quantile2=75)
#backtestdays.actionlist_generator(startpoint=100)
#backtestdays.find_start_of_trading_time()
#backtestdays.reconstruct_data_to_weekly()
#
#backtestdays.crossday_long_with_stoploss(r=0.07,DTtradep=DTtradep,opencost=1.5/10000,closecost=1.5/10000)
#backtestdays.crossday_short_with_stoploss(r=0.07,DTtradep=DTtradep,opencost=1.5/10000,closecost=1.5/10000)
#ss=backtestdays.crossday_fixedstoploss_days_value_everyday_Timeout(0.03,'LongShort')