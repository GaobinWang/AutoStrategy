SET CURRENT=%cd%
cd %CURRENT%

choco install anaconda3 --version 5.2.0.20180920  -y
choco install anaconda2 --version 5.0.0 --x86 -y 
choco install vcredist2013 --x86 -y
choco install git -y

echo all software install complete
echo 必须手动安装MongoDB

call clone.bat