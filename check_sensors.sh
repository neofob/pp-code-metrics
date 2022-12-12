#!/usr/bin/env bash
date
##########
echo ""
echo "Garden:"
wget -O - "http://192.168.42.181:8001/KEY&Stats/json" 2> /dev/null | jq -C '.Stats'
#wget -O - "http://192.168.42.181:8001/KEY&Stats/json" 2> /dev/null | jq -C

##########
echo ""
echo "Soil:"
wget -O - "http://192.168.42.181:8004/KEY&Stats/json" 2> /dev/null | jq -C '.Stats'  
#wget -O - "http://192.168.42.181:8004/KEY&Stats/json" 2> /dev/null | jq -C

##########
echo ""
echo "Soil1:"
wget -O - "http://192.168.42.181:8005/KEY&Stats/json" 2> /dev/null | jq -C '.Stats'  
#wget -O - "http://192.168.42.181:8005/KEY&Stats/json" 2> /dev/null | jq -C
