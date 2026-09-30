#!/bin/bash

for f in *.xib; do
  echo "Processing $f file..."
  ibtool --generate-strings-file $f.strings $f
done