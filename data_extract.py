#Import modules
from pymongo import MongoClient
import matplotlib.pyplot as plt
import heatmap_drawing as hd


def client(username: str, password: str, host: str):
    return MongoClient(f"mongodb://{username}:{password}@{host}:27017/")

def ssid_overview(client: MongoClient, filter_str: str, filtertype : int):

    db = client["scandata"]
    bssid_pool, ssid_pool = db["bssid_pool"], db["ssid_pool"]

    ssid_bssid = {}

    for ssid in ssid_pool.find():
        if (filter_str in ssid['name'] and filtertype == 0) or filtertype == 1:
            ssid_bssid[ssid['name']] = []
            ssid_id = ssid['_id']
            for bssid in bssid_pool.find({'ssid': ssid_id}):
                if (filter_str in bssid['name'] and filtertype == 1) or filtertype == 0:
                    ssid_bssid[ssid['name']].append(bssid['name'])
    
    keys = [k for k, v in ssid_bssid.items() if v == []]

    for key in keys:
        del ssid_bssid[key]

    return ssid_bssid

def bssid_graph(client: MongoClient, bssid: str):

    db = client["scandata"]
    data_frames, ap_data_frames, bssid_pool = db["data_frames"], db["ap_data_frames"], db["bssid_pool"]

    bssid_id = bssid_pool.find_one({"name": bssid})["_id"]

    ap_data_frames_ids = []

    for ap_data_frame in ap_data_frames.find({'bssid': bssid_id}):
        ap_data_frames_ids.append(ap_data_frame["_id"])
    
    datapoints = []

    for ap_data_frames_id in ap_data_frames_ids:
        y = ap_data_frames.find_one({"_id": ap_data_frames_id})['rssi']
        x = data_frames.find_one({"ap_data_frames": ap_data_frames_id})['time']
        datapoints.append((x,y))
    
    datapoints.sort(key = lambda p: p[0])

    start_x = datapoints[0][0]
    for i in range(len(datapoints)):
        datapoints[i] = (datapoints[i][0]-start_x,datapoints[i][1])

    x,y = zip(*datapoints)

    plt.plot(x,y)

    plt.show()


def rssi_location(client: MongoClient, bssid: str):

    db = client["scandata"]
    data_frames, ap_data_frames, bssid_pool = db["data_frames"], db["ap_data_frames"], db["bssid_pool"]
    bssid_id = bssid_pool.find_one({"name": bssid})["_id"]

    ap_data_frames_ids = []

    for ap_data_frames_id in ap_data_frames.find({"bssid": bssid_id}):
        ap_data_frames_ids.append(ap_data_frames_id["_id"])

    datapoints = {"rssi": [],"location": []}

    for ap_data_frames_id in ap_data_frames_ids:
        datapoints["rssi"].append(ap_data_frames.find_one({"_id": ap_data_frames_id})["rssi"])
        datapoints["location"].append(data_frames.find_one({"ap_data_frames": ap_data_frames_id})["location"])
    

    return datapoints



def accesspoint_est(rssi_list: list, locations_list: list):

    signal_strengths = []
    for rssi in rssi_list:
        signal_strengths.append(100+rssi)
    
    sr_list = []

    for signal_strength in signal_strengths:
        sr_list.append(signal_strength/sum(signal_strengths))

    longitude = 0
    latitude = 0

    for i in range(len(locations_list)):
        longitude += locations_list[i][0]*sr_list[i]
        latitude += locations_list[i][1]*sr_list[i]
    

    return round(longitude,6), round(latitude,6)

def convert_location(ap_location: tuple, scan_locations: list, isize: int, buffer: int) -> tuple[tuple, list[tuple]]:

    size = isize-buffer*2

    min_longitude = min(min(scan_locations, key = lambda x: x[1])[1], ap_location[1])
    max_longitude = max(max(scan_locations, key = lambda x: x[1])[1], ap_location[1])

    min_latitude = max(max(scan_locations, key = lambda x: x[0])[0], ap_location[0])
    max_latitude = min(min(scan_locations, key = lambda x: x[0])[0], ap_location[0])
    
    aspect_ratio = abs((max_longitude-min_longitude)/(max_latitude-min_latitude))

    if aspect_ratio > 1:
        x_axis = size 
        y_axis = size * aspect_ratio**(-1)
    else:
        y_axis = size
        x_axis = size * aspect_ratio

    ap_grid_location = (
        int(
            abs(
                (ap_location[1] - min_longitude)/(max_longitude-min_longitude)
            )*x_axis + buffer
        ),
        int(
            abs(
                (ap_location[0] - min_latitude)/(max_latitude-min_latitude)
            )*y_axis + buffer
        )
    )
    scan_grid_locations = []

    for location in scan_locations:
        scan_grid_locations.append((
        int(
            abs(
                (location[1] - min_longitude)/(max_longitude-min_longitude)
            )*x_axis + buffer
        ),
        int(
            abs(
                (location[0] - min_latitude)/(max_latitude-min_latitude)
            )*y_axis + buffer
        )
    ))
    
    return ap_grid_location, scan_grid_locations

def generate_heatmap(ap_location, scan_locations, size, buffer):
    ap_grid_location, scan_grid_locations = convert_location(ap_location, scan_locations['location'], size, buffer)

    ap = {
        'coords': ap_grid_location,
        'label': f'Access Point {ap_location}'
    }

    scans = []

    for i, scan_loc in enumerate(scan_grid_locations):
        scans.append(
            {
                'coords': scan_loc,
                'rssi': scan_locations['rssi'][i],
                'label': f'{scan_locations["location"][i]}'
            }
        )

    im = hd.make_image(size,size)
    hd.draw_heat_circles(im,ap,scans)
    hd.draw_accesspoint(im,ap)
    hd.draw_scanning_points(im,scans)
    im.show()
