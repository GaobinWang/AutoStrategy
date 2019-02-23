# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'total.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QDateTime, Qt, QSize
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import QEventLoop
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush

import datetime
import numpy as np
import re
import webbrowser
import pandas as pd
import os
import gc
import statsmodels.api as smwf
import io 
import traceback
import fnmatch
from sqlalchemy import create_engine
import json
import time
#import qdarkstyle
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

from AutoStrategy.IOdata import Downloader
from AutoStrategy import AutoStrategy
from AutoStrategy.AutomatedCTAGenerator import AutomatedCTATradeHelper
from AutoStrategy.Visualization import plot
from AutoStrategy.PositionSizing import ComboStrategy
from AutoStrategy.Backtest import BacktestPerformence




marketindexes=['SH000016', 'SH000001', 'SH000010', 'SH000009', 'SZ399001',
'SZ399005', 'SZ399101', 'SZ399006', 'SZ399102', 'SZ399106', 'SH000905',
'SH000906', 'SH000852', 'SH000300',
'SZ399317', 'SH000903', 'SZ399330']



def Universal_Data_Updater(TimestampPriceX,Newdata):
    # to find the difference between datetimes to be updated
    OldDates=TimestampPriceX['DATETIME'].unique()
    NewDates=Newdata['DATETIME'].unique()
    DaysUpdated=NewDates[~np.in1d(NewDates,OldDates)]
    
    # the new data ready to be appended 
    Newdata=Newdata[np.in1d(Newdata['DATETIME'],DaysUpdated)]     
    if Newdata.empty:
        return None
    else:
        return Newdata
    






class CreateThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.createparadict = dict()

    # run method gets called when we start the thread
    def run(self):
        
          
        try:
            MongoMindb = Downloader.MongoDBIO(db=re.sub('分钟线','MinsData',self.createparadict['freq']),host='45.40.203.2')

            if self.createparadict['code'].startswith(('QI','SH','SZ')):
                starttimeindex = json.loads(pd.DataFrame([self.createparadict['starttime']]).T.to_json()).values()
                endtimeindex = json.loads(pd.DataFrame([self.createparadict['endtime']]).T.to_json()).values()                
                TimestampPriceX = MongoMindb.read_mongo(query={'DATETIME': {'$gt':list(starttimeindex)[0]['0'],'$lte':list(endtimeindex)[0]['0']}},collection=self.createparadict['code'])    
                TimestampPriceX['DATETIME'] = TimestampPriceX['DATETIME']*1000000
                TimestampPriceX['DATETIME'] = pd.to_datetime(TimestampPriceX['DATETIME'])
                TimestampPriceX['Date']=[x.date() for x in TimestampPriceX['DATETIME']]
                TimestampPriceX['Time']=[x.time() for x in TimestampPriceX['DATETIME']]            
            else:
                print('A Vaild Stock Code MUST be inputed!\n')
        except:
            traceback.print_exc()
            try:
                try:
                    self.createparadict['MktDatpath']=AutoStrategy.ReadListLinebyLine('MktDatpath.txt',os.getcwd())[0]
                except:
                    self.createparadict['MktDatpath']=r'C:\tools\Anaconda3\Lib\site-packages'
                    traceback.print_exc()
                disk_engine =create_engine('sqlite:///'+os.path.join(self.tradedict['MktDatpath'],'MktDat.db'))
                TimestampPriceX=pd.read_sql_query("SELECT * FROM TradingSignal where Code= '%s'" %self.tradedict['MktDatpath'], disk_engine)
            except:
                traceback.print_exc()
                try:
                    TianRuanDownloader=Downloader.TianRuan_Downloader("C:\\Program Files\\Tinysoft\\Analyse.NET")
                    TianRuanDownloader.login()
                    TimestampPriceX=TianRuanDownloader.continuous_min_download(self.createparadict['starttime'], self.createparadict['endtime'], self.createparadict['code'],'hfq',self.createparadict['freq'])         
                    TianRuanDownloader.logout()
                    TimestampPriceX=TimestampPriceX.drop_duplicates(subset='DATETIME', keep='first', inplace=False)        
                    TimestampPriceX = TimestampPriceX.replace({'0':np.nan, 0:np.nan})
                    TimestampPriceX =TimestampPriceX.dropna()
                    TimestampPriceX = TimestampPriceX.reset_index(drop=True)
                except:
                    traceback.print_exc()
      
        if self.createparadict['strategytype']=='机器学习':            
            AutoStrategy.Machine_Learning_GACreate(TimestampPriceX, strategyfolder=self.createparadict['strategyfolder'], code=self.createparadict['code'], 
                                                 strategy=self.createparadict['strategy'], topn=self.createparadict['topn'],numfeature=self.createparadict['numfeature'], 
                                                 numstrategy=1, numtry=self.createparadict['numtry'], 
                                                 opencost=self.createparadict['opencost'],closecost=self.createparadict['closecost'], 
                                                 intradayclosecost=self.createparadict['intradayclosecost'],r=self.createparadict['r'],Type=self.createparadict['backtest'],
                                                 popsize=self.createparadict['popsize'],maxgen=self.createparadict['maxgen'],mutationrate=self.createparadict['mutationrate'],
                                                 breedingrate=self.createparadict['breedingrate'],pexp=0.9,pnew=self.createparadict['pnew'],
                                                 keepbest=self.createparadict['keepbest'],rollingn=self.createparadict['rollingn'])
        else:
            AutoStrategy.Rule_Based_Create(TimestampPriceX, 
                                           strategyfolder=self.createparadict['strategyfolder'], code=self.createparadict['code'], 
                                           strategy=self.createparadict['strategy'], numfeature=self.createparadict['numfeature'], numstrategy=1, 
                                           numtry=self.createparadict['numtry'], target='Sharpe_Ratio',maxdepth=self.createparadict['maxdepth'],
                                           fpr=self.createparadict['fpr'],ppr=self.createparadict['ppr'],popsize=self.createparadict['popsize'],
                                           maxgen=self.createparadict['maxgen'],mutationrate=self.createparadict['mutationrate'],
                                           breedingrate=self.createparadict['breedingrate'],pexp=0.9,pnew=self.createparadict['pnew'], 
                                           opencost=self.createparadict['opencost'],closecost=self.createparadict['closecost'], 
                                           intradayclosecost=self.createparadict['intradayclosecost'],r=self.createparadict['r'],Type=self.createparadict['backtest'],
                                           keepbest=self.createparadict['keepbest'])
        gc.collect()
        self.signal.emit(self.createparadict['strategyfolder'])
        




  



class TradeThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')


    def __init__(self):
        QThread.__init__(self)
        self.tradedict = dict()
        # 初始化一个定时器
        self.tradetimer = QTimer()
        self.tradetimer.moveToThread(self)
        # 将定时器超时信号与槽函数showTime()连接
        self.tradetimer.timeout.connect(self.Trading)
        
        
    def Trading(self):
                
        TimeNow = QDateTime.currentDateTime()

            
        '''
        time_in_range是策略执行的时间，例如对于股票市场，是每日9:31到11:30，13:00到15:00
        TimeNow.minute % 30==1的含义是没过三十分钟计算一次交易信号
        '''
        for xtime in self.tradedict['potitime']:  
            if (TimeNow.toPyDateTime().minute==xtime.minute and TimeNow.toPyDateTime().hour==xtime.hour):
                '''
                下载的数据Newdata为pandas DataFrame
                字段需要是['Code','DATETIME','Date','Time','open','high','low','close','amount','volume']
                'Code': string 'SH000905',
                'DATETIME':datetime.datetime,
                'Date':datetime.date,
                'Time':datetime.time,
                'open':float,
                'high':float,
                'low'float,
                'close':float,
                'amount':float,
                'volume:float'
                Newdata开始日期应为上次运行策略时间，为保险起见，每次都取过去100个交易日的数据。
                示例从天软中下载数据，用户可使用自己的数据源，但需要整理为相同的字段
                ''' 
                # 首先从MongoDB中获取数据，如果失败，尝试天软
                try:
                    MongoMindb = Downloader.MongoDBIO(db=re.sub('分钟线','MinsData',self.tradedict['freq']),host='45.40.203.2')
        
                    if self.tradedict['code'].startswith(('SH','SZ')):
                        starttimeindex = json.loads(pd.DataFrame([self.tradedict['starttime']]).T.to_json()).values()
                        endtimeindex = json.loads(pd.DataFrame([datetime.datetime.combine(datetime.datetime.now().date(),datetime.time(9,0,0))]).T.to_json()).values()                
                        if list(starttimeindex)[0]['0']<list(endtimeindex)[0]['0']:
                            Newdata = MongoMindb.read_mongo(query={'DATETIME': {'$gt':list(starttimeindex)[0]['0'],'$lt':list(endtimeindex)[0]['0']}},collection=self.tradedict['code'])    
                            print (Newdata)
                            if len(Newdata)!=0:
                                Newdata['DATETIME'] = Newdata['DATETIME']*1000000
                                Newdata['DATETIME'] = pd.to_datetime(Newdata['DATETIME'])
                            else:
                                Newdata = pd.DataFrame(columns=['Code', 'Date', 'Time','DATETIME', 'amount', 'close', 'high', 'low', 'open', 'volume'])                                  
                        else:
                            Newdata = pd.DataFrame(columns=['Code', 'Date', 'Time','DATETIME', 'amount', 'close', 'high', 'low', 'open', 'volume'])  
                    elif self.tradedict['code'].startswith('QI'):
                        starttimeindex = json.loads(pd.DataFrame([self.tradedict['starttime']]).T.to_json()).values()
                        endtimeindex=json.loads(pd.DataFrame([datetime.datetime.now()]).T.to_json()).values()
                        if list(starttimeindex)[0]['0']<list(endtimeindex)[0]['0']:
                            Newdata = MongoMindb.read_mongo(query={'DATETIME': {'$gt':list(starttimeindex)[0]['0']}},collection=self.tradedict['code'])    
                            if len(Newdata)!=0:
                                Newdata['DATETIME'] = Newdata['DATETIME']*1000000
                                Newdata['DATETIME'] = pd.to_datetime(Newdata['DATETIME'])
                            else:
                                Newdata = pd.DataFrame(columns=['Code', 'Date', 'Time','DATETIME', 'amount', 'close', 'high', 'low', 'open', 'volume'])
                        else:
                            Newdata = pd.DataFrame(columns=['Code', 'Date', 'Time', 'DATETIME', 'amount', 'close', 'high', 'low', 'open', 'volume'])  
                    else:
                        print('A Vaild Stock Code MUST be inputed!\n')
                except:
                    traceback.print_exc()     
                    try:
                        TianRuanDownloader=Downloader.TianRuan_Downloader("C:\\Program Files\\Tinysoft\\Analyse.NET")
                        TianRuanDownloader.login()
                        Newdata=TianRuanDownloader.continuous_min_download(self.tradedict['starttime']-datetime.timedelta(days=1), datetime.datetime.now(), self.tradedict['code'],'hfq',self.tradedict['freq']) 
                        TianRuanDownloader.logout()
                    except:
                        traceback.print_exc()     
                
                
                
                # 如果数据不为空，那么检查数据是否到了当前位置，如果没有用tushare补齐
                if len(Newdata)!=0:
                    Newdata = Newdata[Newdata['DATETIME']<datetime.datetime.combine(datetime.datetime.now().date(),xtime)]
                    Newdata = Newdata.drop_duplicates(subset='DATETIME', keep='first', inplace=False)        
                    Newdata = Newdata.replace({'0':np.nan, 0:np.nan})
                    Newdata = Newdata.dropna()
                    Newdata = Newdata.reset_index(drop=True)
                    Newdata['Date']=[x.date() for x in Newdata['DATETIME']]
                    Newdata['Time']=[x.time() for x in Newdata['DATETIME']]
                    updatetime=Newdata['DATETIME'].iloc[-1]
                else:
                    updatetime=self.tradedict['starttime']
                    
                    
                    
                if updatetime==(datetime.datetime.combine(datetime.datetime.now().date(),xtime)-datetime.timedelta(minutes=1)):
                    pass
                else:
                    try:
                        tupytdx=Downloader.tushare_pytdx() 
                        time.sleep(1) 
                        if self.tradedict['code'] in marketindexes:
                            tupytdx.ts_bar_downloader(code=re.sub('SH|SZ','',self.tradedict['code']),
                                  start=updatetime,
                                  end=(datetime.datetime.combine(datetime.datetime.now().date(),xtime)-datetime.timedelta(minutes=1)),
                                  ktype=re.sub('分钟线','min',self.tradedict['freq']),asset='INDEX',adj=None)
                            Mindata = tupytdx.pretty(includecode=True) 
                        elif self.tradedict['code'].startswith(('SH','SZ')):
                            tupytdx.ts_bar_downloader(code=re.sub('SH|SZ','',self.tradedict['code']),
                                  start=updatetime,
                                  end=(datetime.datetime.combine(datetime.datetime.now().date(),xtime)-datetime.timedelta(minutes=1)),
                                  ktype=re.sub('分钟线','min',self.tradedict['freq']),asset='E',adj=None)
                            Mindata = tupytdx.pretty(includecode=True) 
                            Mindata = tupytdx.ts_local_hfq(Mindata)
                        print (Mindata)    
                        print (datetime.datetime.combine(datetime.datetime.now().date(),xtime)-datetime.timedelta(minutes=1))
                        tupytdxNewdata = Universal_Data_Updater(Newdata,Mindata)
                        Newdata = Newdata.append(tupytdxNewdata)
                    except:
                        traceback.print_exc()   




                            
                '''
                运行策略
                strategy: 策略名
                strategyfolder:策略所在文件夹
                vtSymbol:vnpy的实盘交易代码，若没有请填写模拟盘交易代码
                vnpypath: vnpy下载下来的所在路径，不能和vnpysettingpath同时为None
                vnpystrategyfolder:strategy 文件夹通常是在 vnpy\\trader\\app\\ctaStrategy' 下
                vnpysettingpath: 用来添加策略至策略字典的路径，通常在VnTrader下
                signalpath: 交易信号写入的数据库，若None则默认在strategyfolder向上一级文件夹下
                
                '''
                if self.tradedict['strategytype']=='机器学习': 
                    Pos=AutoStrategy.Machine_Learning_Run(strategy=self.tradedict['strategy'],
                                                      strategyfolder=self.tradedict['strategyfolder'],
                                                      vtSymbol=self.tradedict['VtSymbol'],Newdata=Newdata,Type=self.tradedict['LStypecomboBox'],
                                                      signalpath=self.tradedict['signalpath']) 
                else:
                    Pos=AutoStrategy.Rule_Based_Run(strategy=self.tradedict['strategy'],
                                                      strategyfolder=self.tradedict['strategyfolder'],
                                                      vtSymbol=self.tradedict['VtSymbol'],Newdata=Newdata,Type=self.tradedict['LStypecomboBox'],
                                                      signalpath=self.tradedict['signalpath']) 
                
                gc.collect()
                    
                if Pos is not None: 
                    tradestr=str(Pos['DATETIME'].iloc[0]) + ' : ' + Pos['StrategyName'].iloc[0]+ ' 在 '+Pos['SecurityName'].iloc[0]+' 发出信号 '+str(Pos['Tradeside'].iloc[0])+'@'+str(Pos['Price'].iloc[0])+' 目前仓位 '+str(Pos['Position'].iloc[0])
                else:                                    
                    disk_engine =create_engine('sqlite:///'+os.path.join(self.tradedict['signalpath'],'TradingSignal.db'))
                    SignalSQL=pd.read_sql_query("SELECT * FROM TradingSignal where StrategyName= '%s'" %self.tradedict['strategy'], disk_engine)
                    
                    if len(SignalSQL)>0:
                        datetime_x=[]
                        for y in SignalSQL['DATETIME']:
                            y=datetime.datetime.strptime(y,'%Y-%m-%d %H:%M:%S.%f')
                            datetime_x.append(y)
                        
                        SignalSQL['DATETIME']=datetime_x
                        SignalSQL=SignalSQL.sort_values(by='DATETIME')
                        CurrentPos=SignalSQL['Position'].iloc[-1]
                    else:
                        CurrentPos=0
                        
                    tradestr=str(datetime.datetime.now()) + ' : ' + self.tradedict['strategy'] + ' 在 '+self.tradedict['code']+' 发出信号 '+' 0 '+' 目前仓位 '+str(CurrentPos)
                
                self.signal.emit(tradestr)
                print (tradestr)                    
    
    # run method gets called when we start the thread
    def run(self):
        self.tradetimer.start(60000)
        loop = QEventLoop()
        loop.exec_()
  



class MCThread(QThread):
    signal = pyqtSignal(pd.DataFrame)

    def __init__(self):
        QThread.__init__(self)
        self.MCdict = dict()

    # run method gets called when we start the thread
    def run(self):

        try:
            MongoMindb = Downloader.MongoDBIO(db=re.sub('分钟线','MinsData',self.MCdict['freq']),host='45.40.203.2')

            if self.MCdict['code'].startswith(('QI','SH','SZ')):
                starttimeindex = json.loads(pd.DataFrame([self.MCdict['starttime']]).T.to_json()).values()
                endtimeindex = json.loads(pd.DataFrame([self.MCdict['endtime']]).T.to_json()).values()                
                TimestampPriceX = MongoMindb.read_mongo(query={'DATETIME': {'$gt':list(starttimeindex)[0]['0'],'$lte':list(endtimeindex)[0]['0']}},collection=self.MCdict['code'])    
                TimestampPriceX['DATETIME'] = TimestampPriceX['DATETIME']*1000000
                TimestampPriceX['DATETIME'] = pd.to_datetime(TimestampPriceX['DATETIME'])
                TimestampPriceX['Date']=[x.date() for x in TimestampPriceX['DATETIME']]
                TimestampPriceX['Time']=[x.time() for x in TimestampPriceX['DATETIME']]            
            else:
                print('A Vaild Stock Code MUST be inputed!\n')
        except:
            traceback.print_exc()
            try:
                try:
                    self.MCdict['MktDatpath']=AutoStrategy.ReadListLinebyLine('MktDatpath.txt',os.getcwd())[0]
                except:
                    self.MCdict['MktDatpath']=r'C:\tools\Anaconda3\Lib\site-packages'
                    traceback.print_exc()
                disk_engine =create_engine('sqlite:///'+os.path.join(self.MCdict['MktDatpath'],'MktDat.db'))
                TimestampPriceX=pd.read_sql_query("SELECT * FROM TradingSignal where Code= '%s'" %self.MCdict['MktDatpath'], disk_engine)
            except:
                traceback.print_exc()
                try:
                    TianRuanDownloader=Downloader.TianRuan_Downloader("C:\\Program Files\\Tinysoft\\Analyse.NET")
                    TianRuanDownloader.login()
                    TimestampPriceX=TianRuanDownloader.continuous_min_download(self.MCdict['starttime'], self.MCdict['endtime'], self.MCdict['code'],'hfq',self.MCdict['freq'])         
                    TianRuanDownloader.logout()
                    TimestampPriceX=TimestampPriceX.drop_duplicates(subset='DATETIME', keep='first', inplace=False)        
                    TimestampPriceX = TimestampPriceX.replace({'0':np.nan, 0:np.nan})
                    TimestampPriceX =TimestampPriceX.dropna()
                    TimestampPriceX = TimestampPriceX.reset_index(drop=True)
                except:
                    traceback.print_exc()
      

        
        evalperfdictall=[]
        
        if self.MCdict['strategytype']=='机器学习':   
            for i in range(self.MCdict['MCtimes']):
                evalperfdict=AutoStrategy.Machine_Learning_RobustTest(TimestampPriceX,self.MCdict['strategy'],self.MCdict['strategyfolder'],
                mutationrate=1,opencost=self.MCdict['opencost'],closecost=self.MCdict['closecost'],
                intradayclosecost=self.MCdict['intradayclosecost'],r=self.MCdict['r'],Type=self.MCdict['backtest'])
                evalperfdictall.append(evalperfdict)
                gc.collect()
            
            # calculate benchmark
            evalperfdictBM=AutoStrategy.Machine_Learning_RobustTest(TimestampPriceX,self.MCdict['strategy'],self.MCdict['strategyfolder'],
            mutationrate=0,opencost=self.MCdict['opencost'],closecost=self.MCdict['closecost'],
            intradayclosecost=self.MCdict['intradayclosecost'],r=self.MCdict['r'],Type=self.MCdict['backtest'])
                
                
        else:
            for i in range(self.MCdict['MCtimes']):
                evalperfdict=AutoStrategy.Tree_Based_RobustTest(TimestampPriceX,self.MCdict['strategy'],self.MCdict['strategyfolder'],
                mutationrate=1,opencost=self.MCdict['opencost'],closecost=self.MCdict['closecost'],
                intradayclosecost=self.MCdict['intradayclosecost'],r=self.MCdict['r'],Type=self.MCdict['backtest'])
                evalperfdictall.append(evalperfdict)  
                gc.collect()
                
            # calculate benchmark    
            evalperfdictBM=AutoStrategy.Tree_Based_RobustTest(TimestampPriceX,self.MCdict['strategy'],self.MCdict['strategyfolder'],
            mutationrate=0,opencost=self.MCdict['opencost'],closecost=self.MCdict['closecost'],
            intradayclosecost=self.MCdict['intradayclosecost'],r=self.MCdict['r'],Type=self.MCdict['backtest'])
   
        MCtable=[]
        values=[]
        
        # 将各个净值曲线合并在一起，组成Pandas DataFrame
        for evalperfdict in evalperfdictall:
            value=pd.DataFrame([list(evalperfdict.values())[0].date,list(evalperfdict.values())[0].SimpleValue]).transpose()
            value.columns=['date',list(evalperfdict.keys())[0]]
            values.append(value)

        MCcombine=ComboStrategy.Combine_Values_Common_Start_End(values)
        MCcombine.find_value_from_common_startpoint()      
        NormalizedValue=MCcombine.all_value_start_from_one()     
        NormalizedValue.append(MCcombine.CommonstartValue[0]['date'])
        NormalizedValue=pd.DataFrame(NormalizedValue).transpose()
        NormalizedValue=NormalizedValue.set_index('date')
        
        # 除重复/画图
        NormalizedValue=NormalizedValue.T.drop_duplicates().T
        fig = NormalizedValue.plot(kind='line',figsize=(10,4)).get_figure()
        
        visualbacktestpath=os.path.join(self.MCdict['strategyfolder'],'visualbacktest')
        if not os.path.exists(visualbacktestpath):
            os.mkdir(visualbacktestpath)
        fig.savefig(os.path.join(visualbacktestpath,"MCline.png"))
        fig.clf()
        
        # 计算最大值，平均值，最小值，基准值
        avgreturns=[np.mean(list(evalperfdict.values())[0].Return_by_year())[0] for evalperfdict in evalperfdictall]
        drawdowns=[list(evalperfdict.values())[0].max_drawdown(choice_simple_interest=True) for evalperfdict in evalperfdictall]
        sharperatios=[list(evalperfdict.values())[0].Sharpe_Ratio_all() for evalperfdict in evalperfdictall]
        
        MCtable.append([np.max(avgreturns),np.mean(avgreturns),np.min(avgreturns),np.mean(list(evalperfdictBM.values())[0].Return_by_year())[0]])
        MCtable.append([np.max(drawdowns),np.mean(drawdowns),np.min(drawdowns),list(evalperfdictBM.values())[0].max_drawdown(choice_simple_interest=True)])
        MCtable.append([np.max(sharperatios),np.mean(sharperatios),np.min(sharperatios),list(evalperfdictBM.values())[0].Sharpe_Ratio_all()])
        MCtable=pd.DataFrame(MCtable).T
        self.signal.emit(MCtable)
        



class OOBBTThread(QThread):
    signal = pyqtSignal(dict)

    def __init__(self):
        QThread.__init__(self)
        self.OOBdict = dict()

    # run method gets called when we start the thread
    def run(self):

        try:
            MongoMindb = Downloader.MongoDBIO(db=re.sub('分钟线','MinsData',self.OOBdict['freq']),host='45.40.203.2')

            if self.OOBdict['code'].startswith(('QI','SH','SZ')):
                starttimeindex = json.loads(pd.DataFrame([self.OOBdict['TimestampPriceXstarttime']]).T.to_json()).values()
                endtimeindex = json.loads(pd.DataFrame([self.OOBdict['endtime']]).T.to_json()).values()                
                TimestampPriceX = MongoMindb.read_mongo(query={'DATETIME': {'$gt':list(starttimeindex)[0]['0'],'$lte':list(endtimeindex)[0]['0']}},collection=self.OOBdict['code'])    
                TimestampPriceX['DATETIME'] = TimestampPriceX['DATETIME']*1000000
                TimestampPriceX['DATETIME'] = pd.to_datetime(TimestampPriceX['DATETIME'])
                TimestampPriceX['Date']=[x.date() for x in TimestampPriceX['DATETIME']]
                TimestampPriceX['Time']=[x.time() for x in TimestampPriceX['DATETIME']]            
            else:
                print('A Vaild Stock Code MUST be inputed!\n')
        except:
            traceback.print_exc()
            try:
                try:
                    self.OOBdict['MktDatpath']=AutoStrategy.ReadListLinebyLine('MktDatpath.txt',os.getcwd())[0]
                except:
                    self.OOBdict['MktDatpath']=r'C:\tools\Anaconda3\Lib\site-packages'
                    traceback.print_exc()
                disk_engine =create_engine('sqlite:///'+os.path.join(self.OOBdict['MktDatpath'],'MktDat.db'))
                TimestampPriceX=pd.read_sql_query("SELECT * FROM TradingSignal where Code= '%s'" %self.OOBdict['MktDatpath'], disk_engine)
            except:
                traceback.print_exc()
                try:
                    TianRuanDownloader=Downloader.TianRuan_Downloader("C:\\Program Files\\Tinysoft\\Analyse.NET")
                    TianRuanDownloader.login()
                    TimestampPriceX=TianRuanDownloader.continuous_min_download(self.OOBdict['starttime'], self.OOBdict['endtime'], self.OOBdict['code'],'hfq',self.OOBdict['freq'])         
                    TianRuanDownloader.logout()
                    TimestampPriceX = TimestampPriceX.drop_duplicates(subset='DATETIME', keep='first', inplace=False)        
                    TimestampPriceX = TimestampPriceX.replace({'0':np.nan, 0:np.nan})
                    TimestampPriceX = TimestampPriceX.dropna()
                    TimestampPriceX = TimestampPriceX.reset_index(drop=True)
                except:
                    traceback.print_exc()
      
        try:
            self.OOBdict['signalpath']=AutoStrategy.ReadListLinebyLine('SignalPath.txt',os.getcwd())[0]
        except:    
            self.OOBdict['signalpath']=r'C:\tools\Anaconda3\Lib\site-packages'
                
        if self.OOBdict['strategytype']=='机器学习':   
            evalperf=AutoStrategy.Machine_Learning_Backtest(TimestampPriceX,self.OOBdict['strategy'],self.OOBdict['strategyfolder'],
            useDBsignal=self.OOBdict['useDBsignal'],signalpath=self.OOBdict['signalpath'],opencost=self.OOBdict['opencost'],closecost=self.OOBdict['closecost'],
            intradayclosecost=self.OOBdict['intradayclosecost'],r=self.OOBdict['r'],Type=self.OOBdict['backtest'],starttime=self.OOBdict['starttime'],endtime=self.OOBdict['endtime'])
        else:
            evalperf=AutoStrategy.Rule_Based_Backtest(TimestampPriceX,self.OOBdict['strategy'],self.OOBdict['strategyfolder'],
            useDBsignal=self.OOBdict['useDBsignal'],signalpath=self.OOBdict['signalpath'],opencost=self.OOBdict['opencost'],closecost=self.OOBdict['closecost'],
            intradayclosecost=self.OOBdict['intradayclosecost'],r=self.OOBdict['r'],Type=self.OOBdict['backtest'],starttime=self.OOBdict['starttime'],endtime=self.OOBdict['endtime'])
        gc.collect()
        
        visualbacktestpath=os.path.join(self.OOBdict['strategyfolder'],'visualbacktest')
        if not os.path.exists(visualbacktestpath):
            os.mkdir(visualbacktestpath)
            
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date,evalperf.SimpleValue]).transpose(),'value')
        plot_trial.date_line_plot(os.path.join(visualbacktestpath,'value.png'))
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date[1:],evalperf.returns]).transpose(),'returns')
        plot_trial.hist_plot(os.path.join(visualbacktestpath,'returns.png'))
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date,-1*np.array(evalperf.SimpleDrawback)]).transpose(),'Drawback')
        plot_trial.area_plot(os.path.join(visualbacktestpath,'drawback.png'))
        
        fig = evalperf.Sharpe_Ratio_by_year()[1].plot(kind='bar').get_figure()
        fig.savefig(os.path.join(visualbacktestpath,"SharpeByYear.png"))
        fig.clf()
        
        BKresultdict=dict()
        BKresultdict['SharpeRatioall']=evalperf.Sharpe_Ratio_all()
        BKresultdict['avgreturns']=np.mean(evalperf.Return_by_year())[0]
        BKresultdict['maxdd']=evalperf.max_drawdown(choice_simple_interest=False)
        BKresultdict['hitratio']=evalperf.win_rate()
        BKresultdict['pnlratio']=evalperf.profit_and_loss_ratio()
        BKresultdict['sharpestd']=np.std(evalperf.Sharpe_Ratio_by_year()[1])
        BKresultdict['returnstd']=np.std(evalperf.Return_by_year())[0]
        
        self.signal.emit(BKresultdict)
        
        
        
        
        
class BacktestOOB_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)

        self.OOBBT_thread = OOBBTThread()      
        self.setupUi(self)      
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(853, 831)
        self.backtestendtimelabel = QtWidgets.QLabel(Dialog)
        self.backtestendtimelabel.setGeometry(QtCore.QRect(500, 260, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestendtimelabel.setFont(font)
        self.backtestendtimelabel.setObjectName("backtestendtimelabel")
        self.backtestcomboBox = QtWidgets.QComboBox(Dialog)
        self.backtestcomboBox.setGeometry(QtCore.QRect(270, 230, 91, 22))
        self.backtestcomboBox.setObjectName("backtestcomboBox")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")
        self.backtestlabel = QtWidgets.QLabel(Dialog)
        self.backtestlabel.setGeometry(QtCore.QRect(70, 219, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestlabel.setFont(font)
        self.backtestlabel.setObjectName("backtestlabel")
        self.EnddateTimeEdit = QtWidgets.QDateTimeEdit(Dialog)
        self.EnddateTimeEdit.setGeometry(QtCore.QRect(630, 270, 161, 22))
        self.EnddateTimeEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(2018, 1, 1), QtCore.QTime(0, 0, 0)))
        self.EnddateTimeEdit.setDate(QtCore.QDate(2018, 1, 1))
        self.EnddateTimeEdit.setObjectName("EnddateTimeEdit")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(340, 0, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.strategylineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategylineEdit.setGeometry(QtCore.QRect(610, 110, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.opencostlabel = QtWidgets.QLabel(Dialog)
        self.opencostlabel.setGeometry(QtCore.QRect(70, 139, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.opencostlabel.setFont(font)
        self.opencostlabel.setObjectName("opencostlabel")
        self.closecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.closecostdoubleSpinBox.setGeometry(QtCore.QRect(270, 191, 91, 22))
        self.closecostdoubleSpinBox.setDecimals(5)
        self.closecostdoubleSpinBox.setMaximum(1.0)
        self.closecostdoubleSpinBox.setSingleStep(0.001)
        self.closecostdoubleSpinBox.setProperty("value", 0.001)
        self.closecostdoubleSpinBox.setObjectName("closecostdoubleSpinBox")
        self.Cancel = QtWidgets.QPushButton(Dialog)
        self.Cancel.setGeometry(QtCore.QRect(700, 770, 93, 28))
        self.Cancel.setObjectName("Cancel")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(180, 110, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.intradayclosecostlabel = QtWidgets.QLabel(Dialog)
        self.intradayclosecostlabel.setGeometry(QtCore.QRect(500, 139, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.intradayclosecostlabel.setFont(font)
        self.intradayclosecostlabel.setObjectName("intradayclosecostlabel")
        self.strategylabel = QtWidgets.QLabel(Dialog)
        self.strategylabel.setGeometry(QtCore.QRect(500, 100, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.backteststarttimelabel = QtWidgets.QLabel(Dialog)
        self.backteststarttimelabel.setGeometry(QtCore.QRect(500, 220, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backteststarttimelabel.setFont(font)
        self.backteststarttimelabel.setObjectName("backteststarttimelabel")
        self.StartdateTimeEdit = QtWidgets.QDateTimeEdit(Dialog)
        self.StartdateTimeEdit.setGeometry(QtCore.QRect(630, 230, 161, 22))
        self.StartdateTimeEdit.setDate(QtCore.QDate(2007, 1, 1))
        self.StartdateTimeEdit.setObjectName("StartdateTimeEdit")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(260, 50, 331, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.closecostlabel = QtWidgets.QLabel(Dialog)
        self.closecostlabel.setGeometry(QtCore.QRect(70, 180, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.closecostlabel.setFont(font)
        self.closecostlabel.setObjectName("closecostlabel")
        self.intradayclosecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.intradayclosecostdoubleSpinBox.setGeometry(QtCore.QRect(700, 150, 91, 22))
        self.intradayclosecostdoubleSpinBox.setDecimals(5)
        self.intradayclosecostdoubleSpinBox.setMaximum(1.0)
        self.intradayclosecostdoubleSpinBox.setSingleStep(0.001)
        self.intradayclosecostdoubleSpinBox.setProperty("value", 0.001)
        self.intradayclosecostdoubleSpinBox.setObjectName("intradayclosecostdoubleSpinBox")
        self.Simulate = QtWidgets.QPushButton(Dialog)
        self.Simulate.setGeometry(QtCore.QRect(600, 770, 93, 28))
        self.Simulate.setObjectName("Simulate")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(70, 100, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.rlabel = QtWidgets.QLabel(Dialog)
        self.rlabel.setGeometry(QtCore.QRect(500, 180, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.rlabel.setFont(font)
        self.rlabel.setObjectName("rlabel")
        self.rdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.rdoubleSpinBox.setGeometry(QtCore.QRect(700, 191, 91, 22))
        self.rdoubleSpinBox.setDecimals(5)
        self.rdoubleSpinBox.setMaximum(1.0)
        self.rdoubleSpinBox.setSingleStep(0.001)
        self.rdoubleSpinBox.setProperty("value", 0.05)
        self.rdoubleSpinBox.setObjectName("rdoubleSpinBox")
        self.opencostdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.opencostdoubleSpinBox.setGeometry(QtCore.QRect(270, 150, 91, 22))
        self.opencostdoubleSpinBox.setDecimals(5)
        self.opencostdoubleSpinBox.setMaximum(1.0)
        self.opencostdoubleSpinBox.setSingleStep(0.001)
        self.opencostdoubleSpinBox.setProperty("value", 0.001)
        self.opencostdoubleSpinBox.setObjectName("opencostdoubleSpinBox")
        self.pnlratiolabel = QtWidgets.QLabel(Dialog)
        self.pnlratiolabel.setGeometry(QtCore.QRect(590, 491, 141, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.pnlratiolabel.setFont(font)
        self.pnlratiolabel.setObjectName("pnlratiolabel")
        self.sharpeall = QtWidgets.QLabel(Dialog)
        self.sharpeall.setGeometry(QtCore.QRect(710, 336, 72, 15))
        self.sharpeall.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sharpeall.setText("")
        self.sharpeall.setObjectName("sharpeall")
        self.Returndist = QtWidgets.QLabel(Dialog)
        self.Returndist.setGeometry(QtCore.QRect(320, 600, 211, 201))
        self.Returndist.setFrameShape(QtWidgets.QFrame.Box)
        self.Returndist.setText("")
        self.Returndist.setScaledContents(True)
        self.Returndist.setObjectName("Returndist")
        self.avgreturnlabel = QtWidgets.QLabel(Dialog)
        self.avgreturnlabel.setGeometry(QtCore.QRect(590, 371, 131, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.avgreturnlabel.setFont(font)
        self.avgreturnlabel.setObjectName("avgreturnlabel")
        self.hitratio = QtWidgets.QLabel(Dialog)
        self.hitratio.setGeometry(QtCore.QRect(710, 456, 72, 15))
        self.hitratio.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.hitratio.setText("")
        self.hitratio.setObjectName("hitratio")
        self.drawdownlabel = QtWidgets.QLabel(Dialog)
        self.drawdownlabel.setGeometry(QtCore.QRect(400, 300, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.drawdownlabel.setFont(font)
        self.drawdownlabel.setObjectName("drawdownlabel")
        self.maxddlabel = QtWidgets.QLabel(Dialog)
        self.maxddlabel.setGeometry(QtCore.QRect(590, 410, 72, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.maxddlabel.setFont(font)
        self.maxddlabel.setObjectName("maxddlabel")
        self.returnstdlabel = QtWidgets.QLabel(Dialog)
        self.returnstdlabel.setGeometry(QtCore.QRect(590, 571, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.returnstdlabel.setFont(font)
        self.returnstdlabel.setObjectName("returnstdlabel")
        self.maxdd = QtWidgets.QLabel(Dialog)
        self.maxdd.setGeometry(QtCore.QRect(710, 416, 72, 15))
        self.maxdd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.maxdd.setText("")
        self.maxdd.setObjectName("maxdd")
        self.SharpeByYear = QtWidgets.QLabel(Dialog)
        self.SharpeByYear.setGeometry(QtCore.QRect(70, 600, 211, 201))
        self.SharpeByYear.setFrameShape(QtWidgets.QFrame.Box)
        self.SharpeByYear.setText("")
        self.SharpeByYear.setScaledContents(True)
        self.SharpeByYear.setObjectName("SharpeByYear")
        self.returnstd = QtWidgets.QLabel(Dialog)
        self.returnstd.setGeometry(QtCore.QRect(710, 576, 72, 15))
        self.returnstd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.returnstd.setText("")
        self.returnstd.setObjectName("returnstd")
        self.pnlratio = QtWidgets.QLabel(Dialog)
        self.pnlratio.setGeometry(QtCore.QRect(710, 496, 72, 15))
        self.pnlratio.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.pnlratio.setText("")
        self.pnlratio.setObjectName("pnlratio")
        self.valuelabel = QtWidgets.QLabel(Dialog)
        self.valuelabel.setGeometry(QtCore.QRect(150, 300, 61, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.valuelabel.setFont(font)
        self.valuelabel.setObjectName("valuelabel")
        self.avgreturn = QtWidgets.QLabel(Dialog)
        self.avgreturn.setGeometry(QtCore.QRect(710, 376, 72, 15))
        self.avgreturn.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.avgreturn.setText("")
        self.avgreturn.setObjectName("avgreturn")
        self.hitratiolabel = QtWidgets.QLabel(Dialog)
        self.hitratiolabel.setGeometry(QtCore.QRect(590, 450, 72, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.hitratiolabel.setFont(font)
        self.hitratiolabel.setObjectName("hitratiolabel")
        self.SharpeByYearlabel = QtWidgets.QLabel(Dialog)
        self.SharpeByYearlabel.setGeometry(QtCore.QRect(120, 570, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.SharpeByYearlabel.setFont(font)
        self.SharpeByYearlabel.setObjectName("SharpeByYearlabel")
        self.drawdown = QtWidgets.QLabel(Dialog)
        self.drawdown.setGeometry(QtCore.QRect(320, 330, 211, 201))
        self.drawdown.setFrameShape(QtWidgets.QFrame.Box)
        self.drawdown.setText("")
        self.drawdown.setScaledContents(True)
        self.drawdown.setObjectName("drawdown")
        self.sharpestd = QtWidgets.QLabel(Dialog)
        self.sharpestd.setGeometry(QtCore.QRect(710, 536, 72, 15))
        self.sharpestd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sharpestd.setText("")
        self.sharpestd.setObjectName("sharpestd")
        self.Returndistlabel = QtWidgets.QLabel(Dialog)
        self.Returndistlabel.setGeometry(QtCore.QRect(380, 570, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.Returndistlabel.setFont(font)
        self.Returndistlabel.setObjectName("Returndistlabel")
        self.value = QtWidgets.QLabel(Dialog)
        self.value.setGeometry(QtCore.QRect(70, 330, 211, 201))
        self.value.setFrameShape(QtWidgets.QFrame.Box)
        self.value.setText("")
        self.value.setScaledContents(True)
        self.value.setObjectName("value")
        self.sharpestdlabel = QtWidgets.QLabel(Dialog)
        self.sharpestdlabel.setGeometry(QtCore.QRect(590, 531, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.sharpestdlabel.setFont(font)
        self.sharpestdlabel.setObjectName("sharpestdlabel")
        self.sharpealllabel = QtWidgets.QLabel(Dialog)
        self.sharpealllabel.setGeometry(QtCore.QRect(590, 330, 101, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.sharpealllabel.setFont(font)
        self.sharpealllabel.setObjectName("sharpealllabel")
        self.useDBsignalcheckBox = QtWidgets.QCheckBox(Dialog)
        self.useDBsignalcheckBox.setGeometry(QtCore.QRect(70, 260, 351, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.useDBsignalcheckBox.setFont(font)
        self.useDBsignalcheckBox.setObjectName("useDBsignalcheckBox")


        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)

        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(1034, 810))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
        
        self.retranslateUi(Dialog)
        self.Simulate.clicked.connect(self.on_ok_clicked)
        self.Cancel.clicked.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)




    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "样本外分析"))
        self.backtestendtimelabel.setText(_translate("Dialog", "回测结束时间"))
        self.backtestcomboBox.setItemText(0, _translate("Dialog", "多空回测"))
        self.backtestcomboBox.setItemText(1, _translate("Dialog", "单空回测"))
        self.backtestcomboBox.setItemText(2, _translate("Dialog", "单多回测"))
        self.backtestlabel.setText(_translate("Dialog", "回测方式"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "必须以Auto_开头"))
        self.opencostlabel.setText(_translate("Dialog", "开仓成本"))
        self.Cancel.setText(_translate("Dialog", "退出"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\\\Strategyfolder"))
        self.intradayclosecostlabel.setText(_translate("Dialog", "日内平仓成本"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.backteststarttimelabel.setText(_translate("Dialog", "回测开始时间"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.closecostlabel.setText(_translate("Dialog", "平仓成本"))
        self.Simulate.setText(_translate("Dialog", "开始分析"))
        self.strategyfolderlabel.setText(_translate("Dialog", "存储路径"))
        self.rlabel.setText(_translate("Dialog", "止损百分比"))
        self.pnlratiolabel.setText(_translate("Dialog", "盈亏比（日）"))
        self.avgreturnlabel.setText(_translate("Dialog", "平均年化收益"))
        self.drawdownlabel.setText(_translate("Dialog", "回撤"))
        self.maxddlabel.setText(_translate("Dialog", "最大回撤"))
        self.returnstdlabel.setText(_translate("Dialog", "年化收益波动率"))
        self.valuelabel.setText(_translate("Dialog", "净值"))
        self.hitratiolabel.setText(_translate("Dialog", "胜率"))
        self.SharpeByYearlabel.setText(_translate("Dialog", "分年度夏普"))
        self.Returndistlabel.setText(_translate("Dialog", "日收益分布"))
        self.sharpestdlabel.setText(_translate("Dialog", "夏普波动率"))
        self.sharpealllabel.setText(_translate("Dialog", "夏普"))
        self.useDBsignalcheckBox.setText(_translate("Dialog", "使用交易数据库信号进行分析"))




    def on_ok_clicked(self):
        self.OOBdict=dict()
        
        self.OOBdict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.OOBdict['strategy']=self.strategylineEdit.text()
        self.OOBdict['opencost']=self.opencostdoubleSpinBox.value()
        self.OOBdict['closecost']=self.closecostdoubleSpinBox.value()
        self.OOBdict['r']=self.rdoubleSpinBox.value()
        self.OOBdict['intradayclosecost']=self.intradayclosecostdoubleSpinBox.value()
        self.OOBdict['backtest']=self.backtestcomboBox.currentText()
        self.OOBdict['starttime']=self.StartdateTimeEdit.dateTime().toPyDateTime().date()
        self.OOBdict['endtime']=self.EnddateTimeEdit.dateTime().toPyDateTime().date()
        self.OOBdict['useDBsignal']=self.useDBsignalcheckBox.isChecked()
        
        SignalGenerator=AutomatedCTATradeHelper.Signal_Generator(self.OOBdict['strategyfolder'], self.OOBdict['strategy'])
        Strategy=SignalGenerator.Load_Strategy()  
        self.OOBdict['TimestampPriceXstarttime']=Strategy['TimestampPriceX']['DATETIME'].iloc[0]
        self.OOBdict['code']=Strategy['Code']
        
        if type(Strategy['Method']) is not str:
            self.OOBdict['strategytype']='基于规则'
        else:
            self.OOBdict['strategytype']='机器学习'        

        self.OOBdict['freq']=str(Strategy['TimestampPriceX']['DATETIME'].diff().value_counts().idxmax())
        self.OOBdict['freq']=re.findall('[0-9]{2}:[0-9]{2}:[0-9]{2}',self.OOBdict['freq'])[0]
        self.OOBdict['freq']=int(self.OOBdict['freq'][1:2])*60+int(self.OOBdict['freq'][3:5])
        self.OOBdict['freq']=str(self.OOBdict['freq'])+'分钟线'

        if self.OOBdict['backtest']=='多空回测':
            self.OOBdict['backtest']='LongShort'
        elif self.OOBdict['backtest']=='单多回测':
            self.OOBdict['backtest']='LongOnly'
        else:
            self.OOBdict['backtest']='ShortOnly'

        self.OOBBT_thread.OOBdict = self.OOBdict # Get the git URL
        self.Simulate.setEnabled(False)
        self.OOBBT_thread.start()  # Finally starts the thread 
        self.OOBBT_thread.signal.connect(self.on_OOBBT)   


    def on_OOBBT(self,BKresultdict):       
        visualbacktestpath=os.path.join(self.OOBdict['strategyfolder'],'visualbacktest')
        if not os.path.exists(visualbacktestpath):
            os.mkdir(visualbacktestpath)
            
        valuepixmap = QPixmap(os.path.join(visualbacktestpath,'value.png'))
        self.value.setPixmap(valuepixmap)

        returnspixmap = QPixmap(os.path.join(visualbacktestpath,'returns.png'))
        self.Returndist.setPixmap(returnspixmap)
        
        drawbackpixmap = QPixmap(os.path.join(visualbacktestpath,'drawback.png'))
        self.drawdown.setPixmap(drawbackpixmap)
        
        sharpepixmap = QPixmap(os.path.join(visualbacktestpath,'SharpeByYear.png'))
        self.SharpeByYear.setPixmap(sharpepixmap)
        
        self.sharpeall.setText('%.2f' % (round(BKresultdict['SharpeRatioall'],2)))
        self.avgreturn.setText('%.2f' % (round(BKresultdict['avgreturns'],4)*100)+'%')
        self.maxdd.setText('%.2f' % (round(BKresultdict['maxdd'],4)*100)+'%')
        self.hitratio.setText('%.2f' % (round(BKresultdict['hitratio'],4)*100)+'%')
        self.pnlratio.setText('%.2f' % (round(BKresultdict['pnlratio'],2)))
        self.sharpestd.setText('%.2f' % (round(BKresultdict['sharpestd'],2)))
        self.returnstd.setText('%.2f' % (round(BKresultdict['returnstd'],4)*100)+'%')
        
        self.Simulate.setEnabled(True)
        self.OOBBT_thread.quit()
        self.OOBBT_thread.wait()        
        
        
        
        
        
        
class MC_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)

        self.MC_thread = MCThread()      
        self.setupUi(self)      
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(876, 849)
        Dialog.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        Dialog.setAutoFillBackground(True)
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(250, 50, 331, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.value = QtWidgets.QLabel(Dialog)
        self.value.setGeometry(QtCore.QRect(60, 300, 751, 281))
        self.value.setFrameShape(QtWidgets.QFrame.Box)
        self.value.setText("")
        self.value.setScaledContents(True)
        self.value.setObjectName("value")
        self.strategylabel = QtWidgets.QLabel(Dialog)
        self.strategylabel.setGeometry(QtCore.QRect(490, 100, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(60, 100, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.strategylineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategylineEdit.setGeometry(QtCore.QRect(600, 110, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(330, 0, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(170, 110, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.tableWidget = QtWidgets.QTableWidget(Dialog)
        self.tableWidget.setGeometry(QtCore.QRect(60, 580, 751, 211))
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.setRowCount(4)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName("tableWidget")
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.tableWidget.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.tableWidget.setItem(0, 1, item)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(231)
        self.tableWidget.verticalHeader().setDefaultSectionSize(42)
        self.opencostdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.opencostdoubleSpinBox.setGeometry(QtCore.QRect(260, 150, 91, 22))
        self.opencostdoubleSpinBox.setDecimals(5)
        self.opencostdoubleSpinBox.setMaximum(1.0)
        self.opencostdoubleSpinBox.setSingleStep(0.001)
        self.opencostdoubleSpinBox.setProperty("value", 0.001)
        self.opencostdoubleSpinBox.setObjectName("opencostdoubleSpinBox")
        self.intradayclosecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.intradayclosecostdoubleSpinBox.setGeometry(QtCore.QRect(690, 150, 91, 22))
        self.intradayclosecostdoubleSpinBox.setDecimals(5)
        self.intradayclosecostdoubleSpinBox.setMaximum(1.0)
        self.intradayclosecostdoubleSpinBox.setSingleStep(0.001)
        self.intradayclosecostdoubleSpinBox.setProperty("value", 0.001)
        self.intradayclosecostdoubleSpinBox.setObjectName("intradayclosecostdoubleSpinBox")
        self.closecostlabel = QtWidgets.QLabel(Dialog)
        self.closecostlabel.setGeometry(QtCore.QRect(60, 180, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.closecostlabel.setFont(font)
        self.closecostlabel.setObjectName("closecostlabel")
        self.backtestlabel = QtWidgets.QLabel(Dialog)
        self.backtestlabel.setGeometry(QtCore.QRect(60, 219, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestlabel.setFont(font)
        self.backtestlabel.setObjectName("backtestlabel")
        self.closecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.closecostdoubleSpinBox.setGeometry(QtCore.QRect(260, 191, 91, 22))
        self.closecostdoubleSpinBox.setDecimals(5)
        self.closecostdoubleSpinBox.setMaximum(1.0)
        self.closecostdoubleSpinBox.setSingleStep(0.001)
        self.closecostdoubleSpinBox.setProperty("value", 0.001)
        self.closecostdoubleSpinBox.setObjectName("closecostdoubleSpinBox")
        self.opencostlabel = QtWidgets.QLabel(Dialog)
        self.opencostlabel.setGeometry(QtCore.QRect(60, 139, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.opencostlabel.setFont(font)
        self.opencostlabel.setObjectName("opencostlabel")
        self.rlabel = QtWidgets.QLabel(Dialog)
        self.rlabel.setGeometry(QtCore.QRect(490, 180, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.rlabel.setFont(font)
        self.rlabel.setObjectName("rlabel")
        self.intradayclosecostlabel = QtWidgets.QLabel(Dialog)
        self.intradayclosecostlabel.setGeometry(QtCore.QRect(490, 139, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.intradayclosecostlabel.setFont(font)
        self.intradayclosecostlabel.setObjectName("intradayclosecostlabel")
        self.backtestcomboBox = QtWidgets.QComboBox(Dialog)
        self.backtestcomboBox.setGeometry(QtCore.QRect(260, 230, 91, 22))
        self.backtestcomboBox.setObjectName("backtestcomboBox")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")
        self.rdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.rdoubleSpinBox.setGeometry(QtCore.QRect(690, 191, 91, 22))
        self.rdoubleSpinBox.setDecimals(5)
        self.rdoubleSpinBox.setMaximum(1.0)
        self.rdoubleSpinBox.setSingleStep(0.001)
        self.rdoubleSpinBox.setProperty("value", 0.05)
        self.rdoubleSpinBox.setObjectName("rdoubleSpinBox")
        self.MCtimeslabel = QtWidgets.QLabel(Dialog)
        self.MCtimeslabel.setGeometry(QtCore.QRect(490, 220, 161, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.MCtimeslabel.setFont(font)
        self.MCtimeslabel.setObjectName("MCtimeslabel")
        self.MCtimesspinBox = QtWidgets.QSpinBox(Dialog)
        self.MCtimesspinBox.setGeometry(QtCore.QRect(690, 230, 91, 22))
        self.MCtimesspinBox.setMaximum(9999)
        self.MCtimesspinBox.setProperty("value", 4)
        self.MCtimesspinBox.setDisplayIntegerBase(10)
        self.MCtimesspinBox.setObjectName("MCtimesspinBox")
        self.backtestendtimelabel = QtWidgets.QLabel(Dialog)
        self.backtestendtimelabel.setGeometry(QtCore.QRect(490, 260, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestendtimelabel.setFont(font)
        self.backtestendtimelabel.setObjectName("backtestendtimelabel")
        self.backteststarttimelabel = QtWidgets.QLabel(Dialog)
        self.backteststarttimelabel.setGeometry(QtCore.QRect(60, 260, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backteststarttimelabel.setFont(font)
        self.backteststarttimelabel.setObjectName("backteststarttimelabel")
        self.StartdateTimeEdit = QtWidgets.QDateTimeEdit(Dialog)
        self.StartdateTimeEdit.setGeometry(QtCore.QRect(190, 270, 161, 22))
        self.StartdateTimeEdit.setDate(QtCore.QDate(2007, 1, 1))
        self.StartdateTimeEdit.setObjectName("StartdateTimeEdit")
        self.EnddateTimeEdit = QtWidgets.QDateTimeEdit(Dialog)
        self.EnddateTimeEdit.setGeometry(QtCore.QRect(620, 270, 161, 22))
        self.EnddateTimeEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(2018, 1, 1), QtCore.QTime(0, 0, 0)))
        self.EnddateTimeEdit.setDate(QtCore.QDate(2018, 1, 1))
        self.EnddateTimeEdit.setObjectName("EnddateTimeEdit")
        self.Simulate = QtWidgets.QPushButton(Dialog)
        self.Simulate.setGeometry(QtCore.QRect(610, 810, 93, 28))
        self.Simulate.setObjectName("Simulate")
        self.Cancel = QtWidgets.QPushButton(Dialog)
        self.Cancel.setGeometry(QtCore.QRect(720, 810, 93, 28))
        self.Cancel.setObjectName("Cancel")


        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)

        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(1034, 810))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
        
        self.retranslateUi(Dialog)
        self.Simulate.clicked.connect(self.on_ok_clicked)
        self.Cancel.clicked.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "蒙特卡洛鲁棒性测试"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.strategyfolderlabel.setText(_translate("Dialog", "存储路径"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "必须以Auto_开头"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\\\Strategyfolder"))
        item = self.tableWidget.verticalHeaderItem(0)
        item.setText(_translate("Dialog", "最大值"))
        item = self.tableWidget.verticalHeaderItem(1)
        item.setText(_translate("Dialog", "平均值"))
        item = self.tableWidget.verticalHeaderItem(2)
        item.setText(_translate("Dialog", "最小值"))
        item = self.tableWidget.verticalHeaderItem(3)
        item.setText(_translate("Dialog", "基准值"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "年化收益"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "最大回撤"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Dialog", "夏普比率"))
        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setSortingEnabled(__sortingEnabled)
        self.closecostlabel.setText(_translate("Dialog", "平仓成本"))
        self.backtestlabel.setText(_translate("Dialog", "回测方式"))
        self.opencostlabel.setText(_translate("Dialog", "开仓成本"))
        self.rlabel.setText(_translate("Dialog", "止损百分比"))
        self.intradayclosecostlabel.setText(_translate("Dialog", "日内平仓成本"))
        self.backtestcomboBox.setItemText(0, _translate("Dialog", "多空回测"))
        self.backtestcomboBox.setItemText(1, _translate("Dialog", "单空回测"))
        self.backtestcomboBox.setItemText(2, _translate("Dialog", "单多回测"))
        self.MCtimeslabel.setText(_translate("Dialog", "蒙特卡洛次数"))
        self.backtestendtimelabel.setText(_translate("Dialog", "回测结束时间"))
        self.backteststarttimelabel.setText(_translate("Dialog", "回测开始时间"))
        self.Simulate.setText(_translate("Dialog", "开始模拟"))
        self.Cancel.setText(_translate("Dialog", "退出"))


    def on_ok_clicked(self):
        self.MCdict=dict()
        
        self.MCdict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.MCdict['strategy']=self.strategylineEdit.text()
        self.MCdict['opencost']=self.opencostdoubleSpinBox.value()
        self.MCdict['closecost']=self.closecostdoubleSpinBox.value()
        self.MCdict['r']=self.rdoubleSpinBox.value()
        self.MCdict['intradayclosecost']=self.intradayclosecostdoubleSpinBox.value()
        self.MCdict['backtest']=self.backtestcomboBox.currentText()
        self.MCdict['MCtimes']=self.MCtimesspinBox.value()
        self.MCdict['starttime']=self.StartdateTimeEdit.dateTime().toPyDateTime()
        self.MCdict['endtime']=self.EnddateTimeEdit.dateTime().toPyDateTime()
        
        SignalGenerator=AutomatedCTATradeHelper.Signal_Generator(self.MCdict['strategyfolder'], self.MCdict['strategy'])
        Strategy=SignalGenerator.Load_Strategy()  
        
        self.MCdict['code']=Strategy['Code']
        if type(Strategy['Method']) is not str:
            self.MCdict['strategytype']='基于规则'
        else:
            self.MCdict['strategytype']='机器学习'        

        self.MCdict['freq']=str(Strategy['TimestampPriceX']['DATETIME'].diff().value_counts().idxmax())
        self.MCdict['freq']=re.findall('[0-9]{2}:[0-9]{2}:[0-9]{2}',self.MCdict['freq'])[0]
        self.MCdict['freq']=int(self.MCdict['freq'][1:2])*60+int(self.MCdict['freq'][3:5])
        self.MCdict['freq']=str(self.MCdict['freq'])+'分钟线'

        if self.MCdict['backtest']=='多空回测':
            self.MCdict['backtest']='LongShort'
        elif self.MCdict['backtest']=='单多回测':
            self.MCdict['backtest']='LongOnly'
        else:
            self.MCdict['backtest']='ShortOnly'

        self.MC_thread.MCdict = self.MCdict # Get the git URL
        self.Simulate.setEnabled(False)
        self.MC_thread.start()  # Finally starts the thread 
        self.MC_thread.signal.connect(self.on_MC)   


    def on_MC(self,MCresult):       
        for i in range(len(MCresult)):
            for j in range(MCresult.columns.size): 
                item = QtWidgets.QTableWidgetItem(str(np.round(MCresult.iloc[i,j],2)))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.tableWidget.setItem(i, j, item)
     
        visualbacktestpath=os.path.join(self.MCdict['strategyfolder'],'visualbacktest')
        if not os.path.exists(visualbacktestpath):
            os.mkdir(visualbacktestpath)
        MCline = QPixmap(os.path.join(visualbacktestpath,'MCline.png'))
        self.value.setPixmap(MCline)
        self.Simulate.setEnabled(True)
        self.MC_thread.quit()
        self.MC_thread.wait()        
        


class DBSetting_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)
        self.setupUi(self)  
        
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(414, 300)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.signalpathtypelabel = QtWidgets.QLabel(Dialog)
        self.signalpathtypelabel.setGeometry(QtCore.QRect(20, 140, 171, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(9)
        self.signalpathtypelabel.setFont(font)
        self.signalpathtypelabel.setObjectName("signalpathtypelabel")
        self.signalpathlineEdit = QtWidgets.QLineEdit(Dialog)
        self.signalpathlineEdit.setGeometry(QtCore.QRect(190, 140, 191, 21))
        self.signalpathlineEdit.setText("")
        self.signalpathlineEdit.setObjectName("signalpathlineEdit")
        self.sqllabel = QtWidgets.QLabel(Dialog)
        self.sqllabel.setGeometry(QtCore.QRect(20, 190, 131, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(9)
        self.sqllabel.setFont(font)
        self.sqllabel.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.sqllabel.setObjectName("sqllabel")
        self.sqllineEdit = QtWidgets.QLineEdit(Dialog)
        self.sqllineEdit.setGeometry(QtCore.QRect(190, 190, 191, 21))
        self.sqllineEdit.setText("")
        self.sqllineEdit.setObjectName("sqllineEdit")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(160, 0, 101, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(90, 50, 250, 23))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setObjectName("subtitlelabel")
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)
        
        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(414, 300))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
                
        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "数据库路径设置"))
        self.signalpathtypelabel.setText(_translate("Dialog", "交易数据库路径"))
        self.signalpathlineEdit.setPlaceholderText(_translate("Dialog", "C:\\tools\\Anaconda3\\Lib\\site-packages"))
        self.sqllineEdit.setPlaceholderText(_translate("Dialog", "C:\\tools\\Anaconda3\\Lib\\site-packages"))
        self.sqllabel.setText(_translate("Dialog", "行情数据库路径"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))

    def on_ok_clicked(self):
        self.MktDatpath=self.sqllineEdit.text()
        if len(self.MktDatpath)==0:
            self.MktDatpath=r'C:\tools\Anaconda3\Lib\site-packages'
        AutoStrategy.WriteListLinebyLine('MktDatpath.txt',os.getcwd(),[self.MktDatpath])
        self.SignalPath=self.signalpathlineEdit.text()
        if len(self.SignalPath)==0:
            self.SignalPath=r'C:\tools\Anaconda3\Lib\site-packages'
        AutoStrategy.WriteListLinebyLine('SignalPath.txt',os.getcwd(),[self.SignalPath])
        self.close()
        
        
        
        
class Load_CSV_Ui_Dialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)
        self.setupUi(self)  
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 229)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(40, 160, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.dataloclabel = QtWidgets.QLabel(Dialog)
        self.dataloclabel.setGeometry(QtCore.QRect(20, 100, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.dataloclabel.setFont(font)
        self.dataloclabel.setObjectName("dataloclabel")
        self.dataloclineEdit = QtWidgets.QLineEdit(Dialog)
        self.dataloclineEdit.setGeometry(QtCore.QRect(120, 110, 261, 21))
        self.dataloclineEdit.setObjectName("dataloclineEdit")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(120, 0, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(40, 50, 331, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)

        
        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(400, 229))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
                
        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        
    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "CSV导入"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.dataloclabel.setText(_translate("Dialog", "数据地址"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))


    def on_ok_clicked(self):
        PreDefineddict={
           'datetime': ['DATETIME'],
           'date': ['Date'],
           'time': ['Time'],
           'code': ['Code'],
           'real':['real','np.array'],
           'open':['open','openprices'],
           'high':['high','highprices'],
           'low':['low','lowprices'],
           'close':['close','closeprices'],
           'volume':['volume','volumn','vol'],
           'amount':['amount','amt']}

        try:
            self.MktDatpath=AutoStrategy.ReadListLinebyLine('MktDatpath.txt',os.getcwd())[0]
        except:
            self.MktDatpath=r'C:\tools\Anaconda3\Lib\site-packages'
            traceback.print_exc()
        self.csvDatpath=self.dataloclineEdit.text()
        if len(self.csvDatpath)!=0:
            colnames=[]
            MKTdata=pd.read_csv(self.csvDatpath)
            for paramname in MKTdata.columns:
                if paramname.lower() in [item.lower() for sublist in list(PreDefineddict.values()) for item in sublist]:
                    colnames.append(paramname)      
            MKTdata=MKTdata[colnames]    
            disk_engine =create_engine('sqlite:///'+os.path.join(self.MktDatpath,'MktDat.db'))
            MKTdata.to_sql('MktDat', disk_engine, if_exists='append',index=False) 
        self.close()



class Attribute_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)
        self.setupUi(self)   
       
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(723, 639)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(320, 560, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(160, 111, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.strategylineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategylineEdit.setGeometry(QtCore.QRect(480, 110, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(60, 100, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.strategylabel = QtWidgets.QLabel(Dialog)
        self.strategylabel.setGeometry(QtCore.QRect(390, 100, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.textBrowser = QtWidgets.QTextBrowser(Dialog)
        self.textBrowser.setGeometry(QtCore.QRect(60, 170, 601, 371))
        self.textBrowser.setObjectName("textBrowser")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(270, 10, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(200, 60, 331, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)
        
        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(723, 639))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
        
        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)



    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "归因"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\Strategyfolder"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "必须以Auto_开头"))
        self.strategyfolderlabel.setText(_translate("Dialog", "存储路径"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))


    def on_ok_clicked(self):
        self.attributedict=dict()
        
        self.attributedict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.attributedict['strategy']=self.strategylineEdit.text()
        
        SignalGenerator=AutomatedCTATradeHelper.Signal_Generator(self.attributedict['strategyfolder'], self.attributedict['strategy'])
        Strategy=SignalGenerator.Load_Strategy()
        
        
        # store function's name with params
        methoddict=dict()
        
        # 初始化
        for name in Strategy['FeaturesXCohort'].keys():  
            methoddict[name]=[]
        
        # 将ParamXCohort与FeaturesXCohort一一对应
        for func in Strategy['ParamXCohort'].keys():
            for name in Strategy['FeaturesXCohort'].keys():  
                funcstr = re.sub('[<>]','',str(func))
                if re.sub("[0-9_]*$", '', name) in re.split('\s+|[.]',funcstr):
                    for param in Strategy['ParamXCohort'][func].keys():
                        if not hasattr(Strategy['ParamXCohort'][func][param], "__len__"):
                            methoddict[name].append(param+'='+ str(round(Strategy['ParamXCohort'][func][param],2)))
                        else:
                            methoddict[name].append(param)
        
        # 将methoddict中的real用RealaliasXCohort替换
        for name in methoddict.keys():
            methoddict[name]=Strategy['RealaliasXCohort'][name]+list(filter(lambda a: a != 'real', methoddict[name]))
        
        AuxiliaryNote=''
        for name in methoddict.keys():
             AuxiliaryNote=AuxiliaryNote+name+'('+', '.join(methoddict[name])+')\n'
        
        methoddictY=dict()
        Yname=list(Strategy['FeatureY'].keys())[0]
        Yfunc=list(Strategy['ParamY'].keys())[0]
        Yfuncstr = re.sub('[<>]','',str(Yfunc))
        methoddictY[Yname]=[]
        if re.sub("[0-9_]*$", '', Yname) in re.split('\s+|[.]',Yfuncstr):
            for param in Strategy['ParamY'][Yfunc].keys():
                if not hasattr(Strategy['ParamY'][Yfunc][param], "__len__"):
                    methoddictY[Yname].append(param+'='+ str(round(Strategy['ParamY'][Yfunc][param],2)))
                else:
                    methoddictY[Yname].append(param)

        for Yname in methoddictY.keys():
            methoddictY[Yname]=Strategy['RealaliasY'][Yname]+list(filter(lambda a: a != 'real', methoddictY[Yname]))

        
        for Yname in methoddictY.keys():
             AuxiliaryNote=Yname+'('+', '.join(methoddictY[Yname])+')\n'+AuxiliaryNote
                            
        Colnames=Strategy['Traindata'].columns.difference(['DATETIME'])
        '''
        colexplanation=''
        for i, colname in enumerate(Colnames):
            colexplanation=colexplanation+'p'+str(i)+': ' + colname +'\n' 
        '''
        if isinstance(Strategy['Method'], str):
            colnamesX = Strategy['Traindata'].columns[2:]
            y = Strategy['Traindata'][Strategy['Traindata'].columns[0]]
            X = Strategy['Traindata'][colnamesX]
            X = smwf.add_constant(X, has_constant='add')
            # change of data type
            y = y.astype(float)
            
            for column in X:
                X[column]=X[column].astype(float)
                
            model = smwf.OLS(y, X).fit() 
            
            Y=Strategy['Traindata'].columns[0]
            Xs=[str(round(x[0],2))+' * '+x[1] for x in zip(model.params[1:], model.params.index[1:])]
            XYformulastr=Y + ' = ' + str(round(model.params[0],2)) + ' + ' + ' + '.join(Xs)
            self.textBrowser.setText(XYformulastr+'\n'*4+'使用因子:\n'+AuxiliaryNote+'注：同一因子带不同后缀出现在表达式中多次为哑变量，如果因子没有出现则代表因子在预处理中被丢弃\n因子说明请查询Talib和AutoStrategy下的FeatureBase.py')
        else:
            StrategyMethod = io.StringIO()
            Strategy['Method'].display(f=StrategyMethod)
            Treeformulastr=StrategyMethod.getvalue()
            for i, colname in enumerate(Colnames):
                Treeformulastr=Treeformulastr.replace('p'+str(i),colname)
            self.textBrowser.setText(Treeformulastr+'\n'*4+'使用因子:\n'+AuxiliaryNote+'注：同一因子带不同后缀出现在表达式中多次为哑变量，如果因子没有出现则代表因子在预处理中被丢弃\n因子说明请查询Talib和AutoStrategy下的FeatureBase.py')
            

class Criteria_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)
        self.setupUi(self)   
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(527, 411)
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        Dialog.setFont(font)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(70, 320, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.sharpealllabel = QtWidgets.QLabel(Dialog)
        self.sharpealllabel.setGeometry(QtCore.QRect(80, 90, 72, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.sharpealllabel.setFont(font)
        self.sharpealllabel.setObjectName("sharpealllabel")
        self.avgreturnlabel = QtWidgets.QLabel(Dialog)
        self.avgreturnlabel.setGeometry(QtCore.QRect(80, 130, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.avgreturnlabel.setFont(font)
        self.avgreturnlabel.setObjectName("avgreturnlabel")
        self.maxddlabel = QtWidgets.QLabel(Dialog)
        self.maxddlabel.setGeometry(QtCore.QRect(80, 170, 91, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.maxddlabel.setFont(font)
        self.maxddlabel.setObjectName("maxddlabel")
        self.sharpestdlabel = QtWidgets.QLabel(Dialog)
        self.sharpestdlabel.setGeometry(QtCore.QRect(80, 210, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.sharpestdlabel.setFont(font)
        self.sharpestdlabel.setObjectName("sharpestdlabel")
        self.returnstdlabel = QtWidgets.QLabel(Dialog)
        self.returnstdlabel.setGeometry(QtCore.QRect(80, 250, 171, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.returnstdlabel.setFont(font)
        self.returnstdlabel.setObjectName("returnstdlabel")
        self.SRGLcomboBox = QtWidgets.QComboBox(Dialog)
        self.SRGLcomboBox.setGeometry(QtCore.QRect(260, 100, 41, 22))
        self.SRGLcomboBox.setObjectName("SRGLcomboBox")
        self.SRGLcomboBox.addItem("")
        self.SRGLcomboBox.addItem("")
        self.AVGRGLcomboBox = QtWidgets.QComboBox(Dialog)
        self.AVGRGLcomboBox.setGeometry(QtCore.QRect(260, 140, 41, 22))
        self.AVGRGLcomboBox.setObjectName("AVGRGLcomboBox")
        self.AVGRGLcomboBox.addItem("")
        self.AVGRGLcomboBox.addItem("")
        self.MAXDDGLcomboBox = QtWidgets.QComboBox(Dialog)
        self.MAXDDGLcomboBox.setGeometry(QtCore.QRect(260, 180, 41, 22))
        self.MAXDDGLcomboBox.setObjectName("MAXDDGLcomboBox")
        self.MAXDDGLcomboBox.addItem("")
        self.MAXDDGLcomboBox.addItem("")
        self.SRSTDGLcomboBox = QtWidgets.QComboBox(Dialog)
        self.SRSTDGLcomboBox.setGeometry(QtCore.QRect(260, 220, 41, 22))
        self.SRSTDGLcomboBox.setObjectName("SRSTDGLcomboBox")
        self.SRSTDGLcomboBox.addItem("")
        self.SRSTDGLcomboBox.addItem("")
        self.AVGRSTDGLcomboBox = QtWidgets.QComboBox(Dialog)
        self.AVGRSTDGLcomboBox.setGeometry(QtCore.QRect(260, 260, 41, 22))
        self.AVGRSTDGLcomboBox.setObjectName("AVGRSTDGLcomboBox")
        self.AVGRSTDGLcomboBox.addItem("")
        self.AVGRSTDGLcomboBox.addItem("")
        self.SRdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.SRdoubleSpinBox.setGeometry(QtCore.QRect(320, 100, 91, 22))
        self.SRdoubleSpinBox.setDecimals(5)
        self.SRdoubleSpinBox.setMinimum(-99.99)
        self.SRdoubleSpinBox.setSingleStep(0.01)
        self.SRdoubleSpinBox.setProperty("value", 1.0)
        self.SRdoubleSpinBox.setObjectName("SPdoubleSpinBox")
        self.AVGRdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.AVGRdoubleSpinBox.setGeometry(QtCore.QRect(320, 140, 91, 22))
        self.AVGRdoubleSpinBox.setDecimals(5)
        self.AVGRdoubleSpinBox.setMinimum(-1.0)
        self.AVGRdoubleSpinBox.setMaximum(1.0)
        self.AVGRdoubleSpinBox.setSingleStep(0.01)
        self.AVGRdoubleSpinBox.setProperty("value", 0.2)
        self.AVGRdoubleSpinBox.setObjectName("AVGRdoubleSpinBox")
        self.MAXDDdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.MAXDDdoubleSpinBox.setGeometry(QtCore.QRect(320, 180, 91, 22))
        self.MAXDDdoubleSpinBox.setDecimals(5)
        self.MAXDDdoubleSpinBox.setMaximum(0.99)
        self.MAXDDdoubleSpinBox.setSingleStep(0.01)
        self.MAXDDdoubleSpinBox.setProperty("value", 0.15)
        self.MAXDDdoubleSpinBox.setObjectName("MAXDDdoubleSpinBox")
        self.SRSTDdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.SRSTDdoubleSpinBox.setGeometry(QtCore.QRect(320, 220, 91, 22))
        self.SRSTDdoubleSpinBox.setDecimals(5)
        self.SRSTDdoubleSpinBox.setSingleStep(0.01)
        self.SRSTDdoubleSpinBox.setProperty("value", 2.0)
        self.SRSTDdoubleSpinBox.setObjectName("SRSTDdoubleSpinBox")
        self.AVGRSTDdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.AVGRSTDdoubleSpinBox.setGeometry(QtCore.QRect(320, 260, 91, 22))
        self.AVGRSTDdoubleSpinBox.setDecimals(5)
        self.AVGRSTDdoubleSpinBox.setSingleStep(0.01)
        self.AVGRSTDdoubleSpinBox.setProperty("value", 1.0)
        self.AVGRSTDdoubleSpinBox.setObjectName("AVGRSTDdoubleSpinBox")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(180, 10, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(80, 50, 361, 31))
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)

        
        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(527, 411))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
        
        
        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(self.on_ok_cliked)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "策略标准"))
        self.sharpealllabel.setText(_translate("Dialog", "夏普"))
        self.avgreturnlabel.setText(_translate("Dialog", "平均年化收益"))
        self.maxddlabel.setText(_translate("Dialog", "最大回撤"))
        self.sharpestdlabel.setText(_translate("Dialog", "夏普波动率"))
        self.returnstdlabel.setText(_translate("Dialog", "年化收益波动率"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.SRGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.SRGLcomboBox.setItemText(1, _translate("Dialog", "<"))
        self.AVGRGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.AVGRGLcomboBox.setItemText(1, _translate("Dialog", "<"))
        self.MAXDDGLcomboBox.setCurrentText(_translate("Dialog", "<"))
        self.MAXDDGLcomboBox.setItemText(0, _translate("Dialog", "<"))
        self.MAXDDGLcomboBox.setItemText(1, _translate("Dialog", ">"))
        self.SRSTDGLcomboBox.setCurrentText(_translate("Dialog", "<"))
        self.SRSTDGLcomboBox.setItemText(0, _translate("Dialog", "<"))
        self.SRSTDGLcomboBox.setItemText(1, _translate("Dialog", ">"))
        self.AVGRSTDGLcomboBox.setCurrentText(_translate("Dialog", "<"))
        self.AVGRSTDGLcomboBox.setItemText(0, _translate("Dialog", "<"))
        self.AVGRSTDGLcomboBox.setItemText(1, _translate("Dialog", ">"))

    def on_ok_cliked(self):
        self.criteria=dict()
        self.evalrequiredNew=dict()
        
        self.criteria['SRGL']=self.SRGLcomboBox.currentText()
        self.criteria['AVGRGL']=self.AVGRGLcomboBox.currentText()
        self.criteria['MAXDDGL']=self.MAXDDGLcomboBox.currentText()
        self.criteria['SRSTDGL']=self.SRSTDGLcomboBox.currentText()
        self.criteria['AVGRSTDGL']=self.AVGRSTDGLcomboBox.currentText()
        self.criteria['SR']=self.SRdoubleSpinBox.value()
        self.criteria['AVGR']=self.AVGRSTDdoubleSpinBox.value()
        self.criteria['MAXDD']=self.MAXDDdoubleSpinBox.value()
        self.criteria['SRSTD']=self.SRSTDdoubleSpinBox.value()
        self.criteria['AVGRSTD']=self.AVGRSTDdoubleSpinBox.value()
        
        self.evalrequiredNew['Sharpe']=self.criteria['SRGL']+str(self.criteria['SR'])
        self.evalrequiredNew['DrawDown']=self.criteria['MAXDDGL']+str(self.criteria['MAXDD'])
        self.evalrequiredNew['SharpeStd']=self.criteria['SRSTDGL']+str(self.criteria['SRSTD'])
        self.evalrequiredNew['Return']=self.criteria['AVGRGL']+str(self.criteria['AVGR'])
        self.evalrequiredNew['ReturnStd']=self.criteria['AVGRSTDGL']+str(self.criteria['AVGRSTD'])
        
        moduleFile=os.path.dirname(AutoStrategy.__file__)
        evalrequired=AutoStrategy.loadJsonSetting('StrategyCritertia.json',moduleFile)
        for key in evalrequired.keys():
            if not self.evalrequiredNew[key]:
                continue
            else:
                evalrequired[key]=self.evalrequiredNew[key]
        AutoStrategy.WriteJsonSetting(evalrequired,os.path.join(moduleFile,'StrategyCritertia.json'))
        self.close()
        
        

class BK_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)
        self.setupUi(self)   
        
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1082, 915)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(480, 840, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.strategylineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategylineEdit.setGeometry(QtCore.QRect(580, 110, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(150, 110, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.strategylabel = QtWidgets.QLabel(Dialog)
        self.strategylabel.setGeometry(QtCore.QRect(470, 99, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(40, 99, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.value = QtWidgets.QLabel(Dialog)
        self.value.setGeometry(QtCore.QRect(40, 180, 351, 291))
        self.value.setFrameShape(QtWidgets.QFrame.Box)
        self.value.setText("")
        self.value.setScaledContents(True)
        self.value.setObjectName("value")
        self.drawdown = QtWidgets.QLabel(Dialog)
        self.drawdown.setGeometry(QtCore.QRect(470, 180, 351, 291))
        self.drawdown.setFrameShape(QtWidgets.QFrame.Box)
        self.drawdown.setText("")
        self.drawdown.setScaledContents(True)
        self.drawdown.setObjectName("drawdown")
        self.SharpeByYear = QtWidgets.QLabel(Dialog)
        self.SharpeByYear.setGeometry(QtCore.QRect(40, 520, 351, 291))
        self.SharpeByYear.setFrameShape(QtWidgets.QFrame.Box)
        self.SharpeByYear.setText("")
        self.SharpeByYear.setScaledContents(True)
        self.SharpeByYear.setObjectName("SharpeByYear")
        self.Returndist = QtWidgets.QLabel(Dialog)
        self.Returndist.setGeometry(QtCore.QRect(470, 520, 351, 291))
        self.Returndist.setFrameShape(QtWidgets.QFrame.Box)
        self.Returndist.setText("")
        self.Returndist.setScaledContents(True)
        self.Returndist.setObjectName("Returndist")
        self.valuelabel = QtWidgets.QLabel(Dialog)
        self.valuelabel.setGeometry(QtCore.QRect(180, 145, 61, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.valuelabel.setFont(font)
        self.valuelabel.setObjectName("valuelabel")
        self.drawdownlabel = QtWidgets.QLabel(Dialog)
        self.drawdownlabel.setGeometry(QtCore.QRect(630, 145, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.drawdownlabel.setFont(font)
        self.drawdownlabel.setObjectName("drawdownlabel")
        self.SharpeByYearlabel = QtWidgets.QLabel(Dialog)
        self.SharpeByYearlabel.setGeometry(QtCore.QRect(170, 485, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.SharpeByYearlabel.setFont(font)
        self.SharpeByYearlabel.setObjectName("SharpeByYearlabel")
        self.Returndistlabel = QtWidgets.QLabel(Dialog)
        self.Returndistlabel.setGeometry(QtCore.QRect(610, 485, 111, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.Returndistlabel.setFont(font)
        self.Returndistlabel.setObjectName("Returndistlabel")
        self.sharpealllabel = QtWidgets.QLabel(Dialog)
        self.sharpealllabel.setGeometry(QtCore.QRect(850, 184, 101, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.sharpealllabel.setFont(font)
        self.sharpealllabel.setObjectName("sharpealllabel")
        self.sharpeall = QtWidgets.QLabel(Dialog)
        self.sharpeall.setGeometry(QtCore.QRect(970, 190, 72, 15))
        self.sharpeall.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sharpeall.setText("")
        self.sharpeall.setObjectName("sharpeall")
        self.avgreturnlabel = QtWidgets.QLabel(Dialog)
        self.avgreturnlabel.setGeometry(QtCore.QRect(850, 225, 131, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.avgreturnlabel.setFont(font)
        self.avgreturnlabel.setObjectName("avgreturnlabel")
        self.avgreturn = QtWidgets.QLabel(Dialog)
        self.avgreturn.setGeometry(QtCore.QRect(970, 230, 72, 15))
        self.avgreturn.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.avgreturn.setText("")
        self.avgreturn.setObjectName("avgreturn")
        self.maxddlabel = QtWidgets.QLabel(Dialog)
        self.maxddlabel.setGeometry(QtCore.QRect(850, 264, 72, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.maxddlabel.setFont(font)
        self.maxddlabel.setObjectName("maxddlabel")
        self.maxdd = QtWidgets.QLabel(Dialog)
        self.maxdd.setGeometry(QtCore.QRect(970, 270, 72, 15))
        self.maxdd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.maxdd.setText("")
        self.maxdd.setObjectName("maxdd")
        self.hitratiolabel = QtWidgets.QLabel(Dialog)
        self.hitratiolabel.setGeometry(QtCore.QRect(850, 304, 72, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.hitratiolabel.setFont(font)
        self.hitratiolabel.setObjectName("hitratiolabel")
        self.hitratio = QtWidgets.QLabel(Dialog)
        self.hitratio.setGeometry(QtCore.QRect(970, 310, 72, 15))
        self.hitratio.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.hitratio.setText("")
        self.hitratio.setObjectName("hitratio")
        self.pnlratiolabel = QtWidgets.QLabel(Dialog)
        self.pnlratiolabel.setGeometry(QtCore.QRect(850, 345, 141, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.pnlratiolabel.setFont(font)
        self.pnlratiolabel.setObjectName("pnlratiolabel")
        self.pnlratio = QtWidgets.QLabel(Dialog)
        self.pnlratio.setGeometry(QtCore.QRect(970, 350, 72, 15))
        self.pnlratio.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.pnlratio.setText("")
        self.pnlratio.setObjectName("pnlratio")
        self.sharpestdlabel = QtWidgets.QLabel(Dialog)
        self.sharpestdlabel.setGeometry(QtCore.QRect(850, 385, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.sharpestdlabel.setFont(font)
        self.sharpestdlabel.setObjectName("sharpestdlabel")
        self.sharpestd = QtWidgets.QLabel(Dialog)
        self.sharpestd.setGeometry(QtCore.QRect(970, 390, 72, 15))
        self.sharpestd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sharpestd.setText("")
        self.sharpestd.setObjectName("sharpestd")
        self.returnstdlabel = QtWidgets.QLabel(Dialog)
        self.returnstdlabel.setGeometry(QtCore.QRect(850, 425, 121, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.returnstdlabel.setFont(font)
        self.returnstdlabel.setObjectName("returnstdlabel")
        self.returnstd = QtWidgets.QLabel(Dialog)
        self.returnstd.setGeometry(QtCore.QRect(970, 430, 72, 15))
        self.returnstd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.returnstd.setText("")
        self.returnstd.setObjectName("returnstd")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(380, 10, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(300, 60, 331, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.totalreturnlabel = QtWidgets.QLabel(Dialog)
        self.totalreturnlabel.setGeometry(QtCore.QRect(850, 460, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.totalreturnlabel.setFont(font)
        self.totalreturnlabel.setObjectName("totalreturnlabel")
        self.totalreturn = QtWidgets.QLabel(Dialog)
        self.totalreturn.setGeometry(QtCore.QRect(970, 470, 72, 15))
        self.totalreturn.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.totalreturn.setText("")
        self.totalreturn.setObjectName("totalreturn")
        self.totaltradeslabel = QtWidgets.QLabel(Dialog)
        self.totaltradeslabel.setGeometry(QtCore.QRect(850, 500, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.totaltradeslabel.setFont(font)
        self.totaltradeslabel.setObjectName("totaltradeslabel")
        self.totaltrades = QtWidgets.QLabel(Dialog)
        self.totaltrades.setGeometry(QtCore.QRect(970, 510, 72, 15))
        self.totaltrades.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.totaltrades.setText("")
        self.totaltrades.setObjectName("totaltrades")
        self.avgtradesprofitlabel = QtWidgets.QLabel(Dialog)
        self.avgtradesprofitlabel.setGeometry(QtCore.QRect(850, 540, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.avgtradesprofitlabel.setFont(font)
        self.avgtradesprofitlabel.setObjectName("avgtradesprofitlabel")
        self.avgtradesprofit = QtWidgets.QLabel(Dialog)
        self.avgtradesprofit.setGeometry(QtCore.QRect(970, 550, 72, 15))
        self.avgtradesprofit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.avgtradesprofit.setText("")
        self.avgtradesprofit.setObjectName("avgtradesprofit")
        self.avgtradeslosslabel = QtWidgets.QLabel(Dialog)
        self.avgtradeslosslabel.setGeometry(QtCore.QRect(850, 580, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(9)
        self.avgtradeslosslabel.setFont(font)
        self.avgtradeslosslabel.setObjectName("avgtradeslosslabel")
        self.avgtradesloss = QtWidgets.QLabel(Dialog)
        self.avgtradesloss.setGeometry(QtCore.QRect(970, 590, 72, 15))
        self.avgtradesloss.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.avgtradesloss.setText("")
        self.avgtradesloss.setObjectName("avgtradesloss")
       
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)
        
        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(1082, 915))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
        
        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "回测展示"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "必须以Auto_开头"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\Strategyfolder"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.strategyfolderlabel.setText(_translate("Dialog", "存储路径"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.valuelabel.setText(_translate("Dialog", "净值"))
        self.drawdownlabel.setText(_translate("Dialog", "回撤"))
        self.SharpeByYearlabel.setText(_translate("Dialog", "分年度夏普"))
        self.Returndistlabel.setText(_translate("Dialog", "日收益分布"))
        self.sharpealllabel.setText(_translate("Dialog", "夏普"))
        self.avgreturnlabel.setText(_translate("Dialog", "平均年化收益"))
        self.maxddlabel.setText(_translate("Dialog", "最大回撤"))
        self.hitratiolabel.setText(_translate("Dialog", "胜率"))
        self.pnlratiolabel.setText(_translate("Dialog", "盈亏比（日）"))
        self.sharpestdlabel.setText(_translate("Dialog", "夏普波动率"))
        self.returnstdlabel.setText(_translate("Dialog", "年化收益波动率"))
        self.totalreturnlabel.setText(_translate("Dialog", "总收益"))
        self.totaltradeslabel.setText(_translate("Dialog", "交易次数"))
        self.avgtradesprofitlabel.setText(_translate("Dialog", "平均盈利"))
        self.avgtradeslosslabel.setText(_translate("Dialog", "平均亏损"))
        
    def on_ok_clicked(self):
        self.okdict=dict()
        self.okdict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.okdict['strategy']=self.strategylineEdit.text()
        visualbacktestpath=os.path.join(self.okdict['strategyfolder'],'visualbacktest')
        if not os.path.exists(visualbacktestpath):
            os.mkdir(visualbacktestpath)
            
        SignalGenerator=AutomatedCTATradeHelper.Signal_Generator(self.okdict['strategyfolder'], self.okdict['strategy'])
        Strategy=SignalGenerator.Load_Strategy()
        evalperf=Strategy['EvalPerformence']
        TimestampSignal=Strategy['TimestampSignal']
        TimestampPriceX=Strategy['TimestampPriceX']

        backtestMins=BacktestPerformence.backtest_minutes(TimestampSignal,TimestampPriceX,opencost=1.5/10000,closecost=1.5/10000,closecost2=10/10000)
        backtestMins.actionlist_generator()
        avgholding=evalperf.avg_holding_period(backtestMins.actionlist, Type='LongShort') 
        avgholding=avgholding/ np.timedelta64(1, 'h')/24
        avgtradeprofit=evalperf.returns[evalperf.returns>0].mean()*avgholding
        avgtradeloss=evalperf.returns[evalperf.returns<0].mean()*avgholding
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date,evalperf.SimpleValue]).transpose(),'value')
        plot_trial.date_line_plot(os.path.join(visualbacktestpath,'value.png'))
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date[1:],evalperf.returns]).transpose(),'returns')
        plot_trial.hist_plot(os.path.join(visualbacktestpath,'returns.png'))
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date,-1*np.array(evalperf.SimpleDrawback)]).transpose(),'Drawback')
        plot_trial.area_plot(os.path.join(visualbacktestpath,'drawback.png'))
        
        fig = evalperf.Sharpe_Ratio_by_year()[1].plot(kind='bar').get_figure()
        fig.savefig(os.path.join(visualbacktestpath,"SharpeByYear.png"))
        fig.clf()
            
        valuepixmap = QPixmap(os.path.join(visualbacktestpath,'value.png'))
        self.value.setPixmap(valuepixmap)

        returnspixmap = QPixmap(os.path.join(visualbacktestpath,'returns.png'))
        self.Returndist.setPixmap(returnspixmap)
        
        drawbackpixmap = QPixmap(os.path.join(visualbacktestpath,'drawback.png'))
        self.drawdown.setPixmap(drawbackpixmap)
        
        sharpepixmap = QPixmap(os.path.join(visualbacktestpath,'SharpeByYear.png'))
        self.SharpeByYear.setPixmap(sharpepixmap)
        
        self.sharpeall.setText('%.2f' % (round(evalperf.Sharpe_Ratio_all(),2)))
        self.avgreturn.setText('%.2f' % (round(np.mean(evalperf.Return_by_year())[0],4)*100)+'%')
        self.maxdd.setText('%.2f' % (round(evalperf.max_drawdown(choice_simple_interest=False),4)*100)+'%')
        self.hitratio.setText('%.2f' % (round(evalperf.win_rate(),4)*100)+'%')
        self.pnlratio.setText('%.2f' % (round(evalperf.profit_and_loss_ratio(),2)))
        self.sharpestd.setText('%.2f' % (round(np.std(evalperf.Sharpe_Ratio_by_year()[1]),2)))
        self.returnstd.setText('%.2f' % (round(np.std(evalperf.Return_by_year())[0],4)*100)+'%')
        self.totalreturn.setText('%.2f' % (round(evalperf.SimpleValue[-1],2)))
        self.avgtradesprofit.setText('%.4f' % (round(avgtradeprofit,2)))
        self.avgtradesloss.setText('%.4f' % (round(avgtradeloss,2)))
        self.totaltrades.setText('%.2f' % (round(avgholding,2))+'days')
        
        
        
        
             
class Trading_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__(flags=Qt.WindowMinimizeButtonHint|Qt.WindowMaximizeButtonHint|Qt.WindowCloseButtonHint)

        self.trade_thread = TradeThread()      
        self.setupUi(self)        
        self.deploydict=dict()
        self.tradedict = dict()



    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.NonModal)
        Dialog.resize(1034, 810)
        self.strategylabel = QtWidgets.QLabel(Dialog)
        self.strategylabel.setGeometry(QtCore.QRect(100, 300, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.LStypecomboBox = QtWidgets.QComboBox(Dialog)
        self.LStypecomboBox.setGeometry(QtCore.QRect(270, 160, 87, 22))
        self.LStypecomboBox.setObjectName("LStypecomboBox")
        self.LStypecomboBox.addItem("")
        self.LStypecomboBox.addItem("")
        self.LStypecomboBox.addItem("")
        self.LStypelabel = QtWidgets.QLabel(Dialog)
        self.LStypelabel.setGeometry(QtCore.QRect(101, 150, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.LStypelabel.setFont(font)
        self.LStypelabel.setObjectName("LStypelabel")
        self.VtSymbollabel = QtWidgets.QLabel(Dialog)
        self.VtSymbollabel.setGeometry(QtCore.QRect(100, 250, 111, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.VtSymbollabel.setFont(font)
        self.VtSymbollabel.setObjectName("VtSymbollabel")
        self.strategylineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategylineEdit.setGeometry(QtCore.QRect(270, 310, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.VtSymbollineEdit = QtWidgets.QLineEdit(Dialog)
        self.VtSymbollineEdit.setGeometry(QtCore.QRect(270, 260, 181, 21))
        self.VtSymbollineEdit.setText("")
        self.VtSymbollineEdit.setObjectName("VtSymbollineEdit")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(101, 199, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(270, 210, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.vnpypathtypelabel = QtWidgets.QLabel(Dialog)
        self.vnpypathtypelabel.setGeometry(QtCore.QRect(540, 300, 151, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.vnpypathtypelabel.setFont(font)
        self.vnpypathtypelabel.setObjectName("vnpypathtypelabel")
        self.trade = QtWidgets.QPushButton(Dialog)
        self.trade.setGeometry(QtCore.QRect(450, 710, 141, 41))
        self.trade.setObjectName("trade")
        self.cancel = QtWidgets.QPushButton(Dialog)
        self.cancel.setGeometry(QtCore.QRect(850, 710, 141, 41))
        self.cancel.setObjectName("cancel")
        self.deploy = QtWidgets.QPushButton(Dialog)
        self.deploy.setGeometry(QtCore.QRect(50, 710, 141, 41))
        self.deploy.setObjectName("deploy")
        self.vnpypathlineEdit = QtWidgets.QLineEdit(Dialog)
        self.vnpypathlineEdit.setGeometry(QtCore.QRect(760, 310, 181, 21))
        self.vnpypathlineEdit.setText("")
        self.vnpypathlineEdit.setObjectName("vnpypathlineEdit")
        self.vnpystrategyfoldertypelabel = QtWidgets.QLabel(Dialog)
        self.vnpystrategyfoldertypelabel.setGeometry(QtCore.QRect(540, 200, 191, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.vnpystrategyfoldertypelabel.setFont(font)
        self.vnpystrategyfoldertypelabel.setObjectName("vnpystrategyfoldertypelabel")
        self.vnpystrategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.vnpystrategyfolderlineEdit.setGeometry(QtCore.QRect(760, 210, 181, 21))
        self.vnpystrategyfolderlineEdit.setText("")
        self.vnpystrategyfolderlineEdit.setObjectName("vnpystrategyfolderlineEdit")
        self.vnpysettingpathtypelabel = QtWidgets.QLabel(Dialog)
        self.vnpysettingpathtypelabel.setGeometry(QtCore.QRect(540, 250, 201, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.vnpysettingpathtypelabel.setFont(font)
        self.vnpysettingpathtypelabel.setObjectName("vnpysettingpathtypelabel")
        self.vnpysettingpathlineEdit = QtWidgets.QLineEdit(Dialog)
        self.vnpysettingpathlineEdit.setGeometry(QtCore.QRect(760, 260, 181, 21))
        self.vnpysettingpathlineEdit.setText("")
        self.vnpysettingpathlineEdit.setObjectName("vnpysettingpathlineEdit")
        self.mockcheckBox = QtWidgets.QCheckBox(Dialog)
        self.mockcheckBox.setGeometry(QtCore.QRect(540, 150, 351, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.mockcheckBox.setFont(font)
        self.mockcheckBox.setObjectName("mockcheckBox")
        self.stoptrade = QtWidgets.QPushButton(Dialog)
        self.stoptrade.setGeometry(QtCore.QRect(600, 710, 141, 41))
        self.stoptrade.setObjectName("stoptrade")
        self.signaltextBrowser = QtWidgets.QTextBrowser(Dialog)
        self.signaltextBrowser.setGeometry(QtCore.QRect(50, 440, 941, 251))
        self.signaltextBrowser.setObjectName("signaltextBrowser")
        self.siganlBrowerlabel = QtWidgets.QLabel(Dialog)
        self.siganlBrowerlabel.setGeometry(QtCore.QRect(440, 400, 161, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.siganlBrowerlabel.setFont(font)
        self.siganlBrowerlabel.setObjectName("siganlBrowerlabel")
        self.canceldeploy = QtWidgets.QPushButton(Dialog)
        self.canceldeploy.setGeometry(QtCore.QRect(200, 710, 141, 41))
        self.canceldeploy.setObjectName("canceldeploy")
        self.orderwaitsclabel = QtWidgets.QLabel(Dialog)
        self.orderwaitsclabel.setGeometry(QtCore.QRect(100, 349, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.orderwaitsclabel.setFont(font)
        self.orderwaitsclabel.setObjectName("orderwaitsclabel")
        self.orderwaitscspinBox = QtWidgets.QSpinBox(Dialog)
        self.orderwaitscspinBox.setGeometry(QtCore.QRect(270, 360, 81, 22))
        self.orderwaitscspinBox.setMaximum(999)
        self.orderwaitscspinBox.setProperty("value", 15)
        self.orderwaitscspinBox.setObjectName("orderwaitscspinBox")
        self.ordervolspinBox = QtWidgets.QSpinBox(Dialog)
        self.ordervolspinBox.setGeometry(QtCore.QRect(760, 360, 81, 22))
        self.ordervolspinBox.setMaximum(9999)
        self.ordervolspinBox.setProperty("value", 1)
        self.ordervolspinBox.setObjectName("ordervolspinBox")
        self.ordervollabel = QtWidgets.QLabel(Dialog)
        self.ordervollabel.setGeometry(QtCore.QRect(540, 350, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.ordervollabel.setFont(font)
        self.ordervollabel.setObjectName("ordervollabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(330, 80, 331, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(410, 30, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  
        Dialog.setWindowIcon(icon)

        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(1034, 810))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        Dialog.setPalette(palette)
        
        self.trade.clicked.connect(self.on_trade_clicked)
        self.trade_thread.signal.connect(self.on_trade)
        self.stoptrade.clicked.connect(self.on_stoptrade)
        self.deploy.clicked.connect(self.on_deploy_clicked)
        self.canceldeploy.clicked.connect(self.on_cancel_deploy)
        
        self.retranslateUi(Dialog)
        self.cancel.clicked.connect(Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)


    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "实时交易启动"))
        self.maintitlelabel.setText(_translate("Dialog", "霹雳侠"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.LStypecomboBox.setItemText(0, _translate("Dialog", "既多也空"))
        self.LStypecomboBox.setItemText(1, _translate("Dialog", "只多不空"))
        self.LStypecomboBox.setItemText(2, _translate("Dialog", "只空不多"))
        self.LStypelabel.setText(_translate("Dialog", "多空控制"))
        self.VtSymbollabel.setText(_translate("Dialog", "VtSymbol"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "必须以Auto_开头"))
        self.VtSymbollineEdit.setPlaceholderText(_translate("Dialog", "IC1812"))
        self.strategyfolderlabel.setText(_translate("Dialog", "存储路径"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\Strategyfolder"))
        self.vnpypathtypelabel.setText(_translate("Dialog", "VNPY文件夹路径"))
        self.trade.setText(_translate("Dialog", "交易"))
        self.cancel.setText(_translate("Dialog", "取消"))
        self.deploy.setText(_translate("Dialog", "部署"))
        self.vnpypathlineEdit.setPlaceholderText(_translate("Dialog", "C:\\vnpy"))
        self.vnpystrategyfoldertypelabel.setText(_translate("Dialog", "VNPY策略文件夹路径"))
        self.vnpystrategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\tools\\Anaconda2\\Lib\\site-packages\\vnpy-1.9.0-py2.7.egg\\vnpy\\trader\\app\\ctaStrategy\\strategy"))
        self.vnpysettingpathtypelabel.setText(_translate("Dialog", "VNPY策略字典路径"))
        self.vnpysettingpathlineEdit.setPlaceholderText(_translate("Dialog", "C:\\vnpy\\examples\\VnTrader"))
        self.mockcheckBox.setText(_translate("Dialog", "接入实盘，若勾选，则填写以下内容"))
        self.stoptrade.setText(_translate("Dialog", "停止交易"))
        self.siganlBrowerlabel.setText(_translate("Dialog", "交易信号浏览器"))
        self.canceldeploy.setText(_translate("Dialog", "撤销部署"))
        self.orderwaitsclabel.setText(_translate("Dialog", "报撤单间隔(秒)"))
        self.ordervollabel.setText(_translate("Dialog", "开仓手数"))
        
    
    def on_deploy_clicked(self):
        self.deploydict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.deploydict['LStypecomboBox']=self.LStypecomboBox.currentText()
        self.deploydict['strategy']=self.strategylineEdit.text()
        if len(self.deploydict['strategy'])==0:
            self.deploydict['strategy']=None
        self.deploydict['VtSymbol']=self.VtSymbollineEdit.text()
        if len(self.deploydict['VtSymbol'])==0:
            self.deploydict['VtSymbol']=None
        self.deploydict['vnpypath']=self.vnpypathlineEdit.text()
        if len(self.deploydict['vnpypath'])==0:
            self.deploydict['vnpypath']=None
        self.deploydict['vnpystrategyfolder']=self.vnpystrategyfolderlineEdit.text()
        if len(self.deploydict['vnpystrategyfolder'])==0:
            vnpyegg=fnmatch.filter(os.listdir(r'C:\tools\Anaconda2\Lib\site-packages\\'), 'vnpy*.egg')
            if len(vnpyegg)!=0:
                self.deploydict['vnpystrategyfolder']=os.path.join(r'C:\tools\Anaconda2\Lib\site-packages',vnpyegg[0],r'vnpy\trader\app\ctaStrategy\strategy')
            else:
                self.deploydict['vnpystrategyfolder']=r'C:\tools\Anaconda2\Lib\site-packages\vnpy-1.9.2-py2.7.egg\vnpy\trader\app\ctaStrategy\strategy'
        self.deploydict['vnpysettingpath']=self.vnpysettingpathlineEdit.text()  
        if len(self.deploydict['vnpysettingpath'])==0:
            self.deploydict['vnpysettingpath']=r'C:\vnpy\examples\VnTrader'  
        try:
            self.deploydict['signalpath']=AutoStrategy.ReadListLinebyLine('SignalPath.txt',os.getcwd())[0]
        except:    
            self.deploydict['signalpath']=r'C:\tools\Anaconda3\Lib\site-packages'
        self.deploydict['mock']=not self.mockcheckBox.isChecked()
        self.deploydict['ordervol']=self.ordervolspinBox.value()
        self.deploydict['orderwaitsc']=self.orderwaitscspinBox.value()
        AutoStrategy.Deploy(strategy=self.deploydict['strategy'],strategyfolder=self.deploydict['strategyfolder'],
                            vtSymbol=self.deploydict['VtSymbol'],vnpypath=self.deploydict['vnpypath'],
                            vnpystrategyfolder=self.deploydict['vnpystrategyfolder'],vnpysettingpath=self.deploydict['vnpysettingpath'],
                            signalpath=self.deploydict['signalpath'],mock=self.deploydict['mock'],sharenum=self.deploydict['ordervol'],orderwaitsc=self.deploydict['orderwaitsc'])


        
        
    def on_cancel_deploy(self):
        self.deploydict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.deploydict['strategy']=self.strategylineEdit.text()
        if len(self.deploydict['strategy'])==0:
            self.deploydict['strategy']=None
        self.deploydict['VtSymbol']=self.VtSymbollineEdit.text()
        if len(self.deploydict['VtSymbol'])==0:
            self.deploydict['VtSymbol']=None
        self.deploydict['vnpypath']=self.vnpypathlineEdit.text()
        if len(self.deploydict['vnpypath'])==0:
            self.deploydict['vnpypath']=None
        self.deploydict['vnpystrategyfolder']=self.vnpystrategyfolderlineEdit.text()
        if len(self.deploydict['vnpystrategyfolder'])==0:
            vnpyegg=fnmatch.filter(os.listdir(r'C:\tools\Anaconda2\Lib\site-packages\\'), 'vnpy*.egg')
            if len(vnpyegg)!=0:
                self.deploydict['vnpystrategyfolder']=os.path.join(r'C:\tools\Anaconda2\Lib\site-packages',vnpyegg[0],r'vnpy\trader\app\ctaStrategy\strategy')
            else:
                self.deploydict['vnpystrategyfolder']=r'C:\tools\Anaconda2\Lib\site-packages\vnpy-1.9.2-py2.7.egg\vnpy\trader\app\ctaStrategy\strategy'
            print (self.deploydict['vnpystrategyfolder'])
        self.deploydict['vnpysettingpath']=self.vnpysettingpathlineEdit.text()  
        if len(self.deploydict['vnpysettingpath'])==0:
            self.deploydict['vnpysettingpath']=r'C:\vnpy\examples\VnTrader' 
        self.deploydict['mock']=not self.mockcheckBox.isChecked()
        AutoStrategy.Cancel_Deploy(self.deploydict['strategy'],self.deploydict['strategyfolder'],self.deploydict['vnpypath'],
                                   self.deploydict['vnpystrategyfolder'],self.deploydict['vnpysettingpath'],self.deploydict['mock'])



    def on_trade_clicked(self):
        self.tradedict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.tradedict['LStypecomboBox']=self.LStypecomboBox.currentText()
        self.tradedict['strategy']=self.strategylineEdit.text()
        if len(self.tradedict['strategy'])==0:
            self.tradedict['strategy']=None
        self.tradedict['VtSymbol']=self.VtSymbollineEdit.text()
        if len(self.tradedict['VtSymbol'])==0:
            self.tradedict['VtSymbol']=None
        self.tradedict['vnpypath']=self.vnpypathlineEdit.text()
        if len(self.tradedict['vnpypath'])==0:
            self.tradedict['vnpypath']=None
        self.tradedict['vnpystrategyfolder']=self.vnpystrategyfolderlineEdit.text()
        if len(self.tradedict['vnpystrategyfolder'])==0:
            vnpyegg=fnmatch.filter(os.listdir(r'C:\tools\Anaconda2\Lib\site-packages\\'), 'vnpy*.egg')
            if len(vnpyegg)!=0:
                self.tradedict['vnpystrategyfolder']=os.path.join(r'C:\tools\Anaconda2\Lib\site-packages',vnpyegg[0],r'vnpy\trader\app\ctaStrategy\strategy')
            else:
                self.tradedict['vnpystrategyfolder']=r'C:\tools\Anaconda2\Lib\site-packages\vnpy-1.9.2-py2.7.egg\vnpy\trader\app\ctaStrategy\strategy'
        self.tradedict['vnpysettingpath']=self.vnpysettingpathlineEdit.text()  
        if len(self.tradedict['vnpysettingpath'])==0:
            self.tradedict['vnpysettingpath']=None
        try:
            self.tradedict['signalpath']=AutoStrategy.ReadListLinebyLine('SignalPath.txt',os.getcwd())[0]
        except:    
            self.tradedict['signalpath']=r'C:\tools\Anaconda3\Lib\site-packages'
        self.tradedict['mock']=not self.mockcheckBox.isChecked()   
        self.tradedict['ordervol']=self.ordervolspinBox.value()
        self.tradedict['orderwaitsc']=self.orderwaitscspinBox.value()
        
        SignalGenerator=AutoStrategy.AutomatedCTATradeHelper.Signal_Generator(self.tradedict['strategyfolder'], self.tradedict['strategy'])
        Strategy=SignalGenerator.Load_Strategy()   
        self.tradedict['code']=Strategy['Code']   
        if type(Strategy['Method']) is not str:
            self.tradedict['strategytype']='基于规则'
        else:
            self.tradedict['strategytype']='机器学习'
        self.tradedict['freq']=str(Strategy['TimestampPriceX']['DATETIME'].diff().value_counts().idxmax())
        self.tradedict['freq']=re.findall('[0-9]{2}:[0-9]{2}:[0-9]{2}',self.tradedict['freq'])[0]
        self.tradedict['freq']=int(self.tradedict['freq'][1:2])*60+int(self.tradedict['freq'][3:5])
        self.tradedict['freq']=str(self.tradedict['freq'])+'分钟线'
        
        potitime=Strategy['TimestampPriceX']['Time'].value_counts()
        potitime=list(potitime[potitime>potitime.max()*0.4].index)
        self.tradedict['potitime']=[(datetime.datetime.combine(datetime.date(1992,3,25),x)+datetime.timedelta(minutes=1)).time() for x in potitime]       
        
        self.tradedict['starttime']=Strategy['TimestampPriceX']['DATETIME'].iloc[-1]
        
        self.trade_thread.tradedict = self.tradedict # Get the git URL
        self.trade.setEnabled(False)  # Disables the pushButton
        self.trade_thread.start()  # Finally starts the thread               


    def on_trade(self,tradestr):
        self.signaltextBrowser.append(tradestr)

    def on_stoptrade(self):
        self.trade_thread.quit()
        self.trade_thread.wait()
        self.trade.setEnabled(True)
        self.stoptrade.setEnabled(False)
        

        
class Ui_MainWindow(object):
    
    def __init__(self):
        self.dialogs = list()
        self.createparadict=dict()
        self.create_thread = CreateThread()  # This is the thread object
        
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(936, 931)
        font = QtGui.QFont()
        font.setFamily("Arial")
        MainWindow.setFont(font)
        MainWindow.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        MainWindow.setAcceptDrops(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setToolTipDuration(7)
        MainWindow.setAutoFillBackground(True)
        MainWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.numfeaturespinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.numfeaturespinBox.setGeometry(QtCore.QRect(260, 310, 71, 22))
        self.numfeaturespinBox.setProperty("value", 5)
        self.numfeaturespinBox.setObjectName("numfeaturespinBox")
        self.pprdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.pprdoubleSpinBox.setGeometry(QtCore.QRect(680, 590, 70, 22))
        self.pprdoubleSpinBox.setMaximum(0.99)
        self.pprdoubleSpinBox.setSingleStep(0.01)
        self.pprdoubleSpinBox.setProperty("value", 0.8)
        self.pprdoubleSpinBox.setObjectName("pprdoubleSpinBox")
        self.subtitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.subtitlelabel.setGeometry(QtCore.QRect(260, 40, 411, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.intradayclosecostlabel = QtWidgets.QLabel(self.centralwidget)
        self.intradayclosecostlabel.setGeometry(QtCore.QRect(90, 499, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.intradayclosecostlabel.setFont(font)
        self.intradayclosecostlabel.setObjectName("intradayclosecostlabel")
        self.maxgenspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.maxgenspinBox.setGeometry(QtCore.QRect(680, 190, 71, 22))
        self.maxgenspinBox.setMaximum(9999)
        self.maxgenspinBox.setProperty("value", 2)
        self.maxgenspinBox.setObjectName("maxgenspinBox")
        self.fprlabel = QtWidgets.QLabel(self.centralwidget)
        self.fprlabel.setGeometry(QtCore.QRect(510, 530, 151, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.fprlabel.setFont(font)
        self.fprlabel.setObjectName("fprlabel")
        self.strategylineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.strategylineEdit.setGeometry(QtCore.QRect(260, 260, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.RLlabel = QtWidgets.QLabel(self.centralwidget)
        self.RLlabel.setGeometry(QtCore.QRect(510, 100, 371, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(True)
        font.setWeight(75)
        self.RLlabel.setFont(font)
        self.RLlabel.setWordWrap(False)
        self.RLlabel.setObjectName("RLlabel")
        self.closecostlabel = QtWidgets.QLabel(self.centralwidget)
        self.closecostlabel.setGeometry(QtCore.QRect(90, 449, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.closecostlabel.setFont(font)
        self.closecostlabel.setObjectName("closecostlabel")
        self.opencostdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.opencostdoubleSpinBox.setGeometry(QtCore.QRect(260, 410, 91, 22))
        self.opencostdoubleSpinBox.setDecimals(5)
        self.opencostdoubleSpinBox.setMaximum(1.0)
        self.opencostdoubleSpinBox.setSingleStep(0.001)
        self.opencostdoubleSpinBox.setProperty("value", 0.001)
        self.opencostdoubleSpinBox.setObjectName("opencostdoubleSpinBox")
        self.breedinglabel = QtWidgets.QLabel(self.centralwidget)
        self.breedinglabel.setGeometry(QtCore.QRect(510, 280, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.breedinglabel.setFont(font)
        self.breedinglabel.setObjectName("breedinglabel")
        self.codelineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.codelineEdit.setGeometry(QtCore.QRect(260, 210, 181, 21))
        self.codelineEdit.setText("")
        self.codelineEdit.setObjectName("codelineEdit")
        self.pprlabel = QtWidgets.QLabel(self.centralwidget)
        self.pprlabel.setGeometry(QtCore.QRect(510, 580, 151, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.pprlabel.setFont(font)
        self.pprlabel.setObjectName("pprlabel")
        self.fprdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.fprdoubleSpinBox.setGeometry(QtCore.QRect(680, 540, 70, 22))
        self.fprdoubleSpinBox.setMaximum(0.99)
        self.fprdoubleSpinBox.setSingleStep(0.01)
        self.fprdoubleSpinBox.setProperty("value", 0.8)
        self.fprdoubleSpinBox.setObjectName("fprdoubleSpinBox")
        self.closecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.closecostdoubleSpinBox.setGeometry(QtCore.QRect(260, 460, 91, 22))
        self.closecostdoubleSpinBox.setDecimals(5)
        self.closecostdoubleSpinBox.setMaximum(1.0)
        self.closecostdoubleSpinBox.setSingleStep(0.001)
        self.closecostdoubleSpinBox.setProperty("value", 0.001)
        self.closecostdoubleSpinBox.setObjectName("closecostdoubleSpinBox")
        self.popsizelabel = QtWidgets.QLabel(self.centralwidget)
        self.popsizelabel.setGeometry(QtCore.QRect(510, 130, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.popsizelabel.setFont(font)
        self.popsizelabel.setObjectName("popsizelabel")
        self.maxdepthspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.maxdepthspinBox.setGeometry(QtCore.QRect(680, 490, 71, 22))
        self.maxdepthspinBox.setProperty("value", 2)
        self.maxdepthspinBox.setObjectName("maxdepthspinBox")
        self.numtryspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.numtryspinBox.setGeometry(QtCore.QRect(260, 360, 71, 22))
        self.numtryspinBox.setMaximum(9999)
        self.numtryspinBox.setProperty("value", 3)
        self.numtryspinBox.setObjectName("numtryspinBox")
        self.codelabel = QtWidgets.QLabel(self.centralwidget)
        self.codelabel.setGeometry(QtCore.QRect(90, 200, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.codelabel.setFont(font)
        self.codelabel.setObjectName("codelabel")
        self.mutationrateSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.mutationrateSpinBox.setGeometry(QtCore.QRect(680, 240, 70, 22))
        self.mutationrateSpinBox.setMaximum(0.99)
        self.mutationrateSpinBox.setSingleStep(0.01)
        self.mutationrateSpinBox.setProperty("value", 0.8)
        self.mutationrateSpinBox.setObjectName("mutationrateSpinBox")
        self.createtypelabel = QtWidgets.QLabel(self.centralwidget)
        self.createtypelabel.setGeometry(QtCore.QRect(91, 100, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.createtypelabel.setFont(font)
        self.createtypelabel.setObjectName("createtypelabel")
        self.strategyfolderlabel = QtWidgets.QLabel(self.centralwidget)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(91, 149, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.maintitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.maintitlelabel.setGeometry(QtCore.QRect(380, 0, 171, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setAlignment(QtCore.Qt.AlignCenter)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.intradayclosecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.intradayclosecostdoubleSpinBox.setGeometry(QtCore.QRect(260, 510, 91, 22))
        self.intradayclosecostdoubleSpinBox.setDecimals(5)
        self.intradayclosecostdoubleSpinBox.setMaximum(1.0)
        self.intradayclosecostdoubleSpinBox.setSingleStep(0.001)
        self.intradayclosecostdoubleSpinBox.setProperty("value", 0.001)
        self.intradayclosecostdoubleSpinBox.setObjectName("intradayclosecostdoubleSpinBox")
        self.opencostlabel = QtWidgets.QLabel(self.centralwidget)
        self.opencostlabel.setGeometry(QtCore.QRect(90, 399, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.opencostlabel.setFont(font)
        self.opencostlabel.setObjectName("opencostlabel")
        self.strategylabel = QtWidgets.QLabel(self.centralwidget)
        self.strategylabel.setGeometry(QtCore.QRect(90, 250, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.pnewSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.pnewSpinBox.setGeometry(QtCore.QRect(680, 340, 70, 22))
        self.pnewSpinBox.setMaximum(0.99)
        self.pnewSpinBox.setSingleStep(0.01)
        self.pnewSpinBox.setProperty("value", 0.8)
        self.pnewSpinBox.setObjectName("pnewSpinBox")
        self.pnewlabel = QtWidgets.QLabel(self.centralwidget)
        self.pnewlabel.setGeometry(QtCore.QRect(510, 330, 111, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.pnewlabel.setFont(font)
        self.pnewlabel.setObjectName("pnewlabel")
        self.mutationratelabel = QtWidgets.QLabel(self.centralwidget)
        self.mutationratelabel.setGeometry(QtCore.QRect(510, 230, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.mutationratelabel.setFont(font)
        self.mutationratelabel.setObjectName("mutationratelabel")
        self.breedingrateSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.breedingrateSpinBox.setGeometry(QtCore.QRect(680, 290, 70, 22))
        self.breedingrateSpinBox.setMaximum(0.99)
        self.breedingrateSpinBox.setSingleStep(0.01)
        self.breedingrateSpinBox.setProperty("value", 0.8)
        self.breedingrateSpinBox.setObjectName("breedingrateSpinBox")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(260, 160, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.strategytypecomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.strategytypecomboBox.setGeometry(QtCore.QRect(260, 110, 91, 22))
        self.strategytypecomboBox.setObjectName("strategytypecomboBox")
        self.strategytypecomboBox.addItem("")
        self.strategytypecomboBox.addItem("")
        self.numfeaturelabel = QtWidgets.QLabel(self.centralwidget)
        self.numfeaturelabel.setGeometry(QtCore.QRect(90, 299, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.numfeaturelabel.setFont(font)
        self.numfeaturelabel.setObjectName("numfeaturelabel")
        self.cancel = QtWidgets.QPushButton(self.centralwidget)
        self.cancel.setGeometry(QtCore.QRect(750, 820, 81, 41))
        self.cancel.setObjectName("cancel")
        self.popsizespinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.popsizespinBox.setGeometry(QtCore.QRect(680, 140, 71, 22))
        self.popsizespinBox.setMaximum(9999)
        self.popsizespinBox.setProperty("value", 10)
        self.popsizespinBox.setObjectName("popsizespinBox")
        self.maxdepthlabel = QtWidgets.QLabel(self.centralwidget)
        self.maxdepthlabel.setGeometry(QtCore.QRect(510, 480, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.maxdepthlabel.setFont(font)
        self.maxdepthlabel.setObjectName("maxdepthlabel")
        self.maxgenlabel = QtWidgets.QLabel(self.centralwidget)
        self.maxgenlabel.setGeometry(QtCore.QRect(510, 180, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.maxgenlabel.setFont(font)
        self.maxgenlabel.setObjectName("maxgenlabel")
        self.numtrylabel = QtWidgets.QLabel(self.centralwidget)
        self.numtrylabel.setGeometry(QtCore.QRect(90, 349, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.numtrylabel.setFont(font)
        self.numtrylabel.setObjectName("numtrylabel")
        self.rlabel = QtWidgets.QLabel(self.centralwidget)
        self.rlabel.setGeometry(QtCore.QRect(90, 549, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.rlabel.setFont(font)
        self.rlabel.setObjectName("rlabel")
        self.backtestlabel = QtWidgets.QLabel(self.centralwidget)
        self.backtestlabel.setGeometry(QtCore.QRect(90, 599, 101, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestlabel.setFont(font)
        self.backtestlabel.setObjectName("backtestlabel")
        self.rdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.rdoubleSpinBox.setGeometry(QtCore.QRect(260, 560, 91, 22))
        self.rdoubleSpinBox.setDecimals(5)
        self.rdoubleSpinBox.setMaximum(1.0)
        self.rdoubleSpinBox.setSingleStep(0.001)
        self.rdoubleSpinBox.setProperty("value", 0.05)
        self.rdoubleSpinBox.setObjectName("rdoubleSpinBox")
        self.backtestcomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.backtestcomboBox.setGeometry(QtCore.QRect(260, 610, 87, 22))
        self.backtestcomboBox.setObjectName("backtestcomboBox")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")
        self.signalfreqlabel = QtWidgets.QLabel(self.centralwidget)
        self.signalfreqlabel.setGeometry(QtCore.QRect(90, 650, 131, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.signalfreqlabel.setFont(font)
        self.signalfreqlabel.setObjectName("signalfreqlabel")
        self.signalfreqcomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.signalfreqcomboBox.setGeometry(QtCore.QRect(260, 660, 87, 22))
        self.signalfreqcomboBox.setMinimumContentsLength(0)
        self.signalfreqcomboBox.setObjectName("signalfreqcomboBox")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.StartdateTimeEdit = QtWidgets.QDateTimeEdit(self.centralwidget)
        self.StartdateTimeEdit.setGeometry(QtCore.QRect(260, 710, 194, 22))
        self.StartdateTimeEdit.setDate(QtCore.QDate(2007, 1, 1))
        self.StartdateTimeEdit.setObjectName("StartdateTimeEdit")
        self.backteststarttimelabel = QtWidgets.QLabel(self.centralwidget)
        self.backteststarttimelabel.setGeometry(QtCore.QRect(90, 700, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backteststarttimelabel.setFont(font)
        self.backteststarttimelabel.setObjectName("backteststarttimelabel")
        self.backtestendtimelabel = QtWidgets.QLabel(self.centralwidget)
        self.backtestendtimelabel.setGeometry(QtCore.QRect(90, 750, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestendtimelabel.setFont(font)
        self.backtestendtimelabel.setObjectName("backtestendtimelabel")
        self.EnddateTimeEdit = QtWidgets.QDateTimeEdit(self.centralwidget)
        self.EnddateTimeEdit.setGeometry(QtCore.QRect(260, 760, 194, 22))
        self.EnddateTimeEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(2018, 1, 1), QtCore.QTime(0, 0, 0)))
        self.EnddateTimeEdit.setDate(QtCore.QDate(2018, 1, 1))
        self.EnddateTimeEdit.setObjectName("EnddateTimeEdit")
        self.backtestrollinglabel = QtWidgets.QLabel(self.centralwidget)
        self.backtestrollinglabel.setGeometry(QtCore.QRect(510, 689, 121, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.backtestrollinglabel.setFont(font)
        self.backtestrollinglabel.setObjectName("backtestrollinglabel")
        self.backtestrollingcomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.backtestrollingcomboBox.setGeometry(QtCore.QRect(690, 700, 141, 22))
        self.backtestrollingcomboBox.setObjectName("backtestrollingcomboBox")
        self.backtestrollingcomboBox.addItem("")
        self.backtestrollingcomboBox.addItem("")
        self.RuleBasedlabel = QtWidgets.QLabel(self.centralwidget)
        self.RuleBasedlabel.setGeometry(QtCore.QRect(510, 440, 371, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.RuleBasedlabel.setFont(font)
        self.RuleBasedlabel.setWordWrap(False)
        self.RuleBasedlabel.setObjectName("RuleBasedlabel")
        self.MLBasedlabel = QtWidgets.QLabel(self.centralwidget)
        self.MLBasedlabel.setGeometry(QtCore.QRect(510, 650, 371, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.MLBasedlabel.setFont(font)
        self.MLBasedlabel.setWordWrap(False)
        self.MLBasedlabel.setObjectName("MLBasedlabel")
        self.rollingwindownlabel = QtWidgets.QLabel(self.centralwidget)
        self.rollingwindownlabel.setGeometry(QtCore.QRect(510, 740, 231, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.rollingwindownlabel.setFont(font)
        self.rollingwindownlabel.setObjectName("rollingwindownlabel")
        self.rollingwindownspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.rollingwindownspinBox.setGeometry(QtCore.QRect(750, 750, 81, 22))
        self.rollingwindownspinBox.setMaximum(9999)
        self.rollingwindownspinBox.setProperty("value", 500)
        self.rollingwindownspinBox.setObjectName("rollingwindownspinBox")
        self.keepbestcheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.keepbestcheckBox.setGeometry(QtCore.QRect(90, 800, 351, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.keepbestcheckBox.setFont(font)
        self.keepbestcheckBox.setObjectName("keepbestcheckBox")
        self.topnlabel = QtWidgets.QLabel(self.centralwidget)
        self.topnlabel.setGeometry(QtCore.QRect(510, 380, 141, 41))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.topnlabel.setFont(font)
        self.topnlabel.setObjectName("topnlabel")
        self.topnspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.topnspinBox.setGeometry(QtCore.QRect(680, 390, 71, 22))
        self.topnspinBox.setMaximum(9999)
        self.topnspinBox.setProperty("value", 5)
        self.topnspinBox.setObjectName("topnspinBox")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 936, 26))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.custommenu = QtWidgets.QMenu(self.menubar)
        self.custommenu.setObjectName("custommenu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        oImage = QImage("background.jpg")
        sImage = oImage.scaled(QSize(936, 931))                   # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))                     # 10 = Windowrole
        MainWindow.setPalette(palette)
        
        self.Trading = QtWidgets.QAction(MainWindow)
        self.Trading.setObjectName("Trading") 
        self.Trading.triggered.connect(self.on_Trading_triggered)
        
        self.reg = QtWidgets.QAction(MainWindow)
        self.reg.setObjectName("reg")
        self.reg.triggered.connect(self.on_Reg_triggered)
        
        self.backtest = QtWidgets.QAction(MainWindow)
        self.backtest.setObjectName("backtest")
        self.backtest.triggered.connect(self.on_Backtest_triggered)
        
        self.criteria = QtWidgets.QAction(MainWindow)
        self.criteria.setObjectName("criteria")
        self.criteria.triggered.connect(self.on_criteria_triggered)
        
        self.attribute = QtWidgets.QAction(MainWindow)
        self.attribute.setObjectName("attribute")
        self.attribute.triggered.connect(self.on_attribute_triggered)
        
        self.loaddatacsv = QtWidgets.QAction(MainWindow)
        self.loaddatacsv.setObjectName("loaddatacsv")
        self.loaddatacsv.triggered.connect(self.on_loadcsv_triggered)
        
        self.dbsetting = QtWidgets.QAction(MainWindow)
        self.dbsetting.setObjectName("dbsetting")
        self.dbsetting.triggered.connect(self.on_dbsetting_triggered)

        self.MC = QtWidgets.QAction(MainWindow)
        self.MC.setObjectName("MC")
        self.MC.triggered.connect(self.on_MC_triggered)
        
        self.BacktestOOB = QtWidgets.QAction(MainWindow)
        self.BacktestOOB.setObjectName("BacktestOOB")
        self.BacktestOOB.triggered.connect(self.on_BacktestOOB_triggered)
        
        self.menu.addAction(self.reg)
        self.menu.addAction(self.Trading)
        self.menu.addAction(self.backtest)
        self.menu.addAction(self.attribute)
        self.menu.addAction(self.MC)
        self.menu.addAction(self.BacktestOOB)
        self.custommenu.addAction(self.criteria)
        self.custommenu.addAction(self.loaddatacsv)
        self.custommenu.addAction(self.dbsetting)

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.custommenu.menuAction())

        self.create = QtWidgets.QPushButton(self.centralwidget)
        self.create.setGeometry(QtCore.QRect(650, 820, 81, 41))
        self.create.setObjectName("create")

        self.retranslateUi(MainWindow)
        self.cancel.clicked.connect(self.on_cancel)
        self.create.clicked.connect(self.on_create_clicked)
        self.create_thread.signal.connect(self.finished)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "霹雳侠"))
        self.subtitlelabel.setText(_translate("MainWindow", "策略自动产生与配置交易一站式平台"))
        self.intradayclosecostlabel.setText(_translate("MainWindow", "日内平仓成本"))
        self.fprlabel.setText(_translate("MainWindow", "规则节点概率"))
        self.strategylineEdit.setPlaceholderText(_translate("MainWindow", "必须以Auto_开头"))
        self.RLlabel.setText(_translate("MainWindow", "遗传算法参数"))
        self.closecostlabel.setText(_translate("MainWindow", "平仓成本"))
        self.breedinglabel.setText(_translate("MainWindow", "交叉概率"))
        self.codelineEdit.setPlaceholderText(_translate("MainWindow", "SH000905"))
        self.pprlabel.setText(_translate("MainWindow", "变量节点概率"))
        self.popsizelabel.setText(_translate("MainWindow", "起始种群数目"))
        self.codelabel.setText(_translate("MainWindow", "标的代码"))
        self.createtypelabel.setText(_translate("MainWindow", "产生方式"))
        self.strategyfolderlabel.setText(_translate("MainWindow", "存储路径"))
        self.create.setText(_translate("MainWindow", "产生"))
        self.maintitlelabel.setText(_translate("MainWindow", "霹雳侠"))
        self.opencostlabel.setText(_translate("MainWindow", "开仓成本"))
        self.strategylabel.setText(_translate("MainWindow", "策略名称"))
        self.pnewlabel.setText(_translate("MainWindow", "新建概率"))
        self.mutationratelabel.setText(_translate("MainWindow", "变异概率"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("MainWindow", "C:\\Strategyfolder"))
        self.strategytypecomboBox.setItemText(0, _translate("MainWindow", "机器学习"))
        self.strategytypecomboBox.setItemText(1, _translate("MainWindow", "基于规则"))
        self.numfeaturelabel.setText(_translate("MainWindow", "因子数目"))
        self.cancel.setText(_translate("MainWindow", "取消"))
        self.maxdepthlabel.setText(_translate("MainWindow", "最大深度"))
        self.maxgenlabel.setText(_translate("MainWindow", "最大演化代数"))
        self.numtrylabel.setText(_translate("MainWindow", "最大尝试数"))
        self.rlabel.setText(_translate("MainWindow", "止损百分比"))
        self.backtestlabel.setText(_translate("MainWindow", "回测方式"))
        self.backtestcomboBox.setItemText(0, _translate("MainWindow", "多空回测"))
        self.backtestcomboBox.setItemText(1, _translate("MainWindow", "单多回测"))
        self.backtestcomboBox.setItemText(2, _translate("MainWindow", "单空回测"))
        self.signalfreqlabel.setText(_translate("MainWindow", "信号频率"))
        self.signalfreqcomboBox.setCurrentText(_translate("MainWindow", "30分钟线"))
        self.signalfreqcomboBox.setItemText(1, _translate("MainWindow", "5分钟线"))
        #self.signalfreqcomboBox.setItemText(2, _translate("MainWindow", "10分钟线"))
        self.signalfreqcomboBox.setItemText(2, _translate("MainWindow", "15分钟线"))
        self.signalfreqcomboBox.setItemText(0, _translate("MainWindow", "30分钟线"))
        self.signalfreqcomboBox.setItemText(3, _translate("MainWindow", "60分钟线"))
        #self.signalfreqcomboBox.setItemText(5, _translate("MainWindow", "120分钟线"))
        self.backteststarttimelabel.setText(_translate("MainWindow", "回测开始时间"))
        self.backtestendtimelabel.setText(_translate("MainWindow", "回测结束时间"))
        self.backtestrollinglabel.setText(_translate("MainWindow", "滚动方式"))
        self.backtestrollingcomboBox.setItemText(0, _translate("MainWindow", "固定起点"))
        self.backtestrollingcomboBox.setItemText(1, _translate("MainWindow", "固定窗口长度"))
        self.RuleBasedlabel.setText(_translate("MainWindow", "若选择基于规则，请填写以下内容"))
        self.MLBasedlabel.setText(_translate("MainWindow", "若选择基于机器学习，请填写以下内容"))
        self.rollingwindownlabel.setText(_translate("MainWindow", "固定窗口长度滚动K线数"))
        self.keepbestcheckBox.setText(_translate("MainWindow", "若没有达到要求，保留最佳策略"))
        self.topnlabel.setText(_translate("MainWindow", "每代优胜个体"))
        self.menu.setTitle(_translate("MainWindow", "策略"))
        self.custommenu.setTitle(_translate("MainWindow", "个性化"))
        self.Trading.setText(_translate("MainWindow", "交易策略"))
        self.Trading.setToolTip(_translate("MainWindow", "<html><head/><body><p>交易策略</p></body></html>"))
        self.reg.setText(_translate("MainWindow", "注册"))
        self.backtest.setText(_translate("MainWindow", "观看回测"))
        self.criteria.setText(_translate("MainWindow", "策略生成条件"))
        self.attribute.setText(_translate("MainWindow", "观看归因"))
        self.loaddatacsv.setText(_translate("MainWindow", "CSV数据导入"))
        self.dbsetting.setText(_translate("MainWindow", "数据库路径设置"))
        self.MC.setText(_translate("MainWindow", "蒙特卡洛参数敏感性分析"))
        self.BacktestOOB.setText(_translate("MainWindow", "模拟盘回溯测试"))        

    def on_Trading_triggered(self):
        dialog = Trading_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()

    def on_Backtest_triggered(self):
        dialog = BK_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()
    
    def on_criteria_triggered(self):
        dialog = Criteria_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()
        
    def on_attribute_triggered(self):
        dialog = Attribute_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()
        
    def on_Reg_triggered(self):
        webbrowser.open('http://estrategyhouse.com')
        
    def on_loadcsv_triggered(self):
        dialog = Load_CSV_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()        

    def on_dbsetting_triggered(self):
        dialog = DBSetting_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()           

    def on_MC_triggered(self):
        dialog = MC_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()  
        
    def on_BacktestOOB_triggered(self):
        dialog = BacktestOOB_Ui_Dialog()
        self.dialogs.append(dialog)
        dialog.show()          
          
        
    def on_create_clicked(self):
        self.createparadict['numfeature']=self.numfeaturespinBox.value()
        self.createparadict['ppr']=self.pprdoubleSpinBox.value()
        self.createparadict['maxgen']=self.maxgenspinBox.value()
        self.createparadict['strategy']=self.strategylineEdit.text()
        if len(self.createparadict['strategy'])==0:
            self.createparadict['strategy']=None
        self.createparadict['opencost']=self.opencostdoubleSpinBox.value()
        self.createparadict['code']=self.codelineEdit.text()
        self.createparadict['fpr']=self.fprdoubleSpinBox.value()
        self.createparadict['closecost']=self.closecostdoubleSpinBox.value()
        self.createparadict['maxdepth']=self.maxdepthspinBox.value()
        self.createparadict['numtry']=self.numtryspinBox.value()
        self.createparadict['mutationrate']=self.mutationrateSpinBox.value()
        self.createparadict['intradayclosecost']=self.intradayclosecostdoubleSpinBox.value()
        self.createparadict['pnew']=self.pnewSpinBox.value()
        self.createparadict['breedingrate']=self.breedingrateSpinBox.value()
        self.createparadict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.createparadict['strategytype']=self.strategytypecomboBox.currentText()
        self.createparadict['popsize']=self.popsizespinBox.value()
        self.createparadict['r']=self.rdoubleSpinBox.value()
        self.createparadict['backtest']=self.backtestcomboBox.currentText()
        if self.createparadict['backtest']=='多空回测':
            self.createparadict['backtest']='LongShort'
        elif self.createparadict['backtest']=='单多回测':
            self.createparadict['backtest']='LongOnly'
        else:
            self.createparadict['backtest']='ShortOnly'
        self.createparadict['freq']=self.signalfreqcomboBox.currentText()
        self.createparadict['rollingtype']=self.backtestrollingcomboBox.currentText()
        self.createparadict['starttime']=self.StartdateTimeEdit.dateTime().toPyDateTime()
        self.createparadict['endtime']=self.EnddateTimeEdit.dateTime().toPyDateTime()
        self.createparadict['keepbest']=self.keepbestcheckBox.isChecked()
        if self.backtestrollingcomboBox.currentText()=="固定窗口长度":
            self.createparadict['rollingn']=self.rollingwindownspinBox.value()
        else:
            self.createparadict['rollingn']=None        
        self.createparadict['topn']=self.topnspinBox.value()
        print (self.createparadict)
        self.create_thread.createparadict = self.createparadict  # Get the git URL
        self.create.setEnabled(False)  # Disables the pushButton
        self.create_thread.start()  # Finally starts the thread



    def finished(self, signal):
        self.create_thread.quit()
        self.create_thread.wait()
        self.create.setEnabled(True)  # Enable the pushButton
        
    def on_cancel(self):
        self.create_thread.terminate()
        self.create_thread.quit()
        self.create_thread.wait()
        self.create.setEnabled(True)  # Enable the pushButton
        self.cancel.setEnabled(True)

        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

