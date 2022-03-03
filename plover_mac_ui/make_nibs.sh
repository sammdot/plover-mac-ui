#!/usr/bin/env bash -e

mkdir -p $(dirname $0)/Resources
rm -f $(dirname $0)/Resources/*.nib
for xib in `ls $(dirname $0)/*.xib`
do
  echo -n $(basename $xib)" "
  ibtool $xib --compile $(dirname $0)/Resources/$(basename $xib .xib).nib
  echo "-> "$(basename $xib .xib).nib
done
