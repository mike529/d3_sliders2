import csv
import json
import collections
import sys
import os
import shapefile
import scipy.sparse
import numpy
import gzip

csv.field_size_limit(sys.maxsize)

def RoundAndNormalize(stats):
	min_value = stats.total_neighbors / 2000.0
	new_total = 0.0
	for k, v in stats.neighbors.iteritems():
		if v > min_value:
			new_total += v
	return {k: v / new_total for k,v in stats.neighbors.iteritems() if v > min_value}

class NeighborhoodStats():
 	def __init__(self):
 		self.neighbors = {}
 		self.total_pings = 0
 		self.population = None
 		self.total_neighbors = 0.0

	def AddInteractions(self, neighbor, square_pings):
		self.neighbors[neighbor] = square_pings
		self.total_neighbors += square_pings



def GetCategory(naics_code):
	
	top_level_code = naics_code / 10000
	if top_level_code == 61:
		return "EDUCATION"
	elif top_level_code == 72:
		return "RESTAURANT"
	elif top_level_code == 62:
		return "HEALTH_CARE"
	elif naics_code / 1000 == 813:
		return "RELIGION"
	else:
		return "OTHER"



def ConvertRowKey(row_key):
	# return row_key[:5]
	return row_key[:-1]

def RowState(row):
	# if row['state'] not in ['ak', 'as', 'hi', 'gu', 'vi', 'pr', 'mp']:
	# 	return 'us'
	# else:
	# 	return 'not_real_us'
	return row['state']


def BuildSerialization(pings_for_state, visits_for_state, census_block_stats):
	id_to_neighborhood = []
	neighborhood_to_id = {}
	def GetId(neighborhood):
		if neighborhood not in neighborhood_to_id:
			new_id = len(neighborhood_to_id)
			neighborhood_to_id[neighborhood] = new_id
			id_to_neighborhood.append(neighborhood)
		return neighborhood_to_id[neighborhood]

	print("Loading {} neighborhoods".format(len(pings_for_state)))
	print("Loading {} neighborhood connections".format(len(visits_for_state)))
	
	for neighborhood in pings_for_state.keys():
		if neighborhood not in neighborhood_to_id:
			GetId(neighborhood)
	for (home_neighborhood, visit_neighborhood) in visits_for_state.keys():
		GetId(home_neighborhood)
		GetId(visit_neighborhood)

	total_pings = 0.0
	total_population = 0.0
	for neighborhood, count in pings_for_state.iteritems():
		population = census_block_stats[neighborhood]['population']
		total_pings += count
		total_population += population
	total_pings_per_pop = total_pings / total_population
	print("Average pings per person {}".format(total_pings_per_pop))

	print("Computing weighted totals")
	print("Matrix size #{}x{}".format(len(neighborhood_to_id), len(id_to_neighborhood)))
	data = []
	rows = []
	cols = []
	for (home_neighborhood, visit_neighborhood), count in visits_for_state.iteritems():
		data.append(count)
		rows.append(GetId(home_neighborhood))
		cols.append(GetId(visit_neighborhood))
	sparse_matrix = scipy.sparse.csr_matrix((data, (rows, cols)), shape=(len(neighborhood_to_id), len(neighborhood_to_id)))
	interconnect = sparse_matrix * sparse_matrix.transpose()


	print("Computed interconnect")
	coo_matrix = interconnect.tocoo()
	print("Converted matrix")

	neighborhood_stats = collections.defaultdict(NeighborhoodStats)

	print("Loading {} connections".format(len(coo_matrix.row)))
	for i in range(len(coo_matrix.row)):
		if i % 1000000 == 0:
			print("Loading connection {}".format(i))
		source = id_to_neighborhood[coo_matrix.row[i]]
		dest = id_to_neighborhood[coo_matrix.col[i]]
		neighborhood_stats[source].AddInteractions(dest, coo_matrix.data[i])


	print("Finalizing stats")
	for neighborhood, count in pings_for_state.iteritems():
		population = census_block_stats[neighborhood]['population']
		pings_per_pop = count / (population + 0.0)
		neighborhood_stats[neighborhood].total_pings = (pings_per_pop / total_pings_per_pop)
		neighborhood_stats[neighborhood].population = population


	return neighborhood_stats


def BuildPoiSerialization(pings_for_state, visits_for_state, census_block_stats):
	id_to_neighborhood = []
	neighborhood_to_id = {}
	def GetId(neighborhood):
		if neighborhood not in neighborhood_to_id:
			new_id = len(neighborhood_to_id)
			neighborhood_to_id[neighborhood] = new_id
			id_to_neighborhood.append(neighborhood)
		return neighborhood_to_id[neighborhood]

	poi_to_id = {}
	def GetPoiId(poi):
		if poi not in poi_to_id:
			new_id = len(poi_to_id)
			poi_to_id[poi] = new_id
		return poi_to_id[poi]

	print("Loading {} neighborhoods".format(len(pings_for_state)))
	print("Loading {} neighborhood connections".format(len(visits_for_state)))
	
	for neighborhood in pings_for_state.keys():
		if neighborhood not in neighborhood_to_id:
			GetId(neighborhood)
	for (home_neighborhood, visit_poi) in visits_for_state.keys():
		GetId(home_neighborhood)
		GetPoiId(visit_poi)

	print("Computing weighted totals")
	print("Matrix size #{}x{}".format(len(neighborhood_to_id), len(poi_to_id)))
	data = []
	rows = []
	cols = []
	for (home_neighborhood, visit_poi), count in visits_for_state.iteritems():
		data.append(count)
		rows.append(GetId(home_neighborhood))
		cols.append(GetPoiId(visit_poi))
	sparse_matrix = scipy.sparse.csr_matrix((data, (rows, cols)), shape=(len(neighborhood_to_id), len(poi_to_id)))
	interconnect = sparse_matrix * sparse_matrix.transpose()


	print("Computed interconnect")
	coo_matrix = interconnect.tocoo()
	print("Converted matrix")

	neighborhood_stats = collections.defaultdict(NeighborhoodStats)

	print("Loading {} connections".format(len(coo_matrix.row)))
	for i in range(len(coo_matrix.row)):
		if i % 1000000 == 0:
			print("Loading connection {}".format(i))
		source = id_to_neighborhood[coo_matrix.row[i]]
		dest = id_to_neighborhood[coo_matrix.col[i]]
		neighborhood_stats[source].AddInteractions(dest, coo_matrix.data[i])


	print("Finalizing stats")
	for neighborhood, count in pings_for_state.iteritems():
		population = census_block_stats[neighborhood]['population']
		pings_per_pop = count / (population + 0.0)
		neighborhood_stats[neighborhood].total_pings = pings_per_pop
		neighborhood_stats[neighborhood].population = population


	return neighborhood_stats	


def SerializeStats(neighborhood_stats, tract_to_points):
	pattern_to_index = {}
	patterns = []
	for category, category_stats in neighborhood_stats.iteritems():
		for key, stats in category_stats.iteritems():
			if key not in pattern_to_index:
				pattern_to_index[key] = len(patterns)
				patterns.append((key, stats.population))

	objects_by_cat = {}
	for category, category_stats in neighborhood_stats.iteritems():
		print("Serializing Category: {}".format(category))
		objects = []
		for i, (key, population) in enumerate(patterns):
			if key not in category_stats:
				if i % 100 == 0:
					print ("Serializing Row #{} Key:{}".format(i, key))

				normalized_object = {
					"k": key,
					"p": population,
					"t": 0,
					"n": {},
					"g": tract_to_points.get(key, [])
				}
			else:

				stats = category_stats[key]
				neighbors = {}
				found_total = 0
				for neighbor, count in stats.neighbors.iteritems():
					if (count / stats.total_neighbors) > .0005:
						found_total += round(count, 4)

				for neighbor, count in stats.neighbors.iteritems():
					if (count / stats.total_neighbors) > .0005:
						neighbors[pattern_to_index[neighbor]] = round(count / found_total, 4)
				if not neighbors:
					neighbors[pattern_to_index[key]] = 1.0
				normalized_object = {
					"k": key,
					"p": population,
					"t": round(stats.total_pings, 4),
					"n": neighbors,
					"g": tract_to_points.get(key, []),
				}
				if i % 100 == 0:
					print("Serializing Row #{} Key:{} Neighbors {}".format(i, key, len(neighbors)))

			objects.append(normalized_object)
		objects_by_cat[category] = objects
	return objects_by_cat


def LoadNeighborhoodPatterns(file_name, census_block_stats):
	pings_by_neighborhood = collections.defaultdict(lambda: collections.defaultdict(int))
	visits = collections.defaultdict(lambda: collections.defaultdict(int))

	def GetId(area):
		converted = ConvertRowKey(area)
		return converted

	def GetState(area):
		census_block_stat = census_block_stats.get(ConvertRowKey(area))
		if not census_block_stat:
			return None
		return census_block_stat['state']

	with open(file_name) as f:
		csv_dict_reader = csv.DictReader(f)
		for i, row in enumerate(csv_dict_reader):
			if i % 100 == 0:
				print("Loading row #{}: CBG Code: {}".format(i, row['area']))
	
			state = GetState(row['area'])
			ping_id = GetId(row['area'])
			stopped_count = int(row['raw_stop_counts'])
			for source_location, source_ping_count in json.loads(row['device_home_areas']).iteritems():
				source_state = GetState(source_location)
				source_id = GetId(source_location)

				pings_by_neighborhood[source_state][source_id] += (source_ping_count * stopped_count)
				if state == source_state:
					visits[source_state][(source_id, ping_id)] += source_ping_count


	return pings_by_neighborhood, visits

	# return cross_neighborhood_match

def MarkKey(state, visit_category, final_key, value, dictionary):
	current = dictionary
	if state not in current:
		current[state] = {}
	current = current[state]
	if visit_category not in current:
		current[visit_category] = {}
	current = current[visit_category]
	if final_key not in current:
		current[final_key] = 0
	current[final_key] += value

def MapPoiToCategory(file_names):
	poi_to_category = {}
	for file_name in file_names:
		print("Parsing file: {}".format(file_name))
		with gzip.open(file_name) as f:
			csv_dict_reader = csv.DictReader(f)
			for i, row in enumerate(csv_dict_reader):
				poi_to_category[row['safegraph_place_id']] = GetCategory(int(row['naics_code'] or 0))
	return poi_to_category

def LoadPoiPatterns(file_names, census_block_stats, poi_to_category):
	pings_by_neighborhood = {}
	visits = {}
	def GetId(area):
		converted = ConvertRowKey(area)
		return converted

	def GetState(area):
		census_block_stat = census_block_stats.get(ConvertRowKey(area))
		if not census_block_stat:
			return None
		return census_block_stat['state']


	total_count = 0
	for file_name in file_names:
		print("Parsing file: {}".format(file_name))
		with gzip.open(file_name) as f:
			csv_dict_reader = csv.DictReader(f)
			for i, row in enumerate(csv_dict_reader):
				total_count += 1
				if i % 100000 == 0:
					print("Loading row #{}: POI:{}".format(i, row['location_name']))
				poi_state = GetState(row['poi_cbg'])
				poi_id = total_count
				poi_type = poi_to_category.get(row['safegraph_place_id'], 'OTHER')
				median_dwell = float(row['median_dwell'])
				for source_location, source_ping_count in json.loads(row['visitor_home_cbgs']).iteritems():
					source_state = GetState(source_location)
					source_id = GetId(source_location)
					MarkKey(source_state, poi_type, source_id, (source_ping_count * median_dwell), pings_by_neighborhood)

					if poi_state == source_state:
						MarkKey(source_state, poi_type, (source_id, poi_id), source_ping_count, visits)
	return pings_by_neighborhood, visits


	

def GetCensusBlockStats(file_name):
	census_block_stats = {}
	with open(file_name) as f:
		csv_dict_reader = csv.DictReader(f)
		for i, row in enumerate(csv_dict_reader):
			converted = ConvertRowKey(row['census_block_group'])
			existing = census_block_stats.get(converted, {})
			existing_pop = existing.get('population', 0)

			census_block_stats[converted] = {'state': RowState(row), 'population': int(row['number_devices_residing']) + existing_pop}
	return census_block_stats	

def GetNormalizedPatterns(cross_match, census_block_stats):
	normalized_patterns = {}
	for source_location, dest_locations in cross_match.iteritems():
		location_stats = census_block_stats.get(source_location)
		if location_stats:
			population = location_stats['population']
			state = location_stats['state']
			normalized_dests = {}
			normalized_total = 0.0

			total_pings = float(sum(dest_locations.values()))

			for dest_location, ping_count in dest_locations.iteritems():
				normalized_dests[dest_location] = ping_count / total_pings
			normalized_patterns[source_location] = {'population': population, 'state': state, 'normalized_pings': normalized_dests, 'normalized_total': total_pings / float(population)}
	return normalized_patterns	

def RestrictToStates(normalized_patterns, restricted_states_names):
	restricted_states = {}
	for source_location, normalized_pattern in normalized_patterns.iteritems():
		if normalized_pattern['state'] not in restricted_states_names:
			continue

		restricted_neighbors = {}
		normalized_external = 0.0
		for dest_location, ping_fraction in normalized_pattern['normalized_pings'].iteritems():
			dest_state = normalized_patterns.get(dest_location, {}).get('state', 'Missing')
			if dest_state not in restricted_states_names:
				normalized_external += ping_fraction
			else:
				restricted_neighbors[dest_location] = ping_fraction
		
		restricted_states[source_location] =  {
			'population': normalized_pattern['population'], 
			'state': normalized_pattern['state'], 
			'normalized_pings': restricted_neighbors, 
			'normalized_external': normalized_external, 
			'normalized_total': normalized_pattern['normalized_total']  
		}

	return restricted_states



def RescalePatterns(normalized_patterns):
	scaled_total = 0.0
	pop = 0.0
	for normalized_pattern in normalized_patterns.values():
		scaled_total += normalized_pattern['population'] * normalized_pattern['normalized_total']
		pop += normalized_pattern['population']

	scaling_factor = scaled_total / pop
	rescaled_patterns = {}
	for source_location, normalized_pattern in normalized_patterns.iteritems():
		
		rescaled_neighbors = {}
		for dest_location, ping_fraction in normalized_pattern['normalized_pings'].iteritems():
			rescaled_neighbors[dest_location] = ping_fraction / scaling_factor

		
		rescaled_patterns[source_location] =  {
			'population': normalized_pattern['population'], 
			'state': normalized_pattern['state'], 
			'normalized_pings': normalized_pattern['normalized_pings'], 
			'normalized_external': normalized_pattern['normalized_external'], 
			'normalized_total': normalized_pattern['normalized_total'] / scaling_factor  
		}

	return rescaled_patterns


def SerializedPatterns(normalized_patterns, tract_to_points):
	pattern_to_index = {}
	for i, (key, normalized_pattern) in enumerate(normalized_patterns.iteritems()):
		pattern_to_index[key] = i

	objects = []

	for i, (key, normalized_pattern) in normalized_patterns.iteritems():
		if i % 10000 == 0:
			print("Serializing Row #{} Key: {}".format(i, key))
		neighbors = collections.defaultdict(float)

		found_total = round(normalized_pattern['normalized_external'], 3)
		for dest_location, ping_fraction in normalized_pattern['normalized_pings'].iteritems():
			if ping_fraction > .0005:
				found_total += round(ping_fraction, 3)

		for dest_location, ping_fraction in normalized_pattern['normalized_pings'].iteritems():
			index = pattern_to_index[dest_location]
			if ping_fraction <= .0005:
				continue
			rounded = round(ping_fraction / found_total, 3)
			if rounded > 0:
				neighbors[index] += rounded
			if index == pattern_to_index[key]:
				neighbors[index] += round(normalized_pattern['normalized_external'], 3)

		normalized_object = {
			"k": key,
			"p": normalized_pattern['population'],
			"t": normalized_pattern['normalized_total'],
			"n": neighbors,
			"g": tract_to_points.get(key, []),
		}
		objects.append(normalized_object)
	return objects

def DumpIntoDirectory(by_state_patterns, output_directory):
	for state, pattern in by_state_patterns.iteritems():
		output_file_name = os.path.join(output_directory, state + ".json")
		output_data = "{}_data = {}".format(state, json.dumps(pattern))
		with open(output_file_name, 'w') as g:
			g.write(output_data)

def BoundingBox(points):
	xs = [x for (x,y) in points]
	ys = [y for (x,y) in points]
	min_x = min(xs)
	max_x = max(xs)
	min_y = min(ys)
	max_y = max(ys)
	return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]

def LoadBoundaryData(shape_file):
	sf = shapefile.Reader(shape_file)
	shapeRecs = sf.shapeRecords()  
	tract_to_points = {}
	for shape_rec in shapeRecs:
		tract = shape_rec.record.as_dict()['GEOID']
		tract_to_points[tract] = BoundingBox(shape_rec.shape.points)
	return tract_to_points

def DumpSerialized(serialized):
	return json.dumps(serialized, separators=(',', ':'))

def SplitIntoSerializedStates(neighborhood_pattern_file_name, census_block_stats_file_name, boundary_data_file_name, output_directory):
	print("Loading Boundary Data")
	boundary_data = LoadBoundaryData(boundary_data_file_name)
	print("Joining Census Data")
	census_block_stats = GetCensusBlockStats(census_block_stats_file_name)

	print("Loading Neighborhoods")
	pings, visits = LoadNeighborhoodPatterns(neighborhood_pattern_file_name, census_block_stats)
	for state in pings.keys():
		if state == 'ca' or state is None:
			continue
		print("Loading state: {}".format(state))
		neighborhood_stats = BuildSerialization(pings[state], visits[state], census_block_stats)
		print("Serializing")
		serialized = SerializeStats(neighborhood_stats, boundary_data)
		print("Writing")
		output_file_name = os.path.join(output_directory, state + ".json")
		output_data = "{}_data = {}".format(state, DumpSerialized(serialized))
		with open(output_file_name, 'w') as g:
			g.write(output_data)


def SplitIntoSerializedPoiStates(poi_pattern_file_names, census_block_stats_file_name, poi_category_file_names, boundary_data_file_name, output_directory):
	print("Loading Boundary Data")
	boundary_data = LoadBoundaryData(boundary_data_file_name)
	print("Joining Census Data")
	census_block_stats = GetCensusBlockStats(census_block_stats_file_name)

	print("Loading Category Names")
	poi_category_map = MapPoiToCategory(poi_category_file_names)

	print("Loading Neighborhoods")
	pings, visits = LoadPoiPatterns(poi_pattern_file_names, census_block_stats, poi_category_map)
	for state in pings.keys():
		print("Loading state: {} ".format(state))
		if state == 'ca' or state is None:
			continue
		state_stats = {}
		for category in pings[state].keys():
			print("Loading Category: {}".format(category))
			state_stats[category] = BuildPoiSerialization(pings[state].get(category, {}), visits[state].get(category, {}), census_block_stats)
		print("Serializing")
		serialized = SerializeStats(state_stats, boundary_data)
		for category, category_serialized in serialized.iteritems():		
			output_file_name = os.path.join(output_directory, "{}_{}.json".format(state, category.lower()))
			output_data = "{}_{}_data = {}".format(state, category.lower(), DumpSerialized(category_serialized))
			print("Writing {} to {} with length {}".format(category, output_file_name, len(output_data)))

			with open(output_file_name, 'w') as g:
				g.write(output_data)





