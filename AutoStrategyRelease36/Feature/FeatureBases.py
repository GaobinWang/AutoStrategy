# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 11:12:09 2017


###############################################################################
#                                                                             #
#                                FeatureBases                                 #
#                   create features for AutomatedCTAGenerator                 #                        
#                        Mao ZHOU (2017) Python Code                          #
#                               Jan 17, 2017                                  #
#                          copy right Mao ZHOU 2017                           #
#                                                                             #
###############################################################################


"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
import talib


# TA-Lib is a library for calculation of technical indicator
# while talib_supplement is a supplement for calculation of technical indicator
# the class is different from withinday or cross day, because it is not timestamp based
# otherwise it is rolling forward based 
# the input and the output of the this class are all numpy array
class talib_supplement:
            
    # CR_helper is to calculate CR, based on high low close 
    # high low close are numpy arrays
    # returns a single CR value
    def __CR_helper(self,highprices,lowprices,closeprices):
        """
        CR_helper(highprices,lowprices,closeprices)
        highprices: real
        lowprices: real
        closeprices: real
        
        
        Output(list): a np.array of CR
        
        infer from __doc__
        """
        M=(2*closeprices+highprices+lowprices)/4
        YM=np.insert(M[:-1],0,np.nan)
        P1All=highprices-YM
        P1=np.nansum(P1All[P1All>0])
        P2All=YM-lowprices
        P2=np.nansum(P2All[P2All>0])
        CR=P1/P2*100
        return CR

    # CR is to calculate CR and rolling forward, n is the lag
    # high low close are numpy arrays
    # return is a set of CRs 
    def CR(self,highprices,lowprices,closeprices,n=20):
        """
        CR(highprices,lowprices,closeprices,n)
        highprices: real
        lowprices: real
        closeprices: real
        n: 20
        
        Output(np.array): a np.array of rolling CR
        
        infer from __doc__
        """
        CRall=[np.nan]*(n-1)
        if len(highprices)!=len(lowprices):
            print ("length of high, low, close don't match")
            return None             
            
        if len(highprices)!=len(closeprices):
            print ("length of high, low, close don't match")
            return None
        
        for i in range(n,(len(closeprices)+1)):
            CRall.append(self.__CR_helper(highprices[(i-n):i],lowprices[(i-n):i],closeprices[(i-n):i]))
            
        return CRall
        
     
    # linear_regression_slope_outlier_helper is to see the outlier of the linear regression
    # prices is any numpy array
    def __linear_regression_slope_outlier_helper(self, prices):
        """
        linear_regression_slope_outlier_helper(prices)
        highprices: real
        lowprices: real
        closeprices: real
        n: 20
        
        Output(np.array): a np.array of relative deviation from the linear regression
        
        infer from __doc__
        """        
        prices=prices.astype(float).tolist()
        index=np.arange(len(prices))+1
        regression_matrix=pd.DataFrame({"price": prices, "index": index.tolist()})
        regression_model = sm.ols(formula="price ~ index", data=regression_matrix).fit()
        Relativedeviation=(prices-regression_model.fittedvalues)/regression_model.fittedvalues
        return Relativedeviation.as_matrix()
        
        
    # linear_regression_slope_outlier is to calculate the outlier of the linear regression and rolling forward
    # stepsize is the number of rows in a given bar (say in ten minutes bar, we have ten rows)
    # n is how many bars we need, say we will need 24 bars in one calculation
    def linear_regression_slope_outlier(self, prices, n=20, stepsize=10):
        """
        linear_regression_slope_outlier_helper(prices)
        prices: real
        n: 20
        stepsize: 10
        
        Output(np.array): a np.array of rolling relative deviation from the linear regression
        
        infer from __doc__
        """   
        deviationall=[np.nan]*(n-1)
        for i in range((stepsize*n-1),len(prices),stepsize):
            deviation=self.__linear_regression_slope_outlier_helper(prices[(i-stepsize*n+1):(i+1)])
            deviation=float(deviation[-1])
            deviationall.append(deviation)
        return deviationall
        
    
    # RSI is a standardized form of RSI after Fisher-transformation
    # prices are a numpy array
    def fisher_RSI(self,prices,n=60):
        """
        fisher_RSI(prices,n)
        prices: real
        n: 60
        
        Output(np.array): a np.array of rolling Fisher RSI
        
        infer from __doc__
        """         
        prices=prices.astype(float)
        RSIs=talib.RSI(prices,n)
        x=RSIs/100-0.5 # transform into x for fisher transformation
        fisherRSI=0.5*np.log((1+x)/(1-x)) # fisher transformation
        return fisherRSI
        
    # calculate the max price divided by the current price
    # n is how many bars we need, say we will need 24 bars in one calculation
    # close price and high price must have the same length and referring to the same DATETIME
    def maxprice_to_currentprice(self,highprices,closeprices,n=20):
        """
        maxprice_to_currentprice(highprices,closeprices,n)
        highprices: real
        closeprices: real
        n: 20

        Output(np.array): a np.array of maxprice_to_currentprice
        
        infer from __doc__        
        """
        maxcurrentall=[np.nan]*(n-1)
        for i in range(n,(len(closeprices)+1)):
            maxcurrent=highprices[(i-n):i].max()/closeprices[(i-n):i][-1]-1
            maxcurrentall.append(maxcurrent)
        return np.array(maxcurrentall)


    # calculate the min price divided by the current price
    # n is how many bars we need, say we will need 24 bars in one calculation
    # close price and low price must have the same length and referring to the same DATETIME
    def minprice_to_currentprice(self,lowprices,closeprices,n=20):
        """
        minprice_to_currentprice(lowprices,closeprices,n)
        lowprices: real
        closeprices: real
        n: 20

        Output(np.array): a np.array of minprice_to_currentprice
        
        infer from __doc__        
        """        
        
        mincurrentall=[np.nan]*(n-1)
        for i in range(n,(len(closeprices)+1)):
            mincurrent=lowprices[(i-n):i].min()/closeprices[(i-n):i][-1]-1
            mincurrentall.append(mincurrent)
        return np.array(mincurrentall)
    
    
    # LLT is called 低延迟趋势线
    # alpha is the coefficient 
    def __LLT(self,prices,alpha=0.05):
        """
        LLT(prices,alpha=0.05)
        prices: real
        alpha: 0.05

        Output(np.array): a np.array of LLT prices
        
        infer from __doc__        
        """   
        LLTval=[]
        prices=prices.astype(float).tolist()
        LLTval.append(prices[0])
        LLTval.append(prices[1])

        for i in range(len(prices)-2):
            newLLT=(alpha-alpha**2/4)*prices[len(LLTval)]+(alpha**2/2)*prices[len(LLTval)-1]-\
                    (alpha-0.75*alpha**2)*prices[len(LLTval)-2]+2*(1-alpha)*LLTval[-1]-\
                    (1-alpha)**2*LLTval[-2]
            LLTval.append(newLLT)
        return LLTval
      
      
    # calculate (approximate) the tangent line of the LLT curve
    # approximate the tangent by using secant line
    # prices is a numpy array
    # n is the starting place to calculate LLT
    def get_tangent_LLT(self, prices, alpha=0.05, n=24 ,secantn=3):
        """
        get_tangent_LLT(prices,alpha, n ,secantn)
        prices: real
        alpha: 0.05
        n: 24
        secantn: 3
        
        Output(np.array): a np.array of tangent LLT slope
        
        infer from __doc__        
        """  
        n=n-1
        tangentLLTall=[np.nan]*n
        LLTprices=self.__LLT(prices,alpha=0.05)
        for i in range(n,len(prices)):
            tangentLLT=(LLTprices[i]-LLTprices[(i-secantn)])/LLTprices[(i-secantn)]
            tangentLLTall.append(tangentLLT)
        return tangentLLTall

    

    # close is a numpy array, n is the how many shifts of days are needed
    # say when n=5, that means the day6's return minus day 1
    def rolling_n_day_return(self,close,n=5):
        """
        rolling_n_day_return(close,n)
        close: real
        n: 24
        
        Output(np.array): a np.array of rolling n day's return
        
        infer from __doc__        
        """  
        closediff=(close[n:]-close[:-n])/close[:-n]
        ncloses=np.concatenate([[np.nan]*n,closediff])
        return ncloses

    
    # DATETIME, openprices, highprices, lowprices, closeprices are all numpy array
    # return a list containing the datetime index and 'up'/'down'
    def close_gap(self,highprices,lowprices):
        """
        close_gap(highprices,lowprices)
        """
        GapIndex=[np.nan]
        for i in range(1,len(highprices)):
            if (highprices[(i-1)]<lowprices[i]):
                GapIndex.append((highprices[i]-lowprices[(i-1)])/highprices[(i-1)])
            elif (lowprices[(i-1)]>highprices[i]):
                GapIndex.append((highprices[i]-lowprices[(i-1)])/lowprices[(i-1)])
            else:
                GapIndex.append(0)
        return np.array(GapIndex)
    

    
    # DATETIME,highprices,closeprices is Timestamp, high, close
    # return 1 if close is at n days high and 0 if not
    def close_at_n_days_high(self,highprices,closeprices,n=24):
        """
        close_at_n_days_high(n,highprices,closeprices)
        close: real
        n: 24
        
        Output(np.array): a np.array of rolling if n day's close large than last close
        
        infer from __doc__        
        """  
        ndayhigh=[]
        for i in range(n,len(closeprices)):
            if (np.max(highprices[(i-n):i]) < closeprices[i]):
                ndayhigh.append(1)
            else:
                ndayhigh.append(0)
        return np.concatenate(([np.nan]*n,ndayhigh))
    
    
    # volume and price relationship
    # to detect the correlation between price and volumn
    # 缩量上涨(01) 缩量下跌(00) 放量下跌(10) 放量上涨(11)
    def __cor_price_vol(self, price, amt):
        """
        cor_price_vol(price, amt)
        price: real
        amt: real
        
        Output(np.array): a np.array of corrlation of price and vol 
        
        infer from __doc__        
        """  
        price=price.astype(float)
        price=price/price[0]
        amt=amt.astype(float)
        amt=amt/amt[0]
        timeindex=np.array(list(range(len(price))))+1
        
        # price and amt correlation with respect to time
        pricecor=np.corrcoef(timeindex,price)[0][1]
        amtcor=np.corrcoef(timeindex,amt)[0][1]
        
        if (amtcor>0 and pricecor>0):
            return '11'
        elif (amtcor<0 and pricecor>0):
            return '01'
        elif (amtcor>0 and pricecor<0):
            return '10'
        elif (amtcor<0 and pricecor<0):
            return '00'
        else:
            return '0'
   
    
    # the returns is a numpy array as returns of a underlying asset
    # the function aims to count the number of times of current direction
    # prior to and include in this timepoint 
    def _Cont_Direction_Times(self, prices):
        """
        Cont_Direction_Times(prices)
        prices: real
        
        Output(np.array): a np.array of continuous same directions times
        """
        prices=prices.astype(float)
        returns=np.diff(prices)
        
        if ((returns[-1]==0) or (len(returns)==1)):
            return 0
            
        # for each point if they has the same direction as returns of time T    
        SameDirection=((returns[-1]*returns)>0)[:-1]
        # self need to be subtracted
        if all(SameDirection):
            return len(SameDirection)
        elif SameDirection[-1]==True:
            return sum(SameDirection[np.where(SameDirection==False)[0][-1]:])
        else:
            return 0        
        
    # the returns is a numpy array as returns of a underlying asset
    # the function aims to count the number of times of the direction opposite 
    # to current direction
    # prior to this timepoint 
    def _Cont_Opposite_Direction_Times(self, prices):
        """
        Cont_Opposite_Direction_Times(prices)
        prices: real
        
        Output(np.array): a np.array of continuous oppo directions times
        """
        prices=prices.astype(float)
        returns=np.diff(prices)
        
        if ((returns[-1]==0) or (len(returns)==1)):
            return 0
            
        # for each point if they has the same direction as returns of time T
        SameDirection=((returns[-1]*returns)>0)[:-1]
        if any(SameDirection)==False:
            return len(SameDirection)
        elif SameDirection[-1]==False:
            return sum(SameDirection[np.where(SameDirection==True)[0][-1]:]==False) 
        else:
            return 0

 
    # count the continuous direction time
    # type can be either 'Oppo' or 'Same'
    def Count_Cont_Direction_Time(self, prices, Oppo=True):
        """
        Count_Cont_Direction_Time(prices)
        prices: real
        Oppo: True
        
        Output(np.array): a np.array of continuous oppo directions times
        """
        DirectionTime=[np.nan]*2
        if Oppo==False:
            for i in range(2,len(prices)):
                DirectionTime.append(self._Cont_Direction_Times(prices[:(i+1)]))
            return DirectionTime
        elif Oppo==True:
            for i in range(2,len(prices)):
                DirectionTime.append(self._Cont_Opposite_Direction_Times(prices[:(i+1)]))  
            return DirectionTime
        else:
            print ("You must enter a type of either Same or Oppo!\n")
   
    # count the number of times for certain direction   
    # n is the the rolling time period
    def N_Days_Direction_Times(self, prices, direction=True, n=20):
        """
        N_Days_Direction_Times(prices, direction, n)
        prices: real
        direction: True
        n: 20
        """
        prices=prices.astype(float)
        returns=np.diff(prices)
        SameDirection=np.array([np.nan]*(n+1))
        if direction==True:
            for i in range(n,len(returns)):
                SameDirection=np.append(SameDirection,sum(returns[(i-n):(i+1)]>0))
        elif direction==False:
            for i in range(n,len(returns)):
                SameDirection=np.append(SameDirection,sum(returns[(i-n):(i+1)]<0)) 
        else:
            print ("You must enter either 1 or -1!\n")
            
        return SameDirection
        
   
    # the function is based on -国泰君安-数量化专题之五十九:基于阻力的市场投资策略
    # the formula is sum[p_i>p_c](V_i * w_1i * w_2i)/sum(V_j * w_1j * w_2j)
    # w_1j is 成交额距离加权 negative cor: log(1/(abs(p_i-p_c)/p_c))
    # w_2j is 成交额时间加权 positive cor: log(j+1)/log(N+1)
    # amt and close are all numpy array, n is the rolling period
    def resistence_support_volume(self, close, amt, n=20):
        """
        resistence_support_volume(close, amt, n)
        n: 20
        """
        close=close.astype(float)
        amt=amt.astype(float)
        
        RELATIVERESIST=np.array([np.nan]*(n-1))
        
        for i in range(n,(len(close)+1)):
            price_i=close[(i-n):i]
            amt_i=amt[(i-n):i]
            
            p_i=price_i[:-1]
            p_c=price_i[-1]
            
            w_1j=np.log(1/(abs(p_i-p_c)/p_c))
            w_2j=np.log( np.array(list(range(len(p_i)))) +2 ) / np.log(len(p_i)+1)
            
            denominator=np.sum(w_1j*w_2j*amt_i[:-1])
            nominator=np.sum(w_1j[p_i>p_c]*w_2j[p_i>p_c]*amt_i[:-1][p_i>p_c])
            
            RelativeResist=nominator/denominator
            
            RELATIVERESIST=np.append(RELATIVERESIST,RelativeResist)
            
        return RELATIVERESIST
        
        
        
    # find the max drawdown of from very begining 
    # assume a investor unfortunately buy a stock at very high position
    def hold_max_drawdown(self, prices):
        """
        hold_max_drawdown(prices)
        prices: real
        """
        prices=prices.astype(float)
        DrawDown=np.array([])
        for i in range(len(prices)):
            DrawDown_i=(np.max(prices[:(i+1)])-prices[i])/np.max(prices[:(i+1)])
            DrawDown=np.append(DrawDown,DrawDown_i)
        return DrawDown
        
    
    # find the change point of MA crosses
    def cross_change_point(self, prices, periodshort=5, periodlong=20):
        """
        cross_change_point(prices,periodshort,periodlong)
        prices: real
        periodshort: 5
        periodlong: 20
        """
        prices=prices.astype(float)
        MAlong=talib.SMA(prices,periodlong)
        MAshort=talib.SMA(prices,periodshort)
        
        MAdiff=MAshort-MAlong
        Cross=MAdiff[np.isnan(MAdiff)].tolist()
        Cross.append(np.nan)
        MAchange=MAdiff[~np.isnan(MAdiff)]
        
        for i in range(1,len(MAchange)):
            if MAchange[(i-1)]>=0 and MAchange[i]<=0:
                Cross.append(-1)
            elif MAchange[(i-1)]<=0 and MAchange[i]>=0:
                Cross.append(1)
            else:
                Cross.append(0)
        return np.array(Cross)
     
       
    def MAdiff(self, prices, periodshort=5, periodlong=20):
        """
        MAdiff(prices,periodshort,periodlong)
        prices: real
        periodshort: 5
        periodlong: 20
        
        Output(np.array): MAshort/MAlong-1
        """        
        prices=prices.astype(float)
        MAlong=talib.SMA(prices,periodlong)
        MAshort=talib.SMA(prices,periodshort)
        
        MAdiff=MAshort/MAlong-1
        return MAdiff

    # get the price change relative to the move distance 
    # 涨幅/路程
    def price_to_distance(self, prices, n=20):
        """
        price_to_distance(prices, n)
        prices: real
        n: 20
        
        
        Output(np.array): rolling return/ rolling abs dist
        
        infer from __doc__
        """
        returns=np.diff(prices)
        PriceDistance=[np.nan]*(n-1)
        for i in range((n-2),len(returns)):
            PCMD=np.sum(returns[(i-n+2):(i+1)])/np.sum(np.abs(returns[(i-n+2):(i+1)]))
            PriceDistance.append(PCMD)
        return PriceDistance


    # identify the Doji based on the length of abs(close-open), Upper Wick, Lower Shadow
    # h is the mutiplier related to (Upper Wick + Lower Shadow)/length of abs(close-open)
    # from 方正证券 夜空中最亮的星 
    def Doji_Identifier(self, Open, High, Low, Close, h:float):
        """
        Doji_Identifier(Open, High, Low, Close, h)
        Open: real
        High: real
        Low: real
        Close: real
        h: 0.3
        
        
        Output(np.array): Doji_Identifier of 1 and 0, 1 means is Doji, 0 otherwise
        
        infer from __doc__
        """
        Doji=[]
        for i in range(len(Open)):
            soild=np.abs(Close[i]-Open[i])
            UpperWick=High[i]-max(Close[i],Open[i])
            LowerShadow=min(Close[i],Open[i])-Low[i]
            if (UpperWick+LowerShadow)>(soild*h):
                Doji.append(1)
            else:
                Doji.append(0)
        return np.array(Doji)
        
        
    # defined volatility to be RS range estimator
    # return a level 1 std like RSSigma
    def RS_Range_estimator(self, High, Low, Close, Open, n=20):
        """
        RS_Range_estimator(High, Low, Close, n)
        High: real
        Low: real
        Close: real
        Open: real
        n: 20
        
        
        Output(np.array): RS_Range_estimator of volatility
        
        infer from __doc__
        """
        H_tao=np.log(High)-np.log(Open)
        L_tao=np.log(Low)-np.log(Open)
        C_tao=np.log(Close)-np.log(Open)
        
        RSsigmasqr=H_tao*(H_tao-C_tao)+L_tao*(L_tao-C_tao)
        RSsigmasqrSMA=talib.SMA(RSsigmasqr, timeperiod=n)
        return np.sqrt(RSsigmasqrSMA)
    
    
    # YZ estimator is a estimator that defined as 
    # Sigma_YZ^2=Sigma_OJ^2+k*Sigma_SD^2+(1-k)*Sigma_RS
    def YZ_volatility_estimator(self, Open, High, Low, Close, n=20):
        """
        YZ_volatility_estimator(Open, High, Low, Close, n)
        Open: real
        High: real
        Low: real
        Close: real
        n: 30
        
        
        Output(np.array): YZ estimator of volatility
        
        infer from __doc__
        """
        SigmaRS=self.RS_Range_estimator(High, Low, Close, Open. n)
        
        SigmaSD=pd.rolling_std(np.log(Close)-np.log(Open), window=n)
        
        SigmaOJ=pd.rolling_std((Open[1:]-Close[:-1])/Close[:-1], window=n)
        SigmaOJ=np.insert(SigmaOJ, 0, np.nan)
        
        k=0.34/(1.34+(n+1)/(n-1))
        
        SigmaYZsqr=np.square(SigmaOJ)+k*np.square(SigmaSD)+(1-k)*np.square(SigmaRS)
        
        return np.sqrt(SigmaYZsqr)
        
        

    # correlation across time
    # nperiod is the number of period that needed in calculation 
    def Rolling_Cor(self, a, b, nperiod=30, shiftn=5):
        """
        Rolling_Cor(a, b, nperiod)
        a: real
        b: real
        nperiod: 30
        shiftn: 5
        
        Output(np.array): real Corrrelation across a and b
        
        infer from __doc__
        """
        a=a[shiftn:]
        b=b[:-shiftn]
        if len(a)!=len(b):
            print ('in Correlation, two vector must have same length')
            return None
            
        Cors=[np.nan]*(nperiod+shiftn)
        for i in range(nperiod,len(a)):
            cor=np.corrcoef(a[(i-nperiod):i], b[(i-nperiod):i])[0,1]
            Cors.append(cor)
        return np.array(Cors)





class yfeatures:
    """
    calculate y features for machine learning
    """
    
    def __init__(self):
        pass


    # calculate the sharpe ratio for all time period           
    def _Sharpe_Ratio(self,close):
        returns=np.diff(close)
        AvgReturn=np.mean(returns)*np.sqrt(252)
        StdReturn=np.std(returns)
        return AvgReturn/StdReturn
        
            
    def Sharpe_Ratio_all_y(self,close,timeperiod=30):
        """
        Sharpe_Ratio_all_y(close,timeperiod)
        timeperiod: 30
        
        Output(np.array): rolling n periods' Sharpe Ratio
        calculate the sharpe ratio for all timeperiod   
        """
        SRs=[np.nan]*timeperiod
        for i in range(timeperiod,len(close)):
            SRs.append(self._Sharpe_Ratio(close[(i-timeperiod):i]))
        return np.array(SRs)
        
        
    # closes is a numpy array, n is the how many shifts of days are needed 
    def rolling_n_day_return_y(self,close,timeperiod=30):
        """
        rolling_n_day_return_y(close,timeperiod)
        
        close: np.array
        timeperiod: 30
        
        Output(np.array): rolling n periods' return
        say when n=5, that means the day 6's return minus day 1
        """
        closediff=(close[timeperiod:]-close[:-timeperiod])/close[:-timeperiod]
        ncloses=np.concatenate([[np.nan]*timeperiod,closediff])
        return np.array(ncloses)
        
        
    def rolling_n_day_ATR_adj_y(self, high, low, close, timeperiod=30):
        """
        rolling_n_day_ATR_y(high, low, close, timeperiod)
        
        high: np.array
        low: np.array
        close: np.array
        timeperiod: 30
        
        Output(np.array): rolling return/rolling ATR
        """
        ATR=talib.ATR(high, low, close, timeperiod)
        RollingReturn=self.rolling_n_day_return_y(close, timeperiod)
        ATRadj=RollingReturn/ATR
        return np.array(ATRadj)
        
        
    # get the price change relative to the move distance 
    # 涨幅/路程
    def price_to_distance_y(self, real, n=20):
        """
        price_to_distance_y(real, n)
        real: real
        n: 20
        
        
        Output(np.array): rolling return/ rolling abs dist
        
        infer from __doc__
        """
        returns=np.diff(real)
        PriceDistance=[np.nan]*(n-1)
        for i in range((n-1),(len(returns)+1)):
            PCMD=np.sum(returns[(i-n+1):i])/np.sum(np.abs(returns[(i-n+1):i]))
            PriceDistance.append(PCMD)
        return np.array(PriceDistance)
        
    
        
        
        
#YFeatures=yfeatures()     
#YFeatures._Sharpe_Ratio(sss['close'])
#YFeatures.Sharpe_Ratio_all(sss['close'].as_matrix(),30)     
#YFeatures.rolling_n_day_return(sss['close'].as_matrix())
#YFeatures.rolling_n_day_ATR_adj_y(mindat['high'].as_matrix(), mindat['low'].as_matrix(), mindat['close'].as_matrix(), timeperiod=30)
#YFeatures.price_to_distance(sss['close'].as_matrix(),30)