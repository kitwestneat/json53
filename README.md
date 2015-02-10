# json53
Export and import route53 records via JSON 

Requires the boto library be installed: 
http://boto.readthedocs.org/en/latest/getting_started.html

Credentials are stored in ~/.boto:
[Credentials]
aws_access_key_id = YOURACCESSKEY
aws_secret_access_key = YOURSECRETKEY

Syntax for json53 is:
json53 {--import|--export} [--checks] [zones]

Import or export zones and or checks. Defaults to exporting all zones. Importing requires a specific zone. Can also export/import health checks with the --checks flag.


