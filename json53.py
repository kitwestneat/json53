import sys
import json
import boto.route53
import argparse
import pprint

INDENT_LEVEL = 2
API_REGION = 'us-east-1'

def get_records(zone):
	record_set = zone.get_records()
	records = {}
	for record in record_set:
		records["{name:s} {type:s} {identifier:s}".format(**record.__dict__)] = record.__dict__
	return records

def export_zone(zone):
	records = get_records(zone)

	with open(zone.name + "json", "w") as f:
		json.dump(records, f, indent=INDENT_LEVEL)

def export_zones():
	zones = conn.get_zones()
	for zone in zones:
		export_zone(zone)

def export_health_checks():
	health_checks = conn.get_list_health_checks()
	with open("health_checks.json", "w") as f:
		json.dump(health_checks.ListHealthChecksResponse.HealthChecks, f, indent=INDENT_LEVEL)

def import_zone(zone_name):
	def add_record_changes(action, records):
		for key in records:
			record = records[key]
			if record["type"] in ["NS", "SOA"]:
				continue

			# resource records have to be added separately
			change_records = record.pop("resource_records")
			record["action"] = action
			change = changes.add_change(**record)
			for value in change_records:
				change.add_value(value)

	with open(zone_name + "json", "r") as f:
		records = json.load(f)

	zone = conn.get_zone(zone_name)

	old_records = get_records(zone)
	delete_keys = set(old_records.keys()) - set(records.keys()) 

	changes = boto.route53.record.ResourceRecordSets(conn, zone.id)
	add_record_changes("DELETE", { key: old_records[key] for key in delete_keys })
	add_record_changes("UPSERT", records)

	#print(changes.to_xml())
	result = changes.commit()

	pprint.pprint(result)

conn = boto.route53.connect_to_region(API_REGION)
parser = argparse.ArgumentParser(description='Import and export route53 records as JSON')
parser.add_argument('zones', nargs='*', help='zone(s) to import or export')
parser.add_argument('--import', '-i', dest='mode', const='import', action='store_const', help='import the zone from JSON to route53')
parser.add_argument('--export', '-e', dest='mode', const='export', action='store_const', help='export the zone from route53 to JSON')
parser.add_argument('--checks', '-c', dest='health', action='store_true', help='export/import health checks')
args = parser.parse_args()
if not args.mode:
    parser.error("One of --import or --export must be given")

if args.health:
	if args.mode == "export":
		export_health_checks()
		sys.exit(0)
	if args.mode == "import":
		import_health_checks()
		sys.exit(0)
else:
	if args.mode == "import":
		if not args.zones:
			parser.error("Zone is required for import")
		for zone in args.zones:
			import_zone(zone)
		sys.exit(0)

	if args.mode == "export":
		if not args.zones:
			export_zones()
		else:
			for zone in args.zones:
				export_zone(conn.get_zone(zone))
		sys.exit(0)

"""
# export_zones()

test_zone = "test.com."
#export_zone(conn.get_zone(test_zone))
import_zone(test_zone)
"""
