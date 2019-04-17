""" test that the pxe_nodes.json and ansible template is valid JSON """

import json

with open('/var/www/provsion/nodes/pxe_nodes.json') as json_file:                 
   data = json.load(json_file)     
   # If we can't load it it's not valid according to the python json library
   # For example is a comma is missing somewhere python will giev a ValueError when loading it
