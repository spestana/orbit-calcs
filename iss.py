#iss.py sjpestana
import math, datetime, urllib3, re, sys
import ephem as e

#set desired lat and lon focus point
#EARTH La Flor Campus in Guanacaste Coasta Rica
print('Enter lat (N+) and lon (E+) for center point of interest.\nLeave blank for default location.')
c_lat_in = raw_input('\t\tCenter point latitude: ')
c_lon_in = raw_input('\t\tCenter point longitude: ')
if c_lat_in == '' or c_lon_in == '':
	#if user didn't give an input, default to Guanacaste, Coasta Rica
	c_lat = 10.5
	c_lon = -85.5
	print('No center point location given, defaulting to Guanacaste Coasta Rica.')
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


print('\n\n\t\tECOSTRESS OVERPASS CALCULATOR')
print('================================================')
print('   Point of interest: lat: %s, lon: %s' % (c_lat,c_lon))
print('   Days from now to search: %s' % n_days)
print('================================================\n')


#Two Line Element of ISS
http = urllib3.PoolManager()
#get from Celestrak https://www.celestrak.com/NORAD/elements/stations.txt
TLEurl = 'http://www.celestrak.com/NORAD/elements/stations.txt'
stationsTLE = http.request('GET',TLEurl)
data = stationsTLE.data
stationsTLE_split = data.split('\r\n')
not_found_count = 0
#find the ISS by looking for the string "1 25544U"
#which is  satellite catalog number = 25544, U = unclassified
#other spacecraft can be used by replacing the cat_num (likely need to change TLE source url too then)
cat_num = "25544U" #including "U" for classification (unclassified)
srch = "1 " + cat_num #add line #1 to search
for n in range(0,(len(stationsTLE_split)-1)):
	if re.search(srch,stationsTLE_split[n]):
		tle0 = stationsTLE_split[n-1]
		tle1 = stationsTLE_split[n]
		tle2 = stationsTLE_split[n+1]
		print("\nFound most recent ISS TLE from CelesTrak:")
		print("%s\n%s\n%s\n" % (tle0,tle1,tle2))
	else:
		not_found_count += 1

#if we iterated through the entire list of TLEs and didn't find the ISS
if not_found_count == len(stationsTLE_split):
	print("\nNo TLE for ISS found from CelesTrak")
	print("\nCheck CelesTrak source url\n")
iss = e.readtle(tle0,tle1,tle2)





#get current ISS location
#compute for current UTC time
iss.compute(datetime.datetime.utcnow())
#print current sub-latitude and sub-longitude point
#convert lat from deg:min:sec to decimal degrees
lat_split = str(iss.sublat).split(":")
lat_deg = float(lat_split[0])
lat_min = float(lat_split[1])
lat_sec = float(lat_split[2])
lat_float = lat_deg + (lat_min/60) + (lat_sec/3600)
#convert lon from deg:min:sec to decimal degrees
lon_split = str(iss.sublong).split(":")
lon_deg = float(lon_split[0])
lon_min = float(lon_split[1])
lon_sec = float(lon_split[2])
lon_float = lon_deg + (lon_min/60) + (lon_sec/3600)
#print lat and lon
print('================================================')
print('|  Current ISS Location:  %s,  %s  |' % (round(lat_float,4), round(lon_float,4)))
print('================================================\n\n')
print('-------------------------------------------------------------------------------')






#set previous month, day, hour all to zero
prev_mon = 0
prev_day = 0
prev_hr = 0
print('  OVERPASS DATE TIME\t\t  LAT\t\t  LON\t\t SWATH WIDTH(km)')

for i in range(0,(n_days*24*60*60)): #number of seconds in n_days
	#compute for every minute for the next n_days from right now
	fordate = datetime.datetime.utcnow()+datetime.timedelta(seconds=i)
	iss.compute(fordate)
	#calculate actual swath width based on ISS orbit height
	swath_w = (iss.elevation/1000)*(math.tan(math.radians(25.5)))*2
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
	lat_split = str(iss.sublat).split(":")
	lat_deg = float(lat_split[0])
	lat_min = float(lat_split[1])
	lat_sec = float(lat_split[2])
	lat_float = lat_deg + (lat_min/60) + (lat_sec/3600)
	#convert lon from deg:min:sec to decimal degrees
	lon_split = str(iss.sublong).split(":")
	lon_deg = float(lon_split[0])
	lon_min = float(lon_split[1])
	lon_sec = float(lon_split[2])
	lon_float = lon_deg + (lon_min/60) + (lon_sec/3600)
	#print(round(min_lat,2),round(max_lat,2),round(min_lon,2),round(max_lon,2),swath_w)
	#check to see if the ISS will overfly anywhere within the area described above
	if math.floor(min_lat) < int(lat_float) < math.ceil(max_lat):
		if math.floor(min_lon) < int(lon_float) < math.ceil(max_lon):
	##if 8.7 < int(lat_float) < 12.3:
		##if -87.8 < int(lon_float) < -83.2:
			#then ISS is covering this area
			#get only unique ISS overpasses
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

