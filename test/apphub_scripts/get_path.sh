#!/bin/bash

full_path=$(realpath $0)
dir_path=$(dirname $full_path)

apphub_path=${dir_path/'test/apphub_scripts'/'apphub'}
echo $apphub_path
#apphub_path=${dir_path/t/a}
#echo $apphub_path
