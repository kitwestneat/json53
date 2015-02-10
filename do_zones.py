import argparse
import boto.route53
import json

API_REGION = 'us-east-1'
REGION_TTL = 600
SERVER_TTL = 300
INDENT_LEVEL = 2

parser = argparse.ArgumentParser(description='Modify route53 records based on server list')
parser.add_argument('zoneinfo', nargs='+', help='zoneinfo file(s) for zones to update')
parser.add_argument('--output', '-o', dest='output_file', action='store', help='output the new zone definition as JSON to given file')
parser.add_argument('--upload', '-u', dest='upload', action='store_true', help='upload the new zone definition to AWS')
args = parser.parse_args()
if not args.output_file and not upload:
	parser.error("One of --output or --upload must be given.")

# zoneinfo file has static records (like CNAME) and zone id info
zoneinfo_file = "test-zoneinfo.json"
with open(zoneinfo_file, "r") as f:
	zoneinfo = json.load(f)

zone_id = zoneinfo["zone"]["id"]
zone_name = zoneinfo["zone"]["name"]
record_list = zoneinfo["records"]

with open("health_checks.json", "r") as f:
	health_checks_json = json.load(f)
health_checks = dict((hc["HealthCheckConfig"]["IPAddress"], hc["Id"])
					for hc in health_checks_json)

def get_health_check(ip_address):
	return health_checks[ip_address]	

# load servers
with open("servers.json", "r") as f:
	server_list = json.load(f)

# build up records
for region_name in server_list:
	# build A record for region
	aws_region = server_list[region_name]["region"]
	identifier = region_name.upper() + " Region"
	alias_name = "www-" + region_name + "." + zone_name
	record_list[zone_name + " A " + identifier] = {
		"alias_hosted_zone_id": zone_id,
		"type": "A",
		"region": aws_region,
		"alias_evaluate_target_health": True,
		"resource_records": [],
		"ttl": REGION_TTL,
		"identifier": identifier,
		"alias_dns_name": alias_name,
		"name": zone_name,
	}

	# build A records for servers in region
	region_servers = server_list[region_name]["servers"]
	for server_name in region_servers:
		ip_address = region_servers[server_name]
		record_list[alias_name + " A " + server_name] = {
			"health_check": get_health_check(ip_address),
			"weight": "10",
			"type": "A", 
			"resource_records": [ip_address], 
			"ttl": SERVER_TTL,
			"identifier": server_name,
			"name": alias_name,
		}

if args.output_file != "":
	with open(args.output_file + ".json", "w") as f:
		json.dump({"zone": { "id": zone_id, "name": zone_name}, "records": record_list}, f, indent=INDENT_LEVEL)
elif args.upload:
	print "XXX do the upload!"
