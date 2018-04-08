import pytz
import urllib.request
import json
from datetime import datetime
import http.client


# Gets the indoor temperature training data from the database.
def get_train_data():
    training_data = []
    try:
        conn = http.client.HTTPConnection("")

        payload = "temperature=23&token="

        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'x-access-token': "",
            'cache-control': "no-cache",
            'postman-token': ""
        }
        conn.request("GET", "/api/temperature?all=true", payload, headers)

        res = conn.getresponse()
        data = json.loads(res.read().decode('utf-8'))
        for x in data['temperatures']:
            dtg = datetime.strptime(x['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            dtg = pytz.timezone('UTC').localize(dtg)
            dtg = dtg.astimezone(pytz.timezone('Europe/Stockholm'))
            temp = str(x['temperature']).replace('.', '')
            while len(temp) < 5:
                temp += '0'
            training_data.append([float(temp), dtg])
        last_timestamp = data['temperatures'][len(data['temperatures'])-1]['time']
    finally:
        conn.close()
    return training_data, last_timestamp


# Help method to get the outdoor temperature training data from SMHI.
def get_smhi_data():
    url = 'http://opendata-download-metobs.smhi.se/api/version/latest/parameter/1/station/52350/period/latest-months/data.json'
    smhi_data = []
    response = urllib.request.urlopen(url).read()
    data = json.loads(response.decode())
    for i in range(0, len(data["value"])):
        timestamp = str(data["value"][i]["date"])
        timestamp = int(timestamp[:-3])
        timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        timestamp_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        timestamp_dt = pytz.timezone('UTC').localize(timestamp_dt)
        timestamp_dt = timestamp_dt.astimezone(pytz.timezone('Europe/Stockholm'))
        value = data["value"][i]["value"]
        smhi_data.append([float(value) * 1000, timestamp_dt])
    return smhi_data


# Main function to collect and return both the outdoor and indoor temperature training data.
def get_all_data():
    train_data, last_timestamp = get_train_data()
    train_smhi = get_smhi_data()
    first = train_smhi[0][1]
    last = train_smhi[len(train_smhi) - 1][1]
    while train_data[0][1] < first:
        train_data.pop(0)
    while train_data[len(train_data) - 1][1] > last:
        train_data.pop()
    train_smhi.pop()
    data = []
    for a, b in zip(train_data, train_smhi):
        dtg = a[1]
        hour = round(dtg.hour + dtg.minute / 60. + dtg.second / 3600.)
        data.append([a[0], b[0], hour])
    return data, last_timestamp


# Chunks the data in to the correct shape.
def chunk(l, n):
    for j in range(0, len(l), n):
        yield l[j:j + n]
