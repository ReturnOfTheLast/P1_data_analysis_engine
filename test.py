import pymongo
import data_extract

db_usernanme = "root"
db_password = "password"
db_host = "localhost"

client = data_extract.client(db_usernanme,db_password,db_host)
filter_str = 'edu'
filtertype = 0

print(data_extract.ssid_overview(client, filter_str = filter_str, filtertype = filtertype))


data_extract.bssid_graph(client,"6c310eba0aa4")

print(data_extract.rssi_location(client, "6c310eba0aa4"))
    

    