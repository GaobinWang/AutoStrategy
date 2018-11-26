# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'total.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QDateTime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import QEventLoop
from PyQt5.QtGui import QPixmap
import datetime
import numpy as np
import re
import webbrowser
import pandas as pd
import os
import gc
from AutoStrategy.IOdata import Downloader
from AutoStrategy import AutoStrategy
from AutoStrategy.AutomatedCTAGenerator import AutomatedCTATradeHelper
from AutoStrategy.Visualization import plot




class CreateThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.createparadict = dict()

    # run method gets called when we start the thread
    def run(self):
        TianRuanDownloader=Downloader.TianRuan_Downloader("E:\\Analyse.NET")
        TianRuanDownloader.login()
        TimestampPriceX=TianRuanDownloader.continuous_min_download(datetime.datetime(2007,1,1,0,0,0), datetime.datetime.now(), self.createparadict['code'],'hfq',self.createparadict['freq'])         
        TianRuanDownloader.logout()
        # remove the duplicated Time
        TimestampPriceX=TimestampPriceX.drop_duplicates(subset='DATETIME', keep='first', inplace=False)        
        # remove the rows that contain zeros
        TimestampPriceX = TimestampPriceX.replace({'0':np.nan, 0:np.nan})
        
        if self.createparadict['strategytype']=='机器学习':            
            AutoStrategy.Machine_Learning_Create(TimestampPriceX, strategyfolder=self.createparadict['strategyfolder'], code=self.createparadict['code'], 
                                                 strategy=self.createparadict['strategy'], numfeature=self.createparadict['numfeature'], 
                                                 numstrategy=1, numtry=self.createparadict['numtry'], 
                                                 opencost=self.createparadict['opencost'],closecost=self.createparadict['closecost'], 
                                                 intradayclosecost=self.createparadict['intradayclosecost'],r=self.createparadict['r'],Type=self.createparadict['backtest'])
        else:
            AutoStrategy.Rule_Based_Create(TimestampPriceX, 
                                           strategyfolder=self.createparadict['strategyfolder'], code=self.createparadict['code'], 
                                           strategy=self.createparadict['strategy'], numfeature=self.createparadict['numfeature'], numstrategy=1, 
                                           numtry=self.createparadict['numtry'], target='Sharpe_Ratio',maxdepth=self.createparadict['maxdepth'],
                                           fpr=self.createparadict['fpr'],ppr=self.createparadict['ppr'],popsize=self.createparadict['popsize'],
                                           maxgen=self.createparadict['maxgen'],mutationrate=self.createparadict['mutationrate'],
                                           breedingrate=self.createparadict['breedingrate'],pexp=0.9,pnew=self.createparadict['pnew'], 
                                           opencost=self.createparadict['opencost'],closecost=self.createparadict['closecost'], 
                                           intradayclosecost=self.createparadict['intradayclosecost'],r=self.createparadict['r'],Type=self.createparadict['backtest'])
        gc.collect()
        self.signal.emit(self.createparadict['strategyfolder'])
        





class DeployThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.deploydict = dict()

    # run method gets called when we start the thread
    def run(self):
        AutoStrategy.Deploy(strategy=self.deploydict['strategy'],strategyfolder=self.deploydict['strategyfolder'],
                            vtSymbol=self.deploydict['VtSymbol'],vnpypath=self.deploydict['vnpypath'],
                            vnpystrategyfolder=self.deploydict['vnpystrategyfolder'],vnpysettingpath=self.deploydict['vnpysettingpath'],
                            signalpath=self.deploydict['signalpath'],mock=self.deploydict['mock'])

        self.signal.emit(self.deploydict['mock'])
  



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
                TianRuanDownloader=Downloader.TianRuan_Downloader("E:\\Analyse.NET")
                TianRuanDownloader.login()
                Newdata=TianRuanDownloader.continuous_min_download(datetime.datetime.now()-datetime.timedelta(days=100), datetime.datetime.now(), self.tradedict['code'],'hfq',str(self.tradedict['freq'])+'分钟线') 
                TianRuanDownloader.logout()
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
                                                      vtSymbol=self.tradedict['VtSymbol'],Newdata=Newdata,
                                                      signalpath=self.tradedict['signalpath']) 
                else:
                    Pos=AutoStrategy.Rule_Based_Run(strategy=self.tradedict['strategy'],
                                                      strategyfolder=self.tradedict['strategyfolder'],
                                                      vtSymbol=self.tradedict['VtSymbol'],Newdata=Newdata,
                                                      signalpath=self.tradedict['signalpath']) 
                
                gc.collect()
                if Pos is not None:  
                    tradestr=Pos['StrategyName'].iloc[0]+ ' 在 '+Pos['SecurityName'].iloc[0]+' 发出信号 '+str(Pos['Tradeside'].iloc[0])+'@'+str(Pos['Price'].iloc[0])+' 目前仓位 '+str(Pos['Position'].iloc[0])
                    self.signal.emit(tradestr)
                    print (tradestr)
                    
    
    # run method gets called when we start the thread
    def run(self):
        self.tradetimer.start(16000)
        loop = QEventLoop()
        loop.exec_()
        



class Criteria_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)   
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(527, 411)
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        Dialog.setFont(font)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(160, 340, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.sharpealllabel = QtWidgets.QLabel(Dialog)
        self.sharpealllabel.setGeometry(QtCore.QRect(80, 100, 72, 21))
        self.sharpealllabel.setObjectName("sharpealllabel")
        self.avgreturnlabel = QtWidgets.QLabel(Dialog)
        self.avgreturnlabel.setGeometry(QtCore.QRect(80, 130, 111, 31))
        self.avgreturnlabel.setObjectName("avgreturnlabel")
        self.maxddlabel = QtWidgets.QLabel(Dialog)
        self.maxddlabel.setGeometry(QtCore.QRect(80, 170, 91, 31))
        self.maxddlabel.setObjectName("maxddlabel")
        self.sharpestdlabel = QtWidgets.QLabel(Dialog)
        self.sharpestdlabel.setGeometry(QtCore.QRect(80, 210, 111, 31))
        self.sharpestdlabel.setObjectName("sharpestdlabel")
        self.returnstdlabel = QtWidgets.QLabel(Dialog)
        self.returnstdlabel.setGeometry(QtCore.QRect(80, 250, 171, 31))
        self.returnstdlabel.setObjectName("returnstdlabel")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(210, 10, 101, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(140, 60, 241, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.subtitlelabel.setFont(font)
        self.subtitlelabel.setObjectName("subtitlelabel")
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
        self.SRdoubleSpinBox.setGeometry(QtCore.QRect(320, 100, 70, 22))
        self.SRdoubleSpinBox.setDecimals(5)
        self.SRdoubleSpinBox.setSingleStep(0.01)
        self.SRdoubleSpinBox.setProperty("value", 1.0)
        self.SRdoubleSpinBox.setObjectName("SRdoubleSpinBox")
        self.AVGRdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.AVGRdoubleSpinBox.setGeometry(QtCore.QRect(320, 140, 70, 22))
        self.AVGRdoubleSpinBox.setDecimals(5)
        self.AVGRdoubleSpinBox.setSingleStep(0.01)
        self.AVGRdoubleSpinBox.setProperty("value", 0.2)
        self.AVGRdoubleSpinBox.setObjectName("AVGRdoubleSpinBox")
        self.MAXDDdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.MAXDDdoubleSpinBox.setGeometry(QtCore.QRect(320, 180, 70, 22))
        self.MAXDDdoubleSpinBox.setDecimals(5)
        self.MAXDDdoubleSpinBox.setSingleStep(0.01)
        self.MAXDDdoubleSpinBox.setProperty("value", 0.15)
        self.MAXDDdoubleSpinBox.setObjectName("MAXDDdoubleSpinBox")
        self.SRSTDdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.SRSTDdoubleSpinBox.setGeometry(QtCore.QRect(320, 220, 70, 22))
        self.SRSTDdoubleSpinBox.setDecimals(5)
        self.SRSTDdoubleSpinBox.setSingleStep(0.01)
        self.SRSTDdoubleSpinBox.setProperty("value", 2.0)
        self.SRSTDdoubleSpinBox.setObjectName("SRSTDdoubleSpinBox")
        self.AVGRSTDdoubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.AVGRSTDdoubleSpinBox.setGeometry(QtCore.QRect(320, 260, 70, 22))
        self.AVGRSTDdoubleSpinBox.setDecimals(5)
        self.AVGRSTDdoubleSpinBox.setSingleStep(0.01)
        self.AVGRSTDdoubleSpinBox.setProperty("value", 1.0)
        self.AVGRSTDdoubleSpinBox.setObjectName("AVGRSTDdoubleSpinBox")

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
        self.maintitlelabel.setText(_translate("Dialog", "黑科技"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.SRGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.SRGLcomboBox.setItemText(1, _translate("Dialog", "<"))
        self.AVGRGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.AVGRGLcomboBox.setItemText(1, _translate("Dialog", "<"))
        self.MAXDDGLcomboBox.setCurrentText(_translate("Dialog", "<"))
        self.MAXDDGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.MAXDDGLcomboBox.setItemText(1, _translate("Dialog", "<"))
        self.SRSTDGLcomboBox.setCurrentText(_translate("Dialog", "<"))
        self.SRSTDGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.SRSTDGLcomboBox.setItemText(1, _translate("Dialog", "<"))
        self.AVGRSTDGLcomboBox.setCurrentText(_translate("Dialog", "<"))
        self.AVGRSTDGLcomboBox.setItemText(0, _translate("Dialog", ">"))
        self.AVGRSTDGLcomboBox.setItemText(1, _translate("Dialog", "<"))

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
        
        
        

class BK_Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)   
        
        
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1082, 1036)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(660, 970, 341, 32))
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
        self.strategylabel.setGeometry(QtCore.QRect(470, 110, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(40, 110, 81, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
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
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(360, 70, 241, 21))
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(430, 20, 101, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.valuelabel = QtWidgets.QLabel(Dialog)
        self.valuelabel.setGeometry(QtCore.QRect(180, 150, 31, 16))
        self.valuelabel.setObjectName("valuelabel")
        self.drawdownlabel = QtWidgets.QLabel(Dialog)
        self.drawdownlabel.setGeometry(QtCore.QRect(630, 150, 31, 16))
        self.drawdownlabel.setObjectName("drawdownlabel")
        self.SharpeByYearlabel = QtWidgets.QLabel(Dialog)
        self.SharpeByYearlabel.setGeometry(QtCore.QRect(170, 490, 81, 16))
        self.SharpeByYearlabel.setObjectName("SharpeByYearlabel")
        self.Returndistlabel = QtWidgets.QLabel(Dialog)
        self.Returndistlabel.setGeometry(QtCore.QRect(610, 490, 81, 16))
        self.Returndistlabel.setObjectName("Returndistlabel")
        self.sharpealllabel = QtWidgets.QLabel(Dialog)
        self.sharpealllabel.setGeometry(QtCore.QRect(850, 190, 72, 15))
        self.sharpealllabel.setObjectName("sharpealllabel")
        self.sharpeall = QtWidgets.QLabel(Dialog)
        self.sharpeall.setGeometry(QtCore.QRect(970, 190, 72, 15))
        self.sharpeall.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sharpeall.setText("")
        self.sharpeall.setObjectName("sharpeall")
        self.avgreturnlabel = QtWidgets.QLabel(Dialog)
        self.avgreturnlabel.setGeometry(QtCore.QRect(850, 230, 91, 16))
        self.avgreturnlabel.setObjectName("avgreturnlabel")
        self.avgreturn = QtWidgets.QLabel(Dialog)
        self.avgreturn.setGeometry(QtCore.QRect(970, 230, 72, 15))
        self.avgreturn.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.avgreturn.setText("")
        self.avgreturn.setObjectName("avgreturn")
        self.maxddlabel = QtWidgets.QLabel(Dialog)
        self.maxddlabel.setGeometry(QtCore.QRect(850, 270, 72, 15))
        self.maxddlabel.setObjectName("maxddlabel")
        self.maxdd = QtWidgets.QLabel(Dialog)
        self.maxdd.setGeometry(QtCore.QRect(970, 270, 72, 15))
        self.maxdd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.maxdd.setText("")
        self.maxdd.setObjectName("maxdd")
        self.hitratiolabel = QtWidgets.QLabel(Dialog)
        self.hitratiolabel.setGeometry(QtCore.QRect(850, 310, 72, 15))
        self.hitratiolabel.setObjectName("hitratiolabel")
        self.hitratio = QtWidgets.QLabel(Dialog)
        self.hitratio.setGeometry(QtCore.QRect(970, 310, 72, 15))
        self.hitratio.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.hitratio.setText("")
        self.hitratio.setObjectName("hitratio")
        self.pnlratiolabel = QtWidgets.QLabel(Dialog)
        self.pnlratiolabel.setGeometry(QtCore.QRect(850, 350, 91, 16))
        self.pnlratiolabel.setObjectName("pnlratiolabel")
        self.pnlratio = QtWidgets.QLabel(Dialog)
        self.pnlratio.setGeometry(QtCore.QRect(970, 350, 72, 15))
        self.pnlratio.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.pnlratio.setText("")
        self.pnlratio.setObjectName("pnlratio")
        self.sharpestdlabel = QtWidgets.QLabel(Dialog)
        self.sharpestdlabel.setGeometry(QtCore.QRect(850, 390, 81, 16))
        self.sharpestdlabel.setObjectName("sharpestdlabel")
        self.sharpestd = QtWidgets.QLabel(Dialog)
        self.sharpestd.setGeometry(QtCore.QRect(970, 390, 72, 15))
        self.sharpestd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sharpestd.setText("")
        self.sharpestd.setObjectName("sharpestd")
        self.returnstdlabel = QtWidgets.QLabel(Dialog)
        self.returnstdlabel.setGeometry(QtCore.QRect(850, 430, 111, 16))
        self.returnstdlabel.setObjectName("returnstdlabel")
        self.returnstd = QtWidgets.QLabel(Dialog)
        self.returnstd.setGeometry(QtCore.QRect(970, 430, 72, 15))
        self.returnstd.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.returnstd.setText("")
        self.returnstd.setObjectName("returnstd")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "回测展示"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "策略名字必须以Auto_开头"))
        self.strategyfolderlineEdit.setPlaceholderText(_translate("Dialog", "C:\\Strategyfolder"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.strategyfolderlabel.setText(_translate("Dialog", "存储路径"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.maintitlelabel.setText(_translate("Dialog", "黑科技"))
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
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date,evalperf.SimpleValue]).transpose(),'value')
        plot_trial.date_line_plot(os.path.join(visualbacktestpath,'value.png'))
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date[1:],evalperf.returns]).transpose(),'returns')
        plot_trial.hist_plot(os.path.join(visualbacktestpath,'returns.png'))
        
        plot_trial=plot.pyplt_plot(pd.DataFrame([evalperf.date,-1*np.array(evalperf.SimpleDrawback)]).transpose(),'Drawback')
        plot_trial.area_plot(os.path.join(visualbacktestpath,'drawback.png'))
        
        fig = evalperf.Sharpe_Ratio_by_year()[1].plot(kind='bar').get_figure()
        fig.savefig(os.path.join(visualbacktestpath,"SharpeByYear.png"))
        fig.clf()
        #fig.cla()
        #fig.close()
            
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
        
        
class Ui_Dialog(QtWidgets.QDialog):
    
    def __init__(self):
        super().__init__()

        self.trade_thread = TradeThread()      
        self.deploy_thread = DeployThread()
        self.setupUi(self)        
        self.deploydict=dict()
        self.tradedict = dict()



    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1044, 810)
        self.maintitlelabel = QtWidgets.QLabel(Dialog)
        self.maintitlelabel.setGeometry(QtCore.QRect(440, 30, 101, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setObjectName("maintitlelabel")
        self.subtitlelabel = QtWidgets.QLabel(Dialog)
        self.subtitlelabel.setGeometry(QtCore.QRect(370, 80, 241, 21))
        self.subtitlelabel.setObjectName("subtitlelabel")
        self.strategylabel = QtWidgets.QLabel(Dialog)
        self.strategylabel.setGeometry(QtCore.QRect(50, 310, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        self.strategytypecomboBox = QtWidgets.QComboBox(Dialog)
        self.strategytypecomboBox.setGeometry(QtCore.QRect(220, 160, 87, 22))
        self.strategytypecomboBox.setObjectName("strategytypecomboBox")
        self.strategytypecomboBox.addItem("")
        self.strategytypecomboBox.addItem("")
        self.createtypelabel = QtWidgets.QLabel(Dialog)
        self.createtypelabel.setGeometry(QtCore.QRect(51, 160, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.createtypelabel.setFont(font)
        self.createtypelabel.setObjectName("createtypelabel")
        self.VtSymbollabel = QtWidgets.QLabel(Dialog)
        self.VtSymbollabel.setGeometry(QtCore.QRect(50, 260, 81, 20))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.VtSymbollabel.setFont(font)
        self.VtSymbollabel.setObjectName("VtSymbollabel")
        self.strategylineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategylineEdit.setGeometry(QtCore.QRect(220, 310, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        self.VtSymbollineEdit = QtWidgets.QLineEdit(Dialog)
        self.VtSymbollineEdit.setGeometry(QtCore.QRect(220, 260, 181, 21))
        self.VtSymbollineEdit.setText("")
        self.VtSymbollineEdit.setObjectName("VtSymbollineEdit")
        self.strategyfolderlabel = QtWidgets.QLabel(Dialog)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(51, 210, 81, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(220, 210, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        self.vnpypathtypelabel = QtWidgets.QLabel(Dialog)
        self.vnpypathtypelabel.setGeometry(QtCore.QRect(540, 310, 121, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.vnpypathtypelabel.setFont(font)
        self.vnpypathtypelabel.setObjectName("vnpypathtypelabel")
        
        self.trade = QtWidgets.QPushButton(Dialog)
        self.trade.setGeometry(QtCore.QRect(450, 710, 141, 41))
        self.trade.setObjectName("trade")
        self.trade.clicked.connect(self.on_trade_clicked)
        self.trade_thread.signal.connect(self.on_trade)
                
        self.cancel = QtWidgets.QPushButton(Dialog)
        self.cancel.setGeometry(QtCore.QRect(850, 710, 141, 41))
        self.cancel.setObjectName("cancel")
        
        self.deploy = QtWidgets.QPushButton(Dialog)
        self.deploy.setGeometry(QtCore.QRect(50, 710, 141, 41))
        self.deploy.setObjectName("deploy")
        self.deploy.clicked.connect(self.on_deploy_clicked)
        self.deploy_thread.signal.connect(self.deploy_finished)
        
        self.vnpypathlineEdit = QtWidgets.QLineEdit(Dialog)
        self.vnpypathlineEdit.setGeometry(QtCore.QRect(760, 310, 181, 21))
        self.vnpypathlineEdit.setText("")
        self.vnpypathlineEdit.setObjectName("vnpypathlineEdit")
        self.vnpystrategyfoldertypelabel = QtWidgets.QLabel(Dialog)
        self.vnpystrategyfoldertypelabel.setGeometry(QtCore.QRect(540, 210, 171, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.vnpystrategyfoldertypelabel.setFont(font)
        self.vnpystrategyfoldertypelabel.setObjectName("vnpystrategyfoldertypelabel")
        self.vnpystrategyfolderlineEdit = QtWidgets.QLineEdit(Dialog)
        self.vnpystrategyfolderlineEdit.setGeometry(QtCore.QRect(760, 210, 181, 21))
        self.vnpystrategyfolderlineEdit.setText("")
        self.vnpystrategyfolderlineEdit.setObjectName("vnpystrategyfolderlineEdit")
        self.vnpysettingpathtypelabel = QtWidgets.QLabel(Dialog)
        self.vnpysettingpathtypelabel.setGeometry(QtCore.QRect(540, 260, 171, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.vnpysettingpathtypelabel.setFont(font)
        self.vnpysettingpathtypelabel.setObjectName("vnpysettingpathtypelabel")
        self.vnpysettingpathlineEdit = QtWidgets.QLineEdit(Dialog)
        self.vnpysettingpathlineEdit.setGeometry(QtCore.QRect(760, 260, 181, 21))
        self.vnpysettingpathlineEdit.setText("")
        self.vnpysettingpathlineEdit.setObjectName("vnpysettingpathlineEdit")
        self.signalpathtypelabel = QtWidgets.QLabel(Dialog)
        self.signalpathtypelabel.setGeometry(QtCore.QRect(50, 360, 171, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.signalpathtypelabel.setFont(font)
        self.signalpathtypelabel.setObjectName("signalpathtypelabel")
        self.signalpathlineEdit = QtWidgets.QLineEdit(Dialog)
        self.signalpathlineEdit.setGeometry(QtCore.QRect(220, 360, 181, 21))
        self.signalpathlineEdit.setText("")
        self.signalpathlineEdit.setObjectName("signalpathlineEdit")
        self.mockcheckBox = QtWidgets.QCheckBox(Dialog)
        self.mockcheckBox.setGeometry(QtCore.QRect(540, 160, 351, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.mockcheckBox.setFont(font)
        self.mockcheckBox.setObjectName("mockcheckBox")
        self.stoptrade = QtWidgets.QPushButton(Dialog)
        self.stoptrade.setGeometry(QtCore.QRect(600, 710, 141, 41))
        self.stoptrade.setObjectName("stoptrade")
        self.stoptrade.clicked.connect(self.on_stoptrade)
        
        self.signaltextBrowser = QtWidgets.QTextBrowser(Dialog)
        self.signaltextBrowser.setGeometry(QtCore.QRect(540, 390, 401, 251))
        self.signaltextBrowser.setObjectName("signaltextBrowser")
        self.siganlBrowerlabel = QtWidgets.QLabel(Dialog)
        self.siganlBrowerlabel.setGeometry(QtCore.QRect(540, 360, 141, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.siganlBrowerlabel.setFont(font)
        self.siganlBrowerlabel.setObjectName("siganlBrowerlabel")

        self.retranslateUi(Dialog)
        self.cancel.clicked.connect(Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)




    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "实时交易启动"))
        self.maintitlelabel.setText(_translate("Dialog", "黑科技"))
        self.subtitlelabel.setText(_translate("Dialog", "策略自动产生与配置交易一站式平台"))
        self.strategylabel.setText(_translate("Dialog", "策略名称"))
        self.strategytypecomboBox.setItemText(0, _translate("Dialog", "机器学习"))
        self.strategytypecomboBox.setItemText(1, _translate("Dialog", "基于规则"))
        self.createtypelabel.setText(_translate("Dialog", "产生方式"))
        self.VtSymbollabel.setText(_translate("Dialog", "VtSymbol"))
        self.strategylineEdit.setPlaceholderText(_translate("Dialog", "策略名字必须以Auto_开头"))
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
        self.vnpysettingpathlineEdit.setPlaceholderText(_translate("Dialog", "C:\\vnpy-master\\examples\\VnTrader"))
        self.signalpathtypelabel.setText(_translate("Dialog", "交易数据库路径"))
        self.signalpathlineEdit.setPlaceholderText(_translate("Dialog", "C:\\vnpy\\examples\\VnTrader"))
        self.mockcheckBox.setText(_translate("Dialog", "接入实盘，若勾选，则填写以下内容"))
        self.stoptrade.setText(_translate("Dialog", "停止交易"))
        self.siganlBrowerlabel.setText(_translate("Dialog", "交易信号浏览器"))

        
    
    def on_deploy_clicked(self):
        self.deploydict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.deploydict['strategytype']=self.strategytypecomboBox.currentText()
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
            self.deploydict['vnpystrategyfolder']=r'C:\tools\Anaconda2\Lib\site-packages\vnpy-1.9.0-py2.7.egg\vnpy\trader\app\ctaStrategy\strategy'
        self.deploydict['vnpysettingpath']=self.vnpysettingpathlineEdit.text()  
        if len(self.deploydict['vnpysettingpath'])==0:
            self.deploydict['vnpysettingpath']=r'C:\vnpy\examples\VnTrader'
        self.deploydict['signalpath']=self.signalpathlineEdit.text()
        if len(self.deploydict['signalpath'])==0:
            self.deploydict['signalpath']=None
        self.deploydict['mock']=not self.mockcheckBox.isChecked()
        
        self.deploy_thread.deploydict = self.deploydict # Get the git URL
        self.deploy.setEnabled(False)  # Disables the pushButton
        self.deploy_thread.start()  # Finally starts the thread



    def deploy_finished(self, result):
        self.deploy_thread.quit()
        self.deploy_thread.wait()
        self.deploy.setEnabled(True)  # Enable the pushButton

        
        

    def on_trade_clicked(self):
        self.tradedict['strategyfolder']=self.strategyfolderlineEdit.text()
        self.tradedict['strategytype']=self.strategytypecomboBox.currentText()
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
            self.tradedict['vnpystrategyfolder']=None
        self.tradedict['vnpysettingpath']=self.vnpysettingpathlineEdit.text()  
        if len(self.tradedict['vnpysettingpath'])==0:
            self.tradedict['vnpysettingpath']=None
        self.tradedict['signalpath']=self.signalpathlineEdit.text()
        if len(self.tradedict['signalpath'])==0:
            self.tradedict['signalpath']=None
        self.tradedict['mock']=not self.mockcheckBox.isChecked()   

        SignalGenerator=AutoStrategy.AutomatedCTATradeHelper.Signal_Generator(self.tradedict['strategyfolder'], self.tradedict['strategy'])
        Strategy=SignalGenerator.Load_Strategy()   
        self.tradedict['code']=Strategy['Code']        
        self.tradedict['freq']=str(Strategy['TimestampPriceX']['DATETIME'].diff().value_counts().idxmax())
        self.tradedict['freq']=re.findall('[0-9]{2}:[0-9]{2}:[0-9]{2}',self.tradedict['freq'])[0]
        self.tradedict['freq']=int(self.tradedict['freq'][1:2])*60+int(self.tradedict['freq'][3:5])
        
        potitime=Strategy['TimestampPriceX']['Time'].value_counts()
        potitime=list(potitime[potitime>potitime.max()*0.95].index)
        self.tradedict['potitime']=[(datetime.datetime.combine(datetime.date(1992,3,25),x)+datetime.timedelta(minutes=1)).time() for x in potitime]
        print (self.tradedict)
        
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
        MainWindow.resize(1046, 1000)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        
        self.numfeaturespinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.numfeaturespinBox.setGeometry(QtCore.QRect(200, 390, 46, 22))
        self.numfeaturespinBox.setObjectName("numfeaturespinBox")
        self.numfeaturespinBox.setProperty("value", 5)
        #self.createparadict['numfeature']=self.numfeaturespinBox.value()
        
        
        self.pprdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.pprdoubleSpinBox.setGeometry(QtCore.QRect(820, 340, 70, 22))
        self.pprdoubleSpinBox.setMaximum(0.99)
        self.pprdoubleSpinBox.setSingleStep(0.01)
        self.pprdoubleSpinBox.setProperty("value", 0.8)
        self.pprdoubleSpinBox.setObjectName("pprdoubleSpinBox")
        #self.createparadict['ppr']=self.pprdoubleSpinBox.value()
        
        
        self.subtitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.subtitlelabel.setGeometry(QtCore.QRect(400, 110, 241, 21))
        self.subtitlelabel.setObjectName("subtitlelabel")
        
        
        self.intradayclosecostlabel = QtWidgets.QLabel(self.centralwidget)
        self.intradayclosecostlabel.setGeometry(QtCore.QRect(30, 590, 111, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.intradayclosecostlabel.setFont(font)
        self.intradayclosecostlabel.setObjectName("intradayclosecostlabel")
        
        
        self.maxgenspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.maxgenspinBox.setGeometry(QtCore.QRect(820, 440, 46, 22))
        self.maxgenspinBox.setMaximum(9999)
        self.maxgenspinBox.setProperty("value", 5)
        self.maxgenspinBox.setObjectName("maxgenspinBox")
        #self.createparadict['maxgen']=self.maxgenspinBox.value()
        
        
        self.fprlabel = QtWidgets.QLabel(self.centralwidget)
        self.fprlabel.setGeometry(QtCore.QRect(650, 290, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.fprlabel.setFont(font)
        self.fprlabel.setObjectName("fprlabel")
        
        
        self.strategylineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.strategylineEdit.setGeometry(QtCore.QRect(200, 340, 181, 21))
        self.strategylineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.strategylineEdit.setInputMask("")
        self.strategylineEdit.setText("")
        self.strategylineEdit.setMaxLength(32767)
        self.strategylineEdit.setFrame(True)
        self.strategylineEdit.setObjectName("strategylineEdit")
        #self.createparadict['strategy']=self.strategylineEdit.text()
        #if len(self.createparadict['strategy'])==0:
        #    self.createparadict['strategy']=None
        
        self.RLlabel = QtWidgets.QLabel(self.centralwidget)
        self.RLlabel.setGeometry(QtCore.QRect(650, 190, 331, 16))
        font = QtGui.QFont()
        font.setFamily("Segoe Print")
        font.setPointSize(11)
        font.setBold(True)
        font.setUnderline(True)
        font.setWeight(75)
        self.RLlabel.setFont(font)
        self.RLlabel.setWordWrap(False)
        self.RLlabel.setObjectName("RLlabel")
        
        
        self.closecostlabel = QtWidgets.QLabel(self.centralwidget)
        self.closecostlabel.setGeometry(QtCore.QRect(30, 540, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.closecostlabel.setFont(font)
        self.closecostlabel.setObjectName("closecostlabel")
        
        
        self.opencostdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.opencostdoubleSpinBox.setGeometry(QtCore.QRect(200, 490, 100, 22))
        self.opencostdoubleSpinBox.setDecimals(5)
        self.opencostdoubleSpinBox.setMaximum(1.0)
        self.opencostdoubleSpinBox.setSingleStep(0.0001)
        self.opencostdoubleSpinBox.setProperty("value", 0.001)
        self.opencostdoubleSpinBox.setObjectName("opencostdoubleSpinBox")
        #self.createparadict['opencost']=self.opencostdoubleSpinBox.value()
        
        
        self.breedinglabel = QtWidgets.QLabel(self.centralwidget)
        self.breedinglabel.setGeometry(QtCore.QRect(650, 540, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.breedinglabel.setFont(font)
        self.breedinglabel.setObjectName("breedinglabel")
        
        
        self.codelineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.codelineEdit.setGeometry(QtCore.QRect(200, 290, 181, 21))
        self.codelineEdit.setText("")
        self.codelineEdit.setObjectName("codelineEdit")
        #self.createparadict['code']=self.codelineEdit.text()
        
        self.pprlabel = QtWidgets.QLabel(self.centralwidget)
        self.pprlabel.setGeometry(QtCore.QRect(650, 340, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.pprlabel.setFont(font)
        self.pprlabel.setObjectName("pprlabel")
        
        
        self.fprdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.fprdoubleSpinBox.setGeometry(QtCore.QRect(820, 290, 70, 22))
        self.fprdoubleSpinBox.setMaximum(0.99)
        self.fprdoubleSpinBox.setSingleStep(0.01)
        self.fprdoubleSpinBox.setProperty("value", 0.8)
        self.fprdoubleSpinBox.setObjectName("fprdoubleSpinBox")
        #self.createparadict['fpr']=self.fprdoubleSpinBox.value()

        
        self.closecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.closecostdoubleSpinBox.setGeometry(QtCore.QRect(200, 540, 100, 22))
        self.closecostdoubleSpinBox.setDecimals(5)
        self.closecostdoubleSpinBox.setMaximum(1.0)
        self.closecostdoubleSpinBox.setSingleStep(0.0001)
        self.closecostdoubleSpinBox.setProperty("value", 0.001)
        self.closecostdoubleSpinBox.setObjectName("closecostdoubleSpinBox")
        #self.createparadict['closecost']=self.closecostdoubleSpinBox.value()
        
        
        self.popsizelabel = QtWidgets.QLabel(self.centralwidget)
        self.popsizelabel.setGeometry(QtCore.QRect(650, 390, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.popsizelabel.setFont(font)
        self.popsizelabel.setObjectName("popsizelabel")
        
        
        self.maxdepthspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.maxdepthspinBox.setGeometry(QtCore.QRect(820, 240, 46, 22))
        self.maxdepthspinBox.setProperty("value", 2)
        self.maxdepthspinBox.setObjectName("maxdepthspinBox")
        #self.createparadict['maxdepth']=self.maxdepthspinBox.value()
        
        
        self.numtryspinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.numtryspinBox.setGeometry(QtCore.QRect(200, 440, 46, 22))
        self.numtryspinBox.setMaximum(9999)
        self.numtryspinBox.setProperty("value", 500)
        self.numtryspinBox.setObjectName("numtryspinBox")
        #self.createparadict['numtry']=self.numtryspinBox.value()
        
        
        self.codelabel = QtWidgets.QLabel(self.centralwidget)
        self.codelabel.setGeometry(QtCore.QRect(30, 290, 81, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.codelabel.setFont(font)
        self.codelabel.setObjectName("codelabel")
        
        
        self.mutationrateSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.mutationrateSpinBox.setGeometry(QtCore.QRect(820, 490, 70, 22))
        self.mutationrateSpinBox.setMaximum(0.99)
        self.mutationrateSpinBox.setSingleStep(0.01)
        self.mutationrateSpinBox.setProperty("value", 0.8)
        self.mutationrateSpinBox.setObjectName("mutationrateSpinBox")
        #self.createparadict['mutationrate']=self.mutationrateSpinBox.value()
        
        self.createtypelabel = QtWidgets.QLabel(self.centralwidget)
        self.createtypelabel.setGeometry(QtCore.QRect(31, 190, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.createtypelabel.setFont(font)
        self.createtypelabel.setObjectName("createtypelabel")
        
        
        self.strategyfolderlabel = QtWidgets.QLabel(self.centralwidget)
        self.strategyfolderlabel.setGeometry(QtCore.QRect(31, 240, 81, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.strategyfolderlabel.setFont(font)
        self.strategyfolderlabel.setObjectName("strategyfolderlabel")
        
        
        self.create = QtWidgets.QPushButton(self.centralwidget)
        self.create.setGeometry(QtCore.QRect(710, 880, 141, 41))
        self.create.setObjectName("create")
        self.create.clicked.connect(self.on_create_clicked)
        # Connect the signal from the thread to the finished method
        self.create_thread.signal.connect(self.finished)
        
        
        
        self.maintitlelabel = QtWidgets.QLabel(self.centralwidget)
        self.maintitlelabel.setGeometry(QtCore.QRect(470, 60, 101, 51))
        font = QtGui.QFont()
        font.setFamily("AlternateGothic2 BT")
        font.setPointSize(18)
        self.maintitlelabel.setFont(font)
        self.maintitlelabel.setObjectName("maintitlelabel")
        
        
        self.intradayclosecostdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.intradayclosecostdoubleSpinBox.setGeometry(QtCore.QRect(200, 590, 100, 22))
        self.intradayclosecostdoubleSpinBox.setDecimals(5)
        self.intradayclosecostdoubleSpinBox.setMaximum(1.0)
        self.intradayclosecostdoubleSpinBox.setSingleStep(0.0001)
        self.intradayclosecostdoubleSpinBox.setProperty("value", 0.001)
        self.intradayclosecostdoubleSpinBox.setObjectName("intradayclosecostdoubleSpinBox")
        #self.createparadict['intradayclosecost']=self.intradayclosecostdoubleSpinBox.value()
        
        
        self.opencostlabel = QtWidgets.QLabel(self.centralwidget)
        self.opencostlabel.setGeometry(QtCore.QRect(30, 490, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.opencostlabel.setFont(font)
        self.opencostlabel.setObjectName("opencostlabel")
        
        
        self.strategylabel = QtWidgets.QLabel(self.centralwidget)
        self.strategylabel.setGeometry(QtCore.QRect(30, 340, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.strategylabel.setFont(font)
        self.strategylabel.setObjectName("strategylabel")
        
        
        self.pnewSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.pnewSpinBox.setGeometry(QtCore.QRect(820, 590, 70, 22))
        self.pnewSpinBox.setMaximum(0.99)
        self.pnewSpinBox.setSingleStep(0.01)
        self.pnewSpinBox.setProperty("value", 0.8)
        self.pnewSpinBox.setObjectName("pnewSpinBox")
        #self.createparadict['pnew']=self.pnewSpinBox.value()
        
        
        self.pnewlabel = QtWidgets.QLabel(self.centralwidget)
        self.pnewlabel.setGeometry(QtCore.QRect(650, 590, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.pnewlabel.setFont(font)
        self.pnewlabel.setObjectName("pnewlabel")
        
        
        self.mutationratelabel = QtWidgets.QLabel(self.centralwidget)
        self.mutationratelabel.setGeometry(QtCore.QRect(650, 490, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.mutationratelabel.setFont(font)
        self.mutationratelabel.setObjectName("mutationratelabel")
        
        
        self.breedingrateSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.breedingrateSpinBox.setGeometry(QtCore.QRect(820, 540, 70, 22))
        self.breedingrateSpinBox.setMaximum(0.99)
        self.breedingrateSpinBox.setSingleStep(0.01)
        self.breedingrateSpinBox.setProperty("value", 0.8)
        self.breedingrateSpinBox.setObjectName("breedingrateSpinBox")
        #self.createparadict['breedingrate']=self.breedingrateSpinBox.value()
        
        
        self.strategyfolderlineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.strategyfolderlineEdit.setGeometry(QtCore.QRect(200, 240, 181, 21))
        self.strategyfolderlineEdit.setText("")
        self.strategyfolderlineEdit.setObjectName("strategyfolderlineEdit")
        #self.createparadict['strategyfolder']=self.strategyfolderlineEdit.text()
        
        
        self.strategytypecomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.strategytypecomboBox.setGeometry(QtCore.QRect(200, 190, 87, 22))
        self.strategytypecomboBox.setObjectName("strategytypecomboBox")
        self.strategytypecomboBox.addItem("")
        self.strategytypecomboBox.addItem("")
        #self.createparadict['strategytype']=self.strategytypecomboBox.currentText()
        
        
        self.numfeaturelabel = QtWidgets.QLabel(self.centralwidget)
        self.numfeaturelabel.setGeometry(QtCore.QRect(30, 390, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.numfeaturelabel.setFont(font)
        self.numfeaturelabel.setObjectName("numfeaturelabel")

        
        self.cancel = QtWidgets.QPushButton(self.centralwidget)
        self.cancel.setGeometry(QtCore.QRect(880, 880, 141, 41))
        self.cancel.setObjectName("cancel")
        
        
        self.popsizespinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.popsizespinBox.setGeometry(QtCore.QRect(820, 390, 46, 22))
        self.popsizespinBox.setMaximum(9999)
        self.popsizespinBox.setProperty("value", 10)
        self.popsizespinBox.setObjectName("popsizespinBox")
        #self.createparadict['popsize']=self.popsizespinBox.value()
        
        
        self.maxdepthlabel = QtWidgets.QLabel(self.centralwidget)
        self.maxdepthlabel.setGeometry(QtCore.QRect(650, 240, 71, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.maxdepthlabel.setFont(font)
        self.maxdepthlabel.setObjectName("maxdepthlabel")
        self.maxgenlabel = QtWidgets.QLabel(self.centralwidget)
        self.maxgenlabel.setGeometry(QtCore.QRect(650, 440, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.maxgenlabel.setFont(font)
        self.maxgenlabel.setObjectName("maxgenlabel")
        
        
        self.numtrylabel = QtWidgets.QLabel(self.centralwidget)
        self.numtrylabel.setGeometry(QtCore.QRect(30, 440, 101, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.numtrylabel.setFont(font)
        self.numtrylabel.setObjectName("numtrylabel")
        
        self.rlabel = QtWidgets.QLabel(self.centralwidget)
        self.rlabel.setGeometry(QtCore.QRect(30, 640, 91, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.rlabel.setFont(font)
        self.rlabel.setObjectName("rlabel")
        
        
        self.backtestlabel = QtWidgets.QLabel(self.centralwidget)
        self.backtestlabel.setGeometry(QtCore.QRect(30, 690, 71, 20))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.backtestlabel.setFont(font)
        self.backtestlabel.setObjectName("backtestlabel")
        
        
        self.rdoubleSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.rdoubleSpinBox.setGeometry(QtCore.QRect(200, 640, 70, 22))
        self.rdoubleSpinBox.setDecimals(5)
        self.rdoubleSpinBox.setMaximum(1.0)
        self.rdoubleSpinBox.setSingleStep(0.0001)
        self.rdoubleSpinBox.setObjectName("rdoubleSpinBox")
        self.rdoubleSpinBox.setProperty("value", 0.05)
        
        self.backtestcomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.backtestcomboBox.setGeometry(QtCore.QRect(200, 690, 87, 22))
        self.backtestcomboBox.setObjectName("backtestcomboBox")
        self.backtestcomboBox.addItem("")
        self.backtestcomboBox.addItem("")

        self.signalfreqlabel = QtWidgets.QLabel(self.centralwidget)
        self.signalfreqlabel.setGeometry(QtCore.QRect(30, 740, 81, 21))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(11)
        self.signalfreqlabel.setFont(font)
        self.signalfreqlabel.setObjectName("signalfreqlabel")
        
        self.signalfreqcomboBox = QtWidgets.QComboBox(self.centralwidget)
        self.signalfreqcomboBox.setGeometry(QtCore.QRect(200, 740, 87, 22))
        self.signalfreqcomboBox.setMinimumContentsLength(0)
        self.signalfreqcomboBox.setObjectName("signalfreqcomboBox")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        self.signalfreqcomboBox.addItem("")
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1046, 26))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.custommenu = QtWidgets.QMenu(self.menubar)
        self.custommenu.setObjectName("custommenu")
        MainWindow.setMenuBar(self.menubar)
        
        
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        
        
        self.Trading = QtWidgets.QAction(MainWindow)
        self.Trading.setObjectName("Trading") 
        self.Trading.triggered.connect(self.on_Trading_triggered)
        
        self.reg = QtWidgets.QAction(MainWindow)
        self.reg.setObjectName("reg")
        self.reg.triggered.connect(self.on_Reg_triggered)
        
        #self.login = QtWidgets.QAction(MainWindow)
        #self.login.setObjectName("login")
        
        #self.menu.addAction(self.login)
        self.backtest = QtWidgets.QAction(MainWindow)
        self.backtest.setObjectName("backtest")
        self.backtest.triggered.connect(self.on_Backtest_triggered)
        
        self.criteria = QtWidgets.QAction(MainWindow)
        self.criteria.setObjectName("criteria")
        self.criteria.triggered.connect(self.on_criteria_triggered)
        
        self.menu.addAction(self.reg)
        self.menu.addAction(self.Trading)
        self.menu.addAction(self.backtest)
        self.custommenu.addAction(self.criteria)

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.custommenu.menuAction())

        self.retranslateUi(MainWindow)
        self.cancel.clicked.connect(MainWindow.close)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "自动产生策略黑科技"))
        self.subtitlelabel.setText(_translate("MainWindow", "策略自动产生与配置交易一站式平台"))
        self.intradayclosecostlabel.setText(_translate("MainWindow", "日内平仓成本"))
        self.fprlabel.setText(_translate("MainWindow", "规则节点概率"))
        self.strategylineEdit.setPlaceholderText(_translate("MainWindow", "策略名字必须以Auto_开头"))
        self.RLlabel.setText(_translate("MainWindow", "若选择基于规则，请一起填写以下内容"))
        self.closecostlabel.setText(_translate("MainWindow", "平仓成本"))
        self.breedinglabel.setText(_translate("MainWindow", "交叉概率"))
        self.codelineEdit.setPlaceholderText(_translate("MainWindow", "SH000905"))
        self.pprlabel.setText(_translate("MainWindow", "变量节点概率"))
        self.popsizelabel.setText(_translate("MainWindow", "起始种群数目"))
        self.codelabel.setText(_translate("MainWindow", "标的代码"))
        self.createtypelabel.setText(_translate("MainWindow", "产生方式"))
        self.strategyfolderlabel.setText(_translate("MainWindow", "存储路径"))
        self.create.setText(_translate("MainWindow", "产生"))
        self.maintitlelabel.setText(_translate("MainWindow", "黑科技"))
        self.opencostlabel.setText(_translate("MainWindow", "开仓成本"))
        self.strategylabel.setText(_translate("MainWindow", "策略名称"))
        self.pnewlabel.setText(_translate("MainWindow", "变异概率"))
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
        self.backtestcomboBox.setItemText(0, _translate("MainWindow", "LongShort"))
        self.backtestcomboBox.setItemText(1, _translate("MainWindow", "LonyOnly"))
        self.signalfreqlabel.setText(_translate("MainWindow", "信号频率"))
        self.signalfreqcomboBox.setCurrentText(_translate("MainWindow", "30分钟线"))
        self.signalfreqcomboBox.setItemText(0, _translate("MainWindow", "30分钟线"))
        self.signalfreqcomboBox.setItemText(1, _translate("MainWindow", "5分钟线"))
        self.signalfreqcomboBox.setItemText(2, _translate("MainWindow", "10分钟线"))
        self.signalfreqcomboBox.setItemText(3, _translate("MainWindow", "15分钟线"))
        self.signalfreqcomboBox.setItemText(4, _translate("MainWindow", "60分钟线"))
        self.signalfreqcomboBox.setItemText(5, _translate("MainWindow", "120分钟线"))
        self.menu.setTitle(_translate("MainWindow", "策略"))
        self.Trading.setText(_translate("MainWindow", "交易策略"))
        self.Trading.setToolTip(_translate("MainWindow", "<html><head/><body><p>交易策略</p></body></html>"))
        self.reg.setText(_translate("MainWindow", "注册"))
        self.custommenu.setTitle(_translate("MainWindow", "个性化"))
        #self.login.setText(_translate("MainWindow", "登陆"))
        self.backtest.setText(_translate("MainWindow", "观看回测"))
        self.criteria.setText(_translate("MainWindow", "策略生成条件"))

    def on_Trading_triggered(self):
        dialog = Ui_Dialog()
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
        
    def on_Reg_triggered(self):
        webbrowser.open('http://estrategyhouse.com')
        
        
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
        self.createparadict['freq']=self.signalfreqcomboBox.currentText()
        
        self.create_thread.createparadict = self.createparadict  # Get the git URL
        self.create.setEnabled(False)  # Disables the pushButton
        self.create_thread.start()  # Finally starts the thread



    def finished(self, result):
        self.create_thread.quit()
        self.create_thread.wait()
        self.create.setEnabled(True)  # Enable the pushButton
        
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

