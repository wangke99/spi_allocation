#!/bin/sh

cat final_output/*.* > output.txt
scp output.txt kewang-ld1.linkedin.biz:projects/lss_spi/assign_output/.
