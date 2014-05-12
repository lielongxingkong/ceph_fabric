#!/bin/bash
yum install -y python-pip python-devel
pip install fabric
pip install tentakel
cp ./tentakel.conf /etc/tentakel.conf

git config --global user.name "Zhao Zhenlong"
git config --global user.email zzl_1164@126.com
git config --global alias.st status
git config --global alias.br branch 
git config --global alias.dif diff 

yum install -y ntp
printf "server 127.127.1.0\nrestrict 192.168.0.0 mask 255.255.0.0 nomodify\nfudge 127.127.1.0 stratum 0 stratum" >> /etc/ntp.conf
service ntpd start 

