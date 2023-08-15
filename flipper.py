#!/usr/bin/env python3

"""
DNS Record Flipper
Author: Ian McCutcheon
Year: 2023
License: MIT

This script provides functionality to check and manipulate DNS records through the NS1 API.
It allows users to "flip" DNS records between primary and secondary values, making it useful
for disaster recovery scenarios.

Key Functions:
- check: Retrieves and displays DNS records for a given FQDN.
- flip: Flips a specified DNS record to new values.
- flip_app: Flips multiple DNS records for a specified application based on a configuration file.

Usage:
- To check a record: ./flipper.py check <fqdn>
- To flip a record: ./flipper.py flip <fqdn> <record_type> <zone> <new_values...>
- To flip records for an application: ./flipper.py flip_app -file <filename> -app <name> -site <primary|secondary>

Configuration:
- API Key: The NS1 API key must be provided in a separate config.py file.
- Flip Definitions: A text file with flip definitions can be used with the flip_app action.
    See sample_flip_config.txt for an example.
    The file must be in the following format:
        [app_name]
        fqdn: <fqdn> <record_type>
        primary: <value>
        secondary: <value>
        fqdn: <fqdn> <record_type>
        primary: <value>
        secondary: <value>
        ...
        [app_name]
        fqdn: <fqdn> <record_type>
        primary: <value>
        secondary: <value>
        fqdn: <fqdn> <record_type>
        primary: <value>
        secondary: <value>
        ...

License:
This code is provided under the MIT License. See the accompanying LICENSE file for full details.
"""

import argparse
from ns1 import NS1, Config
import sys
from collections import defaultdict
from config import NSONE_API_KEY

# Main section: Argument parsing and primary control flow of the script.
# This section reads the command-line arguments and invokes the appropriate action (e.g., check, flip, flip_app).
# It also provides the help text for the script.
def main():
    script_name = sys.argv[0] # Get the name of the script as it was invoked makes for nicer help outout

    parser = argparse.ArgumentParser(description="DNS record checker and flipper.")
    subparsers = parser.add_subparsers(dest="action", help="Choose an action to perform: 'check' or 'flip'.")

    # Subparser for the "check" action
    check_parser = subparsers.add_parser("check", help=f"Check DNS records. Usage: {script_name} check <fqdn>")
    check_parser.add_argument("fqdn", type=str, help="Fully qualified domain name to check.")

    # Subparser for the "flip" action
    flip_parser = subparsers.add_parser("flip", help=f"Flip DNS records. Usage: {script_name} flip <fqdn> <record_type> <zone> <new_values...>")
    flip_parser.add_argument("fqdn", type=str, help="Fully qualified domain name to flip.")
    flip_parser.add_argument("record_type", type=str, help="Record type (e.g., A, CNAME).")
    flip_parser.add_argument("zone", type=str, help="Zone name.")
    flip_parser.add_argument("new_values", nargs='+', type=str, help="New values for the record, separated by spaces.")
    # Subparser for the "flip app" action
    flip_app_parser = subparsers.add_parser(
        "flip_app",
        help=f"Flip DNS records for an application. Usage: {script_name} flip_app -file <filename> -app <name> -site <primary|secondary>",
        description="Flip DNS records for an application based on a configuration file. Use the -list option to list available application names without flipping."
    )
    flip_app_parser.add_argument("-file", type=str, help="Path to the input file containing the flip definitions.")
    flip_app_parser.add_argument("-app", type=str, help="Application name.") 
    flip_app_parser.add_argument("-site", type=str, choices=["primary", "secondary"], help="Site to flip to (either primary or secondary).") 
    flip_app_parser.add_argument("-list", action="store_true", help="List available application names.")

    args = parser.parse_args()

    # Check if the flip_app action is selected and no other argument is provided
    if args.action == "flip_app" and not args.file and not args.app and not args.site and not args.list:
        print("Please provide additional arguments for the flip_app action or use the -list option.")
        flip_app_parser.print_help()
        exit(1)

    # Check if no action has been selected, and print help if so
    if args.action is None:
        parser.print_help()
        return
    
    # Check if the flip action is selected. If so, call the flip_record function.
    if args.action == "flip":
        try:
            flip_record(args.fqdn, args.zone, args.record_type, args.new_values)
        except Exception as e:
            print(f"An error occurred while flipping the record for {args.fqdn}: {e}")
            return

    # Check if the check action is selected. If so, call the search_records function.
    if args.action == "check":
        records = search_records(args.fqdn)
        # print(f"JSON response: {records}\n")
        matching_records = [record for record in records if record[0] == args.fqdn]

        if not matching_records:
            print(f"No A or CNAME records found for {args.fqdn}\n")
        else:
            for domain, zone, record_type, record_values in matching_records:
                print(f"FQDN: {domain}")
                print(f"Zone: {zone}")
                print(f"Record Type: {record_type}")
                print(f"Record Values: {record_values}\n")
        return
    
    # Check if the flip_app action is selected. If so, call the parse_flip_config function.
    # If the -list option is provided, list the available application names.
    # Otherwise, perform flips for the specified application and site.
    if args.action == "flip_app":
    # Read and parse the input file
        flip_config_file = args.file
        flip_config = parse_flip_config(flip_config_file)

        # List available application names if the -list option is provided
        #if args.list:
            # If the -list option is provided, list the available application names or show the full config if -app is specified
        if args.list:
            if args.app:
                app_name = args.app
                app_config = flip_config.get(app_name, [])

                # Display the primary and secondary values for each FQDN in the specified application
                print(f"\nConfig for {app_name}:")
                for record in app_config:
                    fqdn, _ = record['fqdn']  # Extracting the domain name part of the tuple
                    print(f"FQDN: {fqdn}")
                    print(f"Primary: {record['primary']}")
                    print(f"Secondary: {record['secondary']}")

                    # Call the search_records function and print the matching records
                    records = search_records(fqdn)
                    if records is None:
                        print(f"An error occurred while searching the records for {fqdn}")
                        continue

                    matching_records = [r for r in records if r[0] == fqdn]

                    if not matching_records:
                        print(f"No A or CNAME records found for {record['fqdn']}\n")
                    else:
                        for domain, zone, record_type, record_values in matching_records:
                            print(f"-- FQDN: {domain}")
                            print(f"   Zone: {zone}")
                            print(f"   Record Type: {record_type}")
                            print(f"   Record Values: {record_values}\n")
                return
            else:
                # Existing logic to list available application names

                print("Available applications:")
                for app_name, records in flip_config.items():
                    print(f"  {app_name}")
                    for record in records:
                        fqdn, _ = record['fqdn']
                        print(f"    FQDN: {fqdn}")
                return


        # Check that -app and -site are provided unless -list is specified
        if args.app is None or args.site is None:
            print("Error: -app and -site are required unless -list is specified.")
            return

        # Perform flips for the specified application and site
        app_name = args.app
        site = args.site
        if app_name in flip_config:
            print(f"Flipping records for application: {app_name} (site: {site})")
            flips_summary = []
            for record in flip_config[app_name]:
                fqdn, record_type = record['fqdn']
                new_value = record[site]
                print(f"  Flipping {fqdn} {record_type} to {new_value}")

                # Search for the record to get the proper zone
                search_results = search_records(fqdn)
                matching_records = [r for r in search_results if r[0] == fqdn]

                if not matching_records:
                    flips_summary.append(f"{fqdn}: WARNING - No matching records found. Skipping flip.")
                    continue

                # Extract the zone from the first matching record (assuming only one exact match)
                _, zone, _, _ = matching_records[0]

                # Call the flip_record function with the extracted zone
                flip_record(fqdn, zone, record_type, new_value.split(','))

                #flip_record(fqdn, zone, record_type, [new_value])
                flips_summary.append(f"{fqdn} {record_type} -> {new_value}")

            print("\nFlip operation summary:")
            for summary_line in flips_summary:
                print(f"  {summary_line}")
            print("\nFlip operation completed successfully.")
        else:
            print(f"\nApplication '{app_name}' not found in the configuration file.")

# Function to search for records based on a given FQDN
# search_records (if applicable): Function to search for DNS records based on the FQDN.
# It connects to the NS1 API and retrieves matching records.
def search_records(fqdn):
    try:
        config = Config()
        config.createFromAPIKey(NSONE_API_KEY)
        api = NS1(config=config)

        # Use the searchZone method to retrieve the records for the given FQDN
        results = api.searchZone(fqdn)

        # Iterate through the results, extracting the relevant information
        records = []
        for result in results:
            record_type = result.get('type')
            if record_type in ['A', 'CNAME']:
                domain = result.get('domain')
                zone = result.get('zone')
                if domain == fqdn or domain.endswith(f'.{fqdn}'):
                    record_values = [answer['answer'][0] for answer in result.get('answers', [])]
                    records.append((domain, zone, record_type, record_values))

        return records
    except Exception as e:
        print(f"An error occurred while searching the records for {fqdn}: {e}")
        if 'result' in locals():
            print(f"Raw JSON response: {results}")
        return None

# Function to flip a record to new values
# flip_record: Function to flip a DNS record based on the provided parameters.
# It connects to the NS1 API, retrieves the existing record, and replaces it with the new values.
def flip_record(fqdn, zone, record_type, new_values, action="replace"):
    config = Config()
    config.createFromAPIKey(NSONE_API_KEY)
    api = NS1(config=config)

    # Load the existing record based on the FQDN, record type, and zone
    record = api.loadRecord(fqdn, record_type, zone)

    # Perform the flip action based on the specified action
    # replace: Replace the existing answers with the new values
    #          this is the only action currently supported
    if action == "replace":
        # Create a structure for the new answers based on the provided new_values
        new_answers = [{"answer": [value]} for value in new_values]

        # Use the update method to replace the answers
        record.update(answers=new_answers)

# Function to parse the flip configuration file
def parse_flip_config(file_path):
    # Dictionary to hold the parsed data
    flip_config = defaultdict(list)

    # Variables to keep track of the current application and record
    current_application = None
    current_record = {}

    # Read the file line by line
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            
            # Skip empty lines and lines starting with '#'
            if not line or line.startswith('#'):
                continue

            # Identify applications (lines starting with '[')
            if line.startswith('[') and line.endswith(']'):
                current_application = line[1:-1]
                continue

            # Parse FQDN and record type
            if line.startswith('fqdn:'):
                fqdn, record_type = line[5:].split()
                current_record['fqdn'] = (fqdn, record_type)
                continue

            # Parse primary and secondary values
            key, value = line.split(': ')
            current_record[key] = value

            # If the secondary value is parsed, add the record to the application and reset current_record
            if 'secondary' in current_record:
                flip_config[current_application].append(current_record)
                current_record = {}

    return flip_config

if __name__ == "__main__":
    main()

