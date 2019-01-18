@setlocal enableextensions
@cd /d "%~dp0"

SET CURRENT=%cd%

call refreshenv
c:
cd c:\
git clone "https://github.com/vnpy/vnpy.git"
cd %CURRENT%
call vnpy.bat

call refreshenv
c:
cd c:\
git clone "https://github.com/mao-zhou/AutoStrategy"
call C:\tools\Anaconda3\Scripts\activate.bat
cd %CURRENT%
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install TA_Lib-0.4.17-cp35-cp35m-win_amd64.whl
pip install TA_Lib-0.4.17-cp36-cp36m-win_amd64.whl
pip install statsmodels-0.8.0-cp35-cp35m-win_amd64.whl
pip install statsmodels-0.8.0-cp36-cp36m-win_amd64.whl
python pyop.py
python MongoDownloader.py
pip install statsmodels-0.8.0-cp35-cp35m-win_amd64.whl
pip install statsmodels-0.8.0-cp36-cp36m-win_amd64.whl
start /wait msiexec.exe /i "c:\tools\mongodb-win32-x86_64-2008plus-ssl-4.0.4-signed.msi" /QN /L*V "C:\tools\msilog.log"