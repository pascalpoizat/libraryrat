#!/bin/sh
for f in `ls $1_*.json`
do
    ./doiFromDblpJson.sh $f >> $1.doi
done
echo `ls $1_*.json | wc -l` files treated
echo `cat $1.doi | wc -l` DOI found
