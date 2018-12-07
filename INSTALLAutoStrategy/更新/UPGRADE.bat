SET CURRENT=%cd%
call refreshenv
cd c:\
rmdir /s/q AutoStrategy
git clone "https://github.com/mao-zhou/AutoStrategy"
call C:\tools\Anaconda3\Scripts\activate.bat
cd %CURRENT%
rmdir /s/q C:\\tools\\Anaconda3\\Lib\\site-packages\\AutoStrategy
python pyop.py