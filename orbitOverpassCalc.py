#orbitOverpassCalc.py sjpestana
import math, datetime, urllib3, re, sys, json
import ephem as e

#set desired lat and lon focus point
print('Enter lat (N+) and lon (E+) for center point of interest.\nLeave blank for default location.')
c_lat_in = raw_input('\t\tCenter point latitude: ')
c_lon_in = raw_input('\t\tCenter point longitude: ')
if c_lat_in == '' or c_lon_in == '':
	#if user didn't give an input, default to 47.62, -122.35
	c_lat = 47.62
	c_lon = -122.35
	print('No center point location given, defaulting to 0, 0.')
elif (-90 <= float(c_lat_in) <= 90) and (-180 <= float(c_lon_in) <= 180):
	#if user gives good input within correct lat and lon ranges
	c_lat = float(c_lat_in)
	c_lon = float(c_lon_in)
else:
	#abort if bad values input
	print('longitude (-90 to 90) or latitude (-180 to 180) out of range')
	sys.exit()

	
print('\n')
	
#ask user for desired number of days to query (TLE out of date > 30 days out)
print('Enter the number of days from now to search (max: 30 days).\nLeave blank for default of 30 days.')
n_days = raw_input('\t\tNumber of days: ')
if n_days > 30 or n_days < 1:
	print('Number of days input was blank or out of range (1-30), defaulting to 30 days')
	n_days = 30

#ask for the 

print('\n\n\tORBIT OVERPASS CALCULATOR')
print('================================================')
print('   Point of interest: lat: %s, lon: %s' % (c_lat,c_lon))
print('   Days from now to search: %s' % n_days)
print('================================================\n')


with open('TLEs.json') as data_file:    
    data = json.load(data_file)


sat_name = str(data['satellite']['name'])
tle0 = str(sat_name)
tle1 = str(data['satellite']['TLE']['line_1'])
tle2 = str(data['satellite']['TLE']['line_2'])
print("\nLoaded TLE for %s:" % sat_name)
print("%s\n%s\n" % (tle1,tle2))


sat = e.readtle(tle0,tle1,tle2)


#get current satellite location
#compute for current UTC time
sat.compute(datetime.datetime.utcnow())
#print current sub-latitude and sub-longitude point
#convert lat from deg:min:sec to decimal degrees
lat_split = str(sat.sublat).split(":")
lat_deg = float(lat_split[0])
lat_min = float(lat_split[1])
lat_sec = float(lat_split[2])
lat_float = lat_deg + (lat_min/60) + (lat_sec/3600)
#convert lon from deg:min:sec to decimal degrees
lon_split = str(sat.sublong).split(":")
lon_deg = float(lon_split[0])
lon_min = float(lon_split[1])
lon_sec = float(lon_split[2])
lon_float = lon_deg + (lon_min/60) + (lon_sec/3600)
#print lat and lon
current_location = '|  Current %s Location:  %s,  %s  |' % (sat_name, round(lat_float,4), round(lon_float,4))
border = '='
for x in range(0,len(current_location)-1):
	border = '=' + border
print(border)
print(current_location)
print(border)







#set previous month, day, hour all to zero
prev_mon = 0
prev_day = 0
prev_hr = 0
table_headers = '  OVERPASS DATE TIME          LAT          LON         SWATH WIDTH(km)'
border = '-'
for x in range(0,len(table_headers)-1):
	border = '-' + border
print(border)
print(table_headers)

for i in range(0,(n_days*24*60*60)): #number of seconds in n_days
	#compute for every minute for the next n_days from right now
	fordate = datetime.datetime.utcnow()+datetime.timedelta(seconds=i)
	sat.compute(fordate)
	
	#calculate actual swath width based on sat orbit height
	swath_w = (sat.elevation/1000)*(math.tan(math.radians(25.5)))*2
	
	#ECOSTRESS swath width ~384 km (ISS altitude 400 +/- 25 km)
	#ECOSTRESS FOV 51deg
	#from ground, ISS/ECOSTRESS will be imaging your location if ISS is >65deg above horizon, <25 off zenith
	#also see:https://hyspiri.jpl.nasa.gov/downloads/2014_Workshop/day2/3_ECOSTRESS_Coverage.pdf
	#use the swath_width at this point to calculate the area seen by ECOSTRESS
	#using WGS84 spheroid, convert swath width (km) to deg at specified latitude (c_lat)
	#https://en.wikipedia.org/wiki/Geographic_coordinate_system
	km_per_degLat = (111132.954 - 559.822 * math.cos(2*c_lat) + 1.175 * math.cos(4*c_lat))/1000
	km_per_degLon = (111132.954 * math.cos(c_lat))/1000
	#r = one half of the swath width ("radius") in decimal degrees
	r_lat = (swath_w/km_per_degLat)/2
	r_lon = (swath_w/km_per_degLon)/2
	#approximately this box
	min_lat = c_lat - r_lat
	max_lat = c_lat + r_lat
	min_lon = c_lon + r_lon
	max_lon = c_lon - r_lon
	
	#get the sub lat and lon point in decimal degrees 
	#convert lat from deg:min:sec to decimal degrees
	lat_split = str(sat.sublat).split(":")
	lat_deg = float(lat_split[0])
	lat_min = float(lat_split[1])
	lat_sec = float(lat_split[2])
	lat_float = lat_deg + (lat_min/60) + (lat_sec/3600)
	#convert lon from deg:min:sec to decimal degrees
	lon_split = str(sat.sublong).split(":")
	lon_deg = float(lon_split[0])
	lon_min = float(lon_split[1])
	lon_sec = float(lon_split[2])
	lon_float = lon_deg + (lon_min/60) + (lon_sec/3600)
	
	#print(round(min_lat,2),round(max_lat,2),round(min_lon,2),round(max_lon,2),swath_w)
	
	#check to see if the sat will overfly anywhere within the area described above
	if math.floor(min_lat) < int(lat_float) < math.ceil(max_lat):
		if math.floor(min_lon) < int(lon_float) < math.ceil(max_lon):
	##if 8.7 < int(lat_float) < 12.3:
		##if -87.8 < int(lon_float) < -83.2:
			#then sat is covering this area
			#get only unique sat overpasses
			curr_mon = int(fordate.month)
			curr_day = int(fordate.day)
			curr_hr = int(fordate.hour)
			if curr_mon == prev_mon and curr_day == prev_day and curr_hr == prev_hr:
				pass
			else:
				print('%s\t %s\t %s\t %s \n' % (fordate, lat_float, lon_float, swath_w))
				#set the current month,day,hour to previous before moving on
				prev_mon = curr_mon
				prev_day = curr_day
				prev_hr = curr_hr


