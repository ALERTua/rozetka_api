#!/bin/bash
echo "start rozetka @ $(pwd)"
python -V
# python -c "from rozetka.runners.parse_api import main; main()"
python -m "rozetka.runners.parse_api"
echo "done rozetka"
# cron -f
# echo "rozetka cron done"