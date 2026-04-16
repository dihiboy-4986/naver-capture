#!/bin/bash
mkdir -p /usr/local/share/fonts/nanum
cp NanumGothic.ttf /usr/local/share/fonts/nanum/
fc-cache -fv
playwright install chromium