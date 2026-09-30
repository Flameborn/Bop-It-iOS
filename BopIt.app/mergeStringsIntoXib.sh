#!/bin/bash

for f in *.xib; do
  echo "Processing $f file..."
  ibtool --strings-file es.lproj/$f.strings --write es.lproj/$f English.lproj/$f
done