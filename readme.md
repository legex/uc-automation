# DID Migration Script

## Overview: 
Repository contains automation scripts for CUCM line change which will be useful during DID migration from external to internal.

## Components:

### Two main components (backend engin):
- axlconn.py : Instantiates the connection between localhost and target(cucm)
- axlop.py : Performs operations on device line.


### Supporting components:
- dict_helper.py : Cleans serialized zeep object retrieved from response of getxxxx() calls and converts them to native python dictionaries, and also helps clean unwanted keys from dictionary which cause errors which updating lines.
- logger.py : creates a logging pipeline to report events for each function calls and respection exceptions
- debugplugin.py : to be used if there is issue observed with zeep libraries, native from cisco repository.

### Requirements:
- install requirements.txt
- create .env file which would contain:
    1. Username for CUCM
    2. Password
    3. URL of CUCM
- Sample of .env:
    - CUCM_ADDRESS="cucm-addresss"
    - AXL_USERNAME="username"
    - AXL_PASSWORD="password"

### API interface:
- main.py : bridges user interaction with the script and performs the required changes.
    Scope of improvement:
     1. Implementing file handling
     2. Looping over users (n) extracted from files and change DID


## Workflow:
- Input user details along with target line number
- axlop.py will fetch user phone and its current lines,
- if current lines have 555 at the begining, it will move to next line where it doesn't start with 555
- validate if target line number is there already in CUCM or not
- if not in cucm then create line with basic config (routepartition)
- update line fetches rest of the line configuration and replaces the current line with target line with all current configuration for the user
- reports success
