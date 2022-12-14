"""Module that contains functions that can be called to analyse data in the database

The functions in here can be used to do needed data analysis for the frontend.
This module is primarily used by the flask api application
"""

#Import modules
from pymongo import MongoClient
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from io import BytesIO

# Import heatmap utilities
import heatmap_utils as hu

# Set the matplotlib to agg to avoid errors when generating images
# as an headless server
matplotlib.use("agg")

def client(
    username: str,
    password: str,
    host: str
) -> MongoClient:
    """Make a client to communicate with the database.

    Args:
        username (str): DB Username
        password (str): DB Password
        host (str): Hostname where the DB is located

    Returns:
        MongoClient: DB Client
    """

    # Make client connection to database and return it
    return MongoClient(f"mongodb://{username}:{password}@{host}:27017/")

def generate_ssid_overview(
    client: MongoClient,
    filterstr: str,
    filtertype: int
) -> dict:
    """Get an overview of the ssid-bssid connections.

    Args:
        client (MongoClient): DB Client
        filterstr (str): String to filter by
        filtertype (int): Type of filter, 0 = ssid, 1 = bssid, 2 = no filter

    Returns:
        dict: Overview of ssid-bssid connections
    """

    # Get Collections from database
    db = client["scandata"]
    ap_data_frames, bssid_pool, ssid_pool = (db["ap_data_frames"],
                                             db["bssid_pool"],
                                             db["ssid_pool"])

    # Instantiate empty dictionary for storing return data
    ssid_bssid = {}

    # Loop over all ssids
    for ssid in ssid_pool.find():

        # Filter by ssid name (or dont if filter is set to bssid)
        if (filtertype == 2 or
            (filterstr in ssid['name'] and filtertype == 0) or
            filtertype == 1):
            
            # Instantiate empty list for the ssids mac addresses name
            ssid_bssid[ssid['name']] = []
            
            # Get id of ssid document
            ssid_id = ssid['_id']

            # Loop over all mac address for ssid
            for bssid in bssid_pool.find({'ssid': ssid_id}):

                # Filter by bssid (or dont if filter is set ssid)
                if (filtertype == 2 or
                    (filterstr in bssid['name'] and filtertype == 1) or
                    filtertype == 0):

                    # Find the number of scans the bssid is in
                    num_of_scans = len(
                        list(
                            ap_data_frames.find(
                                {"bssid": bssid["_id"]}
                            )
                        )
                    )

                    # Append mac address and number of scanes to the list
                    ssid_bssid[ssid['name']].append(
                        (bssid['name'], num_of_scans)
                    )
    
    # Remove all ssids that doesn't have at least one mac address
    keys = [k for k, v in ssid_bssid.items() if v == []]

    for key in keys:
        del ssid_bssid[key]

    # Return dictionary
    return ssid_bssid

def generate_datapoint_overview(
    client: MongoClient,
    bssid: str
) -> list[dict]:
    """Generate a table of datapoints.

    Args:
        client (MongoClient): Client to connect to the DB
        bssid (str): The BSSID to generate datapoints for

    Returns:
        list[dict]: List of dictionarys containing location, rssi and time
    """

    # Get Collections from database
    db = client["scandata"]
    data_frames, ap_data_frames, bssid_pool = (db["data_frames"],
                                              db["ap_data_frames"],
                                              db["bssid_pool"])

    # Get DB id of the bssid
    bssid_id = bssid_pool.find_one({"name": bssid})["_id"]

    # Instantiate empty list to contain the datapoints
    datapoints = []

    # Extract datapoints
    for ap_data_frame in ap_data_frames.find({"bssid": bssid_id}):
        ap_data_frame_id = ap_data_frame["_id"]
        
        # Make temporary dictionary
        temp_dict = {"location": (), "rssi": 0, "time": 0}
        
        # Find the data frame in the database
        data_frame = data_frames.find_one({"ap_data_frames": ap_data_frame_id})
        
        # Populate the temporary dictionary with location, rssi and time from
        # the data frame
        temp_dict["location"] = (
            data_frame["location"][0],
            data_frame["location"][1]
        )
        temp_dict["rssi"] = ap_data_frame["rssi"]
        temp_dict["time"] = data_frame["time"]
        
        # Added the datapoints to the datapoints list
        datapoints.append(temp_dict)

    # Return the datapoints
    return datapoints

def generate_bssid_graph(
    client: MongoClient,
    bssid: str
) -> plt.Figure:
    """Make a graph of bssid rssi and time.

    Args:
        client (MongoClient): DB Client
        bssid (str): Mac Address to graph

    Returns:
        plt.Figure: Graph
    """

    # Get Collections from database
    db = client["scandata"]
    data_frames, ap_data_frames, bssid_pool = (db["data_frames"],
                                               db["ap_data_frames"],
                                               db["bssid_pool"])

    # Get DB id of the bssid
    bssid_id = bssid_pool.find_one({"name": bssid})["_id"]

    # Instantiate empty list to hold ap_data_frames ids
    ap_data_frames_ids = []

    # Loop over all data_frames that reference the bssid
    # and append their ids to the list
    for ap_data_frame in ap_data_frames.find({'bssid': bssid_id}):
        ap_data_frames_ids.append(ap_data_frame["_id"])
    
    # Instantiate empty list to contain the datapoints to plot
    datapoints = []

    # Loop over all ap_data_frame ids
    # and find the rssi and time for each ap_data_frame
    # adding them to the datapoints as an tuple
    for ap_data_frames_id in ap_data_frames_ids:
        y = ap_data_frames.find_one({"_id": ap_data_frames_id})['rssi']
        x = data_frames.find_one({"ap_data_frames": ap_data_frames_id})['time']
        datapoints.append((x,y))

    # Make plotable datapoints by splitting it into two lists
    # of x and y values
    x, y = zip(*datapoints)

    # Make scatter plot of the values
    fig, ax = plt.subplots()
    ax.plot(x, y, label="Measured RSSI")

    # Setup legends
    ax.legend()
    ax.set_title("RSSI over Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("RSSI")
   
    # Return Figure
    return fig

def generate_graph_of_aps(
    client: MongoClient
):
    """Generate a graph of the number of access points scanned over time.

    Args:
        client (MongoClient): Client to connect to DB
    """
    # Get Collections from database
    db = client["scandata"]
    data_frames = db["data_frames"]

    # Instantiate empty list to contain the datapoints to plot
    datapoints = []

    for data_frame in data_frames.find({}):
        y = len(data_frame["ap_data_frames"])
        x = data_frame["time"]
        datapoints.append((x, y))

    # plotable datapoints by splitting it into two lists
    # of x and y values
    x, y = zip(*datapoints)

    # Make scatter plot of the values
    fig, ax = plt.subplots()
    ax.plot(x, y, label="Number of Access Points")

    # Setup legends
    ax.legend()
    ax.set_title("Access Point scans over Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Access Point Scans")

    # Return Figure
    return fig

def get_rssi_location_datapoints(
    client: MongoClient,
    bssid: str
) -> dict:
    """Get datapoints of the rssi and location of chosen mac address.

    Args:
        client (MongoClient): DB Client
        bssid (str): Mac Address to get datapoints for

    Returns:
        dict: RSSI and Location datapoints
    """
   
    # Get Collections from database
    db = client["scandata"]
    data_frames, ap_data_frames, bssid_pool = (db["data_frames"],
                                               db["ap_data_frames"],
                                               db["bssid_pool"])
    
    # Grab id of the requested bssid
    bssid_id = bssid_pool.find_one({"name": bssid})["_id"]

    # Instantiate empty list of ap_data_frame ids
    ap_data_frames_ids = []

    # Loop over all ap_data_frames that reference the bssid
    # and add the ap_data_frames' id to the list
    for ap_data_frames_id in ap_data_frames.find({"bssid": bssid_id}):
        ap_data_frames_ids.append(ap_data_frames_id["_id"])

    # Instantiate dictionary to hold the datapoints
    datapoints = {"rssi": [], "location": [], "number": [], "time": []}

    # Loop over all the ap_data_frames ids and append
    # the measured rssi and location to the dictionary
    for ap_data_frames_id in ap_data_frames_ids:
        datapoints["rssi"].append(
            ap_data_frames.find_one(
                {"_id": ap_data_frames_id}
            )["rssi"]
        )
        datapoints["location"].append(
            data_frames.find_one(
                {"ap_data_frames": ap_data_frames_id}
            )["location"]
        )
        datapoints["number"].append(
            data_frames.find_one(
                {"ap_data_frames": ap_data_frames_id}
            )["number"]
        )
        datapoints["time"].append(
            data_frames.find_one(
                {"ap_data_frames": ap_data_frames_id}
            )["time"]
        )

    # Return the dictionary of datapoints
    return datapoints

def estimate_accesspoint_location(
    rssi_list: list[int],
    locations_list: list[tuple[float, float]]
) -> tuple[float, float]:
    """Estimate the location of the access point using trilateration.

    Args:
        rssi_list (list[int]): List of rssi measurements
        locations_list (list[tuple[float, float]]): List of locations

    Returns:
        tuple[float, float]: Estimated longitude and latitude
    """

    # Instantiate empty list to hold signal strengths
    signal_strengths = []

    # Loop over all rssis, convert them signal positive signal strength by
    # 100 + rssi (rssi is negative)
    for rssi in rssi_list:
        signal_strengths.append(100+rssi)
    
    # Instantiate empty list to hold signal ratios
    signal_ratios = []

    # Loop over all signal strengths and convert them to signal ratios by
    # calculation how big a part of the sum of signal strengths each
    # signal strength is
    for signal_strength in signal_strengths:
        signal_ratios.append(signal_strength/sum(signal_strengths))

    # Variables to hold the calculated longitude and latitude
    longitude = 0
    latitude = 0

    # Loop over all the locations and signal_ratios and add the
    # location longitude sized by the signal_ratio to the longitude variable
    # and the same with the latitude
    for location, signal_ratio in zip(locations_list, signal_ratios):
        longitude += location[1] * signal_ratio
        latitude += location[0] * signal_ratio
    
    # Return the location estimation
    return (round(latitude,6), round(longitude, 6))

def convert_locations_to_grid( 
    ap_location: tuple[float, float],
    scan_locations: list[list[float, float]],
    isize: int,
    buffer: int
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    """Convert real world coordinates to locations on an image grid.

    Args:
        ap_location (tuple[float, float]): Location of Access Point
        scan_locations (list[list[float, float]]): Locations of scans
        isize (int): Size of image in pixels
        buffer (int): Size of outer buffer

    Returns:
        tuple[tuple[int, int], list[tuple[int, int]]]: Grid coordinates of access point and scans
    """

    # Calculate size without the buffers
    size = isize-buffer*2

    # Get the minimum and maximum longitude 
    min_longitude = min(min(scan_locations, key = lambda x: x[1])[1], ap_location[1])
    max_longitude = max(max(scan_locations, key = lambda x: x[1])[1], ap_location[1])

    # Get the minimum and maximum latitude
    # Technically inversed since the image will have (0,0) in the top left,
    # But the gps has it in the bottom left, so flipping the latitude around will
    # avoid a y-axis flip.
    min_latitude = max(max(scan_locations, key = lambda x: x[0])[0], ap_location[0])
    max_latitude = min(min(scan_locations, key = lambda x: x[0])[0], ap_location[0])
    
    # Calculate the aspcet ratio between the x- and y-axis
    aspect_ratio = abs((max_longitude-min_longitude)/(max_latitude-min_latitude))

    # Set the x- and y-axis size based on the aspect_ratio
    if aspect_ratio > 1:
        x_axis = size 
        y_axis = size * aspect_ratio**(-1)
    else:
        y_axis = size
        x_axis = size * aspect_ratio

    # Calculate extra padding space to center the data when one axis is smaller
    x_padding = (y_axis - x_axis) / 2
    if x_padding < 0: x_padding = 0
    
    y_padding = (x_axis - y_axis) / 2
    if y_padding < 0: y_padding = 0

    # Tuple of access point grid location
    ap_grid_location = (
        int(
            abs(
                (ap_location[1] - min_longitude)/(max_longitude-min_longitude)
            )*x_axis
        ) + buffer + x_padding,
        int(
            abs(
                (ap_location[0] - min_latitude)/(max_latitude-min_latitude)
            )*y_axis
        ) + buffer + y_padding
    )

    # Instantiate empty list for scan grid locations
    scan_grid_locations = []

    # Loop over all scan locations and append a tuple of grid location
    for location in scan_locations:
        scan_grid_locations.append((
            int(
                abs(
                    (location[1] - min_longitude)/(max_longitude-min_longitude)
                )*x_axis 
            ) + buffer + x_padding,
            int(
                abs(
                    (location[0] - min_latitude)/(max_latitude-min_latitude)
                )*y_axis
            ) + buffer + y_padding
        ))
    
    # Return grid locations
    return ap_grid_location, scan_grid_locations

def generate_heatmap(
    ap_location: tuple[float, float],
    rssi_location_datapoints: dict,
    size: int,
    buffer: int
) -> Image.Image:
    """Generate a heatmap of access point.

    Args:
        ap_location (tuple[float, float]): Location of the access point
        rssi_location_datapoints (dict): Data points from get_rssi_location_datapoints
        size (int): Size of the image
        buffer (int): Outer buffer on the image

    Returns:
        Image.Image:
    """

    # Convert locations to grid locations
    if len(rssi_location_datapoints) > 1:
        ap_grid_location, scan_grid_locations = convert_locations_to_grid(
            ap_location,
            rssi_location_datapoints['location'],
            size,
            buffer
        )
    else:
        # If there isn't more then 1 scans of the access points we can't
        # generate a heatmap and we should instead display an error and
        # return early.
        im = hu.make_image(500, 500)
        draw = ImageDraw.ImageDraw(im)
        draw.text(
            (250, 250),
            "Not Enough Data to Generate Heatmap",
            fill=(0, 0, 0),
            font=hu.fnt,
            anchor="mm"
        )
        return im

    # Make dict to describe the access point node
    ap = {
        'coords': ap_grid_location,
        'label': f'Access Point\n{ap_location}'
    }

    # Instantiate empty list to hold scan nodes
    scans = []

    # Loop over all scan grid locations, rssi and real locations
    # then append a node to the list for each
    for grid_location, rssi, real_location, number, time in zip(
        scan_grid_locations,
        rssi_location_datapoints["rssi"],
        rssi_location_datapoints["location"],
        rssi_location_datapoints["number"],
        rssi_location_datapoints["time"]
    ):
        scans.append(
            {
                'coords': grid_location,
                'rssi': rssi,
                'label': f"{real_location}\n({number}) ({time})"
            }
        )

    # Make the image and draw the heat circles and nodes
    im = hu.make_image(size, size)
    hu.draw_heat_circles(im,ap,scans)
    hu.draw_accesspoint(im,ap)
    hu.draw_scanning_points(im,scans)
    hu.draw_scale_guide(im)

    # Return the generated image
    return im
