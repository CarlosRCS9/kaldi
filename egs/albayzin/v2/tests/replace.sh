#!/bin/bash

if [ $# -lt 1 ]; then
  echo "Usage: $0 <replacements> <path-to-dir> <--reverse>"
  exit 1
fi

replacements=$1
data_dir=$2
reverse=$([ ${3:-false} = true ] && echo true || echo false)

while IFS= read -r line; do
  if [ reverset = false ]; then
    target=$(echo $line | cut -d" "  -f1)
    replacement=$(echo $line | cut -d" " -f2)
  else
    target=$(echo $line | cut -d" "  -f2)
    replacement=$(echo $line | cut -d" " -f1)
  fi
  #find $data_dir -type f -exec sed -i.bak "s/$target/$replacement/g" {} \;
  find $data_dir -type f -print0 | xargs -0 sed -i "s/$target/$replacement/g"
done < $replacements

