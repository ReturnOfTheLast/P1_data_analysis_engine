from flask import Flask, request, Response, jsonify
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO
import data_analysis as da

db_username = "root"
db_password = "password"
db_host = "localhost"

app = Flask(__name__)

@app.get("/api/ssidoverview/<int:filtertype>/<string:filterstr>")
def ssidoverview(filtertype: int, filterstr: str):
    print(filtertype, filterstr)
    client = da.client(db_username, db_password, db_host)
    overview = da.generate_ssid_overview(client, filterstr, filtertype)
    return jsonify(overview)

@app.get("/api/bssidplot/<string:bssid>.png")
def bssidplot(bssid: str):
    client = da.client(db_username, db_password, db_host)
    fig = da.generate_bssid_graph(client, bssid)
    output = BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


@app.get("/api/heatmap/<string:bssid>.png")
def heatmap(bssid: str):
    client = da.client(db_username, db_password, db_host)
    datapoints = da.get_rssi_location_datapoints(client, bssid)
    ap_location = da.estimate_accesspoint_location(
        datapoints["rssi"], datapoints["location"]
    )
    
    im = da.generate_heatmap(ap_location, datapoints, 2000, 20)
    output = BytesIO()
    im.save(output, format='png')

    return Response(output.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    app.run("0.0.0.0", 8090)
