#!/bin/bash

# Accept the first parameter as `subdomain` and the second as `output-directory` (default to /out)
subdomain="$1"
output_directory="${2:-./out}"

# Check if subdomain is provided
if [[ -z "$subdomain" ]]; then
    echo "Error: Please provide a subdomain as the first parameter."
    exit 1
fi

# Ensure the subdomain has https:// or http:// at the beginning
if [[ "$subdomain" != http://* && "$subdomain" != https://* ]]; then
    echo "Error: The subdomain must start with http:// or https://."
    exit 1
fi

# Perform grep to search for the subdomain in the specified output directory's index file
grep_result=$(grep "$subdomain" "$output_directory/index" | head -n 1)

# Check if grep found a result
if [[ -z "$grep_result" ]]; then
    echo "Error: Subdomain '$subdomain' not found in $output_directory/index."
    exit 1
fi

# Split by empty space and get the first element (the result path)
result_path=$(echo "$grep_result" | awk '{print $1}')

# Read and show the content of the result path
if [[ -f "$result_path" ]]; then
    cat "$result_path"
else
    echo "Error: Result path '$result_path' not found or is not a file."
    exit 1
fi
