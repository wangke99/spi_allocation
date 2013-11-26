#!/bin/sh

./clean.sh
python model_connector.py -t dm_biz.ke_lss_assign_data
python run_allocation.py
python format_result.py
./result.sh
