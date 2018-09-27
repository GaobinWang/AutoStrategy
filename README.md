# AutoStrategy
通过人工智能的方法自动产生（1）基于机器学习的策略（2）基于规则的策略

输入是[时间戳，高，开，低，收，成交额，成交量]，输出是一个个策略，详情请参阅《自动产生策略系统使用说明》

常见命令

AutoStrategy.Machine_Learning_Create(TimestampPriceX=TimestampPriceX, strategyfolder='C:\\Users\\maozh\\Desktop\\Work\\StartegyFolder', code='SH000905',numfeature=5,numtry=500)

AutoStrategy.Rule_Based_Create(TimestampPriceX=TimestampPriceX, strategyfolder='C:\\Users\\maozh\\Desktop\\Work\\StartegyFolder', code='SH000905',numfeature=5,numtry=500)

AutoStrategy.Deploy(strategy=strategyName,strategyfolder='C:\\Users\\maozh\\Desktop\\Work\\StartegyFolder',vtSymbol='IC1810',vnpypath='C:\\Users\\maozh\\Downloads\\vnpy\\vnpy-master\\vnpy-master')

AutoStrategy.Machine_Learning_Run(strategy=strategyName,strategyfolder='C:\\Users\\maozh\\Desktop\\Work\\StartegyFolder',vtSymbol='IC1810',Newdata=Newdata)
             
AutoStrategy.Rule_Based_Run(strategy=strategyName,strategyfolder='C:\\Users\\maozh\\Desktop\\Work\\StartegyFolder',vtSymbol='IC1810',Newdata=Newdata)


快速开始
（1）	安装Anaconda3，推荐5.0版本

（2）	安装需要的一些Python包

a)	pip install TA_Lib-0.4.17-cp35-cp35m-win_amd64.whl
b)	pip install tushare
c)	pip install pymysql
d)	pip install passlib
e)	statsmodels版本必须为0.8.0

（3）	若要连接CTP接口进行程序化交易，请安装VNPY（传送门：https://github.com/vnpy/vnpy），注意，安装Anaconda2时候，路径为C:\Anaconda3\envs\Anaconda2。如果talib包无法安装，请cd到安装包下，并pip install TA_Lib-0.4.17-cp27-cp27m-win32.whl。

（4）	将AutoStrategy文件夹放入Anaconda3\Lib\site-packages\ 目录下

（5）	在estrategyhouse.com上注册用户名和密码

（6）	打开Anaconda

（7）	使用import AutoStrategy导入自动产生策略系统，期间会要求用户输入estrategyhouse.com上注册的用户名和密码

（8）	使用create, deploy以及run命令去进行产生策略，部署策略，实盘或模拟盘运行策略

（9）	实盘时候首先要启动Anaconda2，输入activate anaconda2, 然后cd到\vnpy-master\examples\VnTrader\ 下， python run.py




AutoStrategyRelease35 是 Python Version 3.5 包， 使用时修改文件名为AutoStrategy

AutoStrategyRelease36 是 Python Version 3.6 包， 使用时修改文件名为AutoStrategy
