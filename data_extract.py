#Import modules
from pymongo import MongoClient
import numpy as np
import matplotlib.pyplot as plt


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
        longitude += float(locations_list[i][0])*sr_list[i]
        latitude += float(locations_list[i][1])*sr_list[i]
    

    return longitude, latitude



