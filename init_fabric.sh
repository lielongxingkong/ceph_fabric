#!/bin/bash
yum install -y python-pip python-devel
pip install fabric
pip install tentakel
cp ./tentakel.conf /etc/tentakel.conf
