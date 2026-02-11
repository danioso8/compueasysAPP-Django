#!/bin/bash
# Script de monitoreo para CompuEasys

echo "==================================="
echo "  Estado del Servicio CompuEasys"
echo "==================================="
systemctl status compueasys --no-pager | head -15

echo -e "\n==================================="
echo "  Uso de Memoria"
echo "==================================="
free -h

echo -e "\n==================================="
echo "  Procesos Gunicorn"
echo "==================================="
ps aux | grep gunicorn | grep -v grep

echo -e "\n==================================="
echo "  Últimos 10 logs"
echo "==================================="
journalctl -u compueasys -n 10 --no-pager
