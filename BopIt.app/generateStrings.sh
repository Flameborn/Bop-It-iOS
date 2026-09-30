#!/bin/bash

for f in *.xib; do
  echo "Processing $f file..."
  ibtool --generate-strings-file de.lproj/$f.strings de.lproj/$f
done