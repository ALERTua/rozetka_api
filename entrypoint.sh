#!/bin/bash
echo "start rozetka @ $(pwd)"
python -c "from rozetka.runners.parse_api import main; main()"
echo "done rozetka"
# cron -f
# echo "rozetka cron done"