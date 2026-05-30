#!/bin/bash


LOCKFILE="/var/locks/$PEERNAME.lock"
if [ -f "$LOCKFILE" ]; then
    echo "Пользователь $PEERNAME уже подключён. Отключение." >&2
    exit 1
else
    touch "$LOCKFILE"
fi