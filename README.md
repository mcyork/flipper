
# DNS Record Flipper
## Author: Ian McCutcheon
## Year: 2023
## License: MIT

### Overview
This script provides functionality to check and manipulate DNS records through the NS1 API.
It allows users to "flip" DNS records between primary and secondary values, making it useful
for disaster recovery scenarios.

### Key Functions
- **check**: Retrieves and displays DNS records for a given FQDN.
- **flip**: Flips a specified DNS record to new values.
- **flip_app**: Flips multiple DNS records for a specified application based on a configuration file.

### Usage
- To check a record: `./flipper.py check <fqdn>`
- To flip a record: `./flipper.py flip <fqdn> <record_type> <zone> <new_values...>`
- To flip records for an application: `./flipper.py flip_app -file <filename> -app <name> -site <primary|secondary>`

### Configuration
- **API Key**: The NS1 API key must be provided in a separate config.py file.
- **Flip Definitions**: A text file with flip definitions can be used with the flip_app action.

### Note
Please refer to any accompanying documentation and sample_flip_config.txt for more details.

### CONFIG.PY
Should contain your NS1 API KEY in a single line like below
NSONE_API_KEY = 'YOUR_KEY_HERE'

### Dependencies
pip install -r requirements.txt

### License
This code is provided under the MIT License. See the accompanying LICENSE file for full details.

