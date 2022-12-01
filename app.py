"""Flask application to serve data analysis as an API

This script starts up a flask http server to serve API endpoints for different
data analysis methods and return the requested data to the main interface.
"""

# Import Modules
from flask import Flask, request, Response, jsonify
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import argparse
from io import BytesIO

# Import data analysis module
import data_analysis as da


# Docker flag for when run in a docker network
parser = argparse.ArgumentParser()
parser.add_argument('--docker', action="store_true", default=False, dest="docker")
args = parser.parse_args()

# Set the credentials for the mongo database
db_username = "root"
db_password = "password"
db_host = "localhost"

# If in a docker network change the database to mongo for
# docker dns resolution over the provided network
if args.docker: db_host = "mongo"

# Define the flask application
app = Flask(__name__)

@app.get("/api/ssidoverview/<int:filtertype>/<string:filterstr>")
def ssidoverview(filtertype: int, filterstr: str):
    """Endpoint for list of ssid and bssid relationships with filter.

    Args:
        filtertype (int): Type of filter, 0 = ssid, 1 = bssid, 2 = no filter
        filterstr (str): String to filter by
    """

    # Make db client
    client = da.client(db_username, db_password, db_host)
    
    # Get the overview from the data analysis function
    overview = da.generate_ssid_overview(client, filterstr, filtertype)
    
    # Return result in json format
    return jsonify(overview)

@app.get("/api/apscans.png")
def applot():
    """Endpoint to get a plot of bssids seen over time.
    """

    # Make db client
    client = da.client(db_username, db_password, db_host)
    
    # Generate the plot
    fig = da.generate_graph_of_aps(client)
    
    # Create file buffer in memory
    output = BytesIO()
    
    # Save the plot in the buffer as an png image
    FigureCanvas(fig).print_figure(output)
    
    # Return the png image
    return Response(output.getvalue(), mimetype='image/png')

@app.get("/api/bssidplot/<string:bssid>.png")
def bssidplot(bssid: str):
    """Endpoint to get a plot of rssi over time for bssid.

    Args:
        bssid (str): BSSID to plot the rssi of
    """

    # Make db client
    client = da.client(db_username, db_password, db_host)
    
    # Generate the plot
    fig = da.generate_bssid_graph(client, bssid)
    
    # Create file buffer in memory
    output = BytesIO()

    # Save the plot in the buffer as an png image
    FigureCanvas(fig).print_png(output)

    # Return the png image
    return Response(output.getvalue(), mimetype='image/png')

@app.get("/api/bssiddatapoints/<string:bssid>")
def bssiddatapoints(bssid: str):
    """Endpoint to get the datapoints collected about bssid.

    Args:
        bssid (str): BSSID to get datapoints for
    """

    # Make db client
    client = da.client(db_username, db_password, db_host)
    
    # Generate the datapoints
    overview = da.generate_datapoint_overview(client, bssid)
    
    # Return the datapoints in json format
    return jsonify(overview)

@app.get("/api/heatmap/<string:bssid>.png")
def heatmap(bssid: str):
    """Endpoint to generate a heatmap for bssid.

    Args:
        bssid (str): BSSID to generate heatmap for
    """

    # Make db client
    client = da.client(db_username, db_password, db_host)
    
    # Get the datapoints
    datapoints = da.get_rssi_location_datapoints(client, bssid)
    
    # Estimate the access point location
    ap_location = da.estimate_accesspoint_location(
        datapoints["rssi"], datapoints["location"]
    )
    
    # Generate heatmap
    im = da.generate_heatmap(ap_location, datapoints, 2000, 20)
    
    # Make file buffer in memory
    output = BytesIO()

    # Save heatmap in the buffer as a png image
    im.save(output, format='png')

    # Return the png image
    return Response(output.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    # Start the flask server when this file is run
    app.run("0.0.0.0", 8090)
