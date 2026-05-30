#!/bin/bash
# 1. Создаем таблицу маршрутизации для TPROXY
ip rule add fwmark 1 table 400
ip route add local default dev lo table 400
# 2. Перенаправляем весь TCP трафик от L2TP клиентов (192.168.42.0/24) в sing-box
iptables -t mangle -A PREROUTING -s 10.1.0.0/24 -p tcp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1
# 3. Перенаправляем весь UDP трафик от L2TP клиентов в sing-box
iptables -t mangle -A PREROUTING -s 10.1.0.0/24 -p udp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1
