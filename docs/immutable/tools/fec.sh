#!/usr/bin/env sh

set -x
set -eo pipefail

size=640x120
size=1920x1200

convert $1 $1.rgb
zfec -k $2 -m $3 $1.rgb
rm $1.rgb
for i in *.fec; do
    mv $i $i.rgb
    convert -size $size $i.rgb $i.png
    rm $i.rgb
done
