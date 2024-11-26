import argparse

import pandas as pd


def extract_header(result_path, header_name):
    """Extract specified header from the result file."""
    try:
        with open(result_path, 'r') as file:
            for line in file:
                # Look for the specified header
                if header_name in line:
                    # Extract and return the header value
                    return line.split(header_name)[1].strip()
    except FileNotFoundError:
        # If the file doesn't exist, return "Unknown"
        return "Unknown"


def process_full_result_to_tsv(input_file, output_file):
    # List to store processed data
    data = []

    # Read the file line by line
    with open(input_file, 'r') as file:
        for line in file:
            # Split line by spaces
            parts = line.strip().split()

            # Ensure the line has enough parts to avoid index errors
            if len(parts) >= 3:
                # Extract subdomain and status
                result_path = parts[0]
                subdomain = parts[1]
                status = " ".join(parts[2:]).lstrip("(").rstrip(")")
                # Determine the type based on subdomain
                type_value = "https" if subdomain.startswith(
                    "https") else "http"

                # Extract content type by reading the result_path, and grep `Content-Type`
                # Add the content type to data
                # Extract content type by reading the result_path file
                content_type = extract_header(result_path, 'Content-Type:')
                content_length = extract_header(result_path, 'Content-Length:')
                server = extract_header(result_path, 'Server:')
                location = extract_header(result_path, 'Location:')

                # Append to data list as a dictionary
                data.append({
                    "subdomain": subdomain,
                    "status": status,
                    "type": type_value,
                    "content_type": content_type,
                    "content_length": content_length,
                    "server": server,
                    "redirection_location": location
                })

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)

    # Remove duplicate subdomains, keeping the first occurrence
    df = df.drop_duplicates(subset="subdomain", keep="first")

    # Export the DataFrame to a TSV file
    df.to_csv(output_file, sep='\t', index=False, na_rep="NA")


def process_error_subdomain_list(source_index_file, all_hosts_file, source_error_file, full_error_subdomain_file_tsv):
    # Read all hosts into a list from all_hosts_file, each host separated by line
    with open(all_hosts_file, 'r') as file:
        # Adding '/' to each host
        all_hosts = [line.strip() for line in file if line.strip()]

    # Track subdomains from the input file to identify missing hosts
    input_subdomains = set()

    # Read the file line by line
    with open(source_index_file, 'r') as file:
        for line in file:
            parts = line.strip().split()

            if len(parts) >= 3:
                # Extract subdomain
                subdomain = parts[1]
                input_subdomains.add(subdomain.rstrip('/'))

    # Find hosts in all_hosts_file that are not in input_subdomains
    failed_hosts = [
        host for host in all_hosts if host.rstrip('/') not in input_subdomains]

    # Load errors from source_error_file into a dictionary
    error_dict = {}
    with open(source_error_file, 'r') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                subdomain = parts[0].rstrip('/')
                error_message = parts[1]

                # Determine error status based on the error message content
                if 'no such host' in error_message:
                    error_status = 'no such host'
                elif 'Client.Timeout' in error_message:  # can retry
                    error_status = 'client timeout'
                elif 'connection refused' in error_message:
                    error_status = 'connection refused'
                elif 'tls: handshake failure' in error_message:
                    error_status = 'tls handshake failure'
                elif 'connection reset by peer' in error_message:
                    error_status = 'connection reset by peer'
                elif 'EOF' in error_message:  # can retry
                    error_status = 'EOF'
                elif 'unrecognized name' in error_message:
                    error_status = 'unrecognized name'
                else:
                    error_status = 'unknown'

                error_dict[subdomain] = error_status

    # Process failed_hosts and create error_data with fallback for missing entries
    error_data = []
    for host in failed_hosts:
        subdomain = host.rstrip('/')
        # Use error status from error_dict if available; otherwise, set as "Unexpected error"
        error_status = error_dict.get(subdomain, 'Unexpected error')
        error_data.append(
            {'Subdomain': subdomain, 'Error Status': error_status})

    # Create DataFrame and output to TSV file
    error_df = pd.DataFrame(error_data)
    error_df.to_csv(full_error_subdomain_file_tsv, sep='\t', index=False)


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Process result files.")
    parser.add_argument("--source_dir", type=str, default="out",
                        help="Directory containing the result files (default: out)")

    args = parser.parse_args()

    # Define file paths
    source_dir = args.source_dir
    output_index = f"{source_dir}/index"
    output_error = f"{source_dir}/error"

    # Process the files
    process_full_result_to_tsv(output_index, 'subdomains_with_response.tsv')
    process_error_subdomain_list(
        output_index, 'hosts', output_error, 'subdomains_errors.tsv')
