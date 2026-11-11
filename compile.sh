#!/bin/sh

if [ "$#" -ne 4 ]; then
    echo "Use: ./compile.sh <image_path> <display_cols> <display_rows> <scrematic_name>"
    exit 1
fi

IMAGE_PATH="$1"
D_COLS="$2"
D_ROWS="$3"
SCH_NAME="$4"

python3 main.py "$IMAGE_PATH" "$D_COLS" "$D_ROWS" "$SCH_NAME"

if [ $? -ne 0 ]; then
    echo "error in python script"
    exit 1
fi

java -jar mindcode.jar cs "$SCH_NAME.mnd" -c

rm "$SCH_NAME.mnd"
rm "$SCH_NAME.log"

