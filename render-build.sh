#!/bin/bash
apt-get update
apt-get install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra
fc-cache -fv
playwright install chromium