# -*- coding: utf-8 -*-
"""
这是一个示例模板，
通过AutoStrategy.create来产生策略
通过AutoStrategy.deploy来部署实盘（模拟盘可以省略该步骤）
通过AutoStrategy.run来运行实盘或者是实盘
运行时候需要修改模板以适应自己的系统
"""


from AutoStrategy.IOdata import Downloader
import datetime
import numpy as np
import threading
import time
from AutoStrategy.TradingSystem.Trade import time_in_range
import AutoStrategy

Trading=False

def get_time():
    """
    The function is to create a global variable of current time: TimeNow
    """
    global TimeNow, Timeeer
    TimeNow=datetime.datetime.now().time()
    Timeeer=threading.Timer(1.0, get_time)
    Timeeer.start()


        
if __name__ == "__main__":  
    
    # 如果是产生策略或者部署策略
    if not Trading:
        
        """
        下载的数据TimestampPriceX为pandas DataFrame
        字段需要是['Code','DATETIME','Date','Time','open','high','low','close','amount','volume']
        
        示例从天软中下载数据，用户可使用自己的数据源，但需要整理为相同的字段
        """
        TianRuanDownloader=Downloader.TianRuan_Downloader("E:\\Analyse.NET")
        TimestampPriceX=TianRuanDownloader.continuous_min_download(datetime.datetime(2007,1,1,0,0,0), datetime.datetime.now(), 'SZ000905','hfq','30分钟线')         
        # remove the duplicated Time
        TimestampPriceX=TimestampPriceX.drop_duplicates(subset='DATETIME', keep='first', inplace=False)        
        # remove the rows that contain zeros
        TimestampPriceX = TimestampPriceX.replace({'0':np.nan, 0:np.nan})
        
        
        
        
        
        """
        实现根据K线自动产生交易策略
        使用时需至少输入产生策略基于的K线，策略存储的文件夹，基于的标的代码
        TimestampPriceX: 产生策略基于的K线，字段是['Code','DATETIME','Date','Time','open','high','low','close','amount','volume']
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
        strategyfolder: 产生策略存储的文件夹，若不存在，自动创建
        code: 策略基于的标的代码
        strategy: 策略名称
        numfeature: 一次抽取的因子数目
        numstrategy: 需要产生的策略数目
        numtry: 最大尝试次数
        opencost: 开仓成本
        closecost: 隔日平仓成本
        intradayclosecost: 当日平仓成本
        Type: 回测规则，'LongShort'是多空回测，'LongOnly'是只多不空回测
        moduleFile: 存放StrategyCritertia.json'的位置
        """
        strategyName=AutoStrategy.create(TimestampPriceX=TimestampPriceX, strategyfolder='C:\\Users\\pc\\Desktop\\AutoCTA\\AutoCTATest', code='SH000905',numfeature=5,numtry=500)
        
        
        
        
        '''
        部署策略
        strategy: 策略名
        strategyfolder:策略所在文件夹
        vtSymbol:vnpy的实盘交易代码
        vnpypath: vnpy下载下来的所在路径，不能和vnpysettingpath同时为None
        vnpystrategyfolder:strategy 文件夹通常是在 vnpy\\trader\\app\\ctaStrategy' 下
        vnpysettingpath: 用来添加策略至策略字典的路径，通常在VnTrader下
        signalpath: 交易信号写入的数据库，若None则默认在strategyfolder向上一级文件夹下
        '''
        AutoStrategy.deploy(strategy=strategyName,strategyfolder='C:\\Users\\pc\\Desktop\\AutoCTA\\AutoCTATest',vtSymbol='IC1809',vnpypath='C:\\Users\\pc\\Desktop\\vnpy-master')
    
    # 如果实盘交易
    if Trading:
        lock = threading.Lock()    
        
        
        get_time()
        time.sleep(1)
        
        
        def Trading(strategyName):
            '''
            实盘交易示例函数，传入策略名
            '''
            
            '''
            time_in_range是策略执行的时间，例如对于股票市场，是每日9:31到11:30，13:00到15:00
            TimeNow.minute % 30==1的含义是没过三十分钟计算一次交易信号
            '''
            if ((time_in_range(datetime.time(9,31,0),datetime.time(11,30,0),TimeNow)) or (time_in_range(datetime.time(13,00,0),datetime.time(15,0,0),TimeNow))):
                if (TimeNow.minute % 30==1):
                    lock.acquire()

                    """
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
                    """                    
                    TianRuanDownloader=Downloader.TianRuan_Downloader("E:\\Analyse.NET")
                    Newdata=TianRuanDownloader.continuous_min_download(datetime.datetime.now()-datetime.timedelta(days=100), datetime.datetime.now(), 'SH000905','hfq','30分钟线') 

                    '''
                    运行策略
                    如果有VNPY了，并且经过了Deploy，在运行run就是实盘；
                    如果没有，就是模拟盘
                    strategy: 策略名
                    strategyfolder: 策略所在文件夹
                    vtSymbol: 实际交易标的代码，需要与Deploy时候一致，如果None，那么为模拟盘交易，否则为实盘。
                    Newdata: 新的数据['Code', 'DATETIME', 'Date', 'Time', 'open', 'high', 'low', 'close','amount', 'volume']
                    signalpath: 交易数据库地址，若None则默认在strategyfolder向上一级文件夹下
                    '''
                    AutoStrategy.run(strategy=strategyName,strategyfolder='C:\\Users\\pc\\Desktop\\AutoCTA\\AutoCTATest',vtSymbol='IC1809',Newdata=Newdata)
                
                    lock.release()
                    
            if (TimeNow>datetime.time(6, 45, 50) and TimeNow<datetime.time(23, 15, 0)):
                '''
                每隔一分钟刷新一下，看是否需要执行交易程序
                '''
                TradingTimer=threading.Timer(60.0, Trading, [strategyName])
                TradingTimer.start() 
            else: 
                TradingTimer.cancel()
                    
                    
        strategyName='Auto_2018_09_08_15_49_59_SH000905'
        Trading(strategyName)