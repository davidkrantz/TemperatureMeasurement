from flask import Flask, request, Response, redirect, render_template, g
import pygal
from datetime import datetime, timedelta, date
import pytz
import urllib.request
import json
from sklearn.svm import SVR
from sklearn.preprocessing import RobustScaler
import urllib.request
import http.client

import ml

global start
global end

app = Flask(__name__)


# Main page showing the temperature of the last 24 hours.
@app.route('/')
def main():
    return """
                    <html>
                     <head>
                          <title>%s</title>
                     </head>
                      <body bgcolor="#F9F9F9">
                                <button onclick="window.location.href='/'">Last 24 hours</button>
                                <button onclick="window.location.href='/today'">Today</button>
                                <button onclick="window.location.href='/forecast'">Forecast</button>
                                <form action="/form" method="POST">
                                    Select a start and end date and time:
                                    <input type="datetime-local" name="start_time">
                                    <input type="datetime-local" name="end_time">
                                    <input type="submit" name="my-form" value="Show">
                                </form>
                                <hr>
                                <figure>
                                    <embed type="image/svg+xml" src="/graph" />
                                </figure>
                     </body>
                </html>
"""


# Page that shows the temperature during the current day.
@app.route('/today')
def today():
    return """
                    <html>
                     <head>
                          <title>%s</title>
                     </head>
                      <body bgcolor="#F9F9F9">
                                <button onclick="window.location.href='/'">Last 24 hours</button>
                                <button onclick="window.location.href='/today'">Today</button>
                                <button onclick="window.location.href='/forecast'">Forecast</button>
                                <form action="/form" method="POST">
                                    Select a start and end date and time:
                                    <input type="datetime-local" name="start_time">
                                    <input type="datetime-local" name="end_time">
                                    <input type="submit" name="my-form" value="Show">
                                </form>
                                <hr>
                                <figure>
                                    <embed type="image/svg+xml" src="/graph_today" />
                                </figure>
                     </body>
                </html>
"""


# Page that shows a prediction of indoor temperature.
@app.route('/forecast')
def forecast():
    return """
                    <html>
                     <head>
                          <title>%s</title>
                     </head>
                      <body bgcolor="#F9F9F9">
                                <button onclick="window.location.href='/'">Last 24 hours</button>
                                <button onclick="window.location.href='/today'">Today</button>
                                <button onclick="window.location.href='/forecast'">Forecast</button>
                                <form action="/form" method="POST">
                                    Select a start and end date and time:
                                    <input type="datetime-local" name="start_time">
                                    <input type="datetime-local" name="end_time">
                                    <input type="submit" name="my-form" value="Show">
                                </form>
                                <hr>
                                <figure>
                                    <embed type="image/svg+xml" src="/graph_forecast" />
                                </figure>
                     </body>
                </html>
"""


# Page that shows the temperature between the dates and times that were inputted in the form.
@app.route('/date')
def date():
    return """
                    <html>
                     <head>
                          <title>%s</title>
                     </head>
                      <body bgcolor="#F9F9F9">
                                <button onclick="window.location.href='/'">Last 24 hours</button>
                                <button onclick="window.location.href='/today'">Today</button>
                                <button onclick="window.location.href='/forecast'">Forecast</button>
                                <form action="/form" method="POST">
                                    Select a start and end date and time:
                                    <input type="datetime-local" name="start_time">
                                    <input type="datetime-local" name="end_time">
                                    <input type="submit" name="my-form" value="Show">
                                </form>
                                <hr>
                                <figure>
                                    <embed type="image/svg+xml" src="/graph_date" />
                                </figure>
                     </body>
                </html>
"""


# Main graph.
@app.route("/graph")
def graph():
    return plot(" ", " ", '24')


# Returns a graph of the temperature from the current day.
@app.route("/graph_today", methods=['GET', 'POST'])
def graph_today():
    return plot('', '', 'today')


# Predict the coming 24 hours of indoor temperature
@app.route("/graph_forecast")
def graph_forecast():
    data, last_timestamp = ml.get_all_data()

    # Prediction
    # print(last_timestamp)
    # data.reverse()
    # train = data[:-24]
    # test = data[len(data) - 24:]
    # train = list(ml.chunk(train, 24))

    # Test
    train = data[:-48]
    test = data[len(data) - 48:len(data) - 24]
    actual = data[len(data) - 24:]
    train = list(ml.chunk(train, 24))
    real_temp = []
    for a in range(0, len(actual)):
        real_temp.append(actual[a][0])
    print(real_temp)

    # Train model and predict the new temperature
    train_X = []
    train_Y = []
    for k in range(0, len(train) - 2):
        for j in range(0, 24):
            train_X.append(train[k][j])
            train_Y.append(train[k + 1][j][0])
    rbX = RobustScaler()
    X = rbX.fit_transform(train_X)
    rbY = RobustScaler()
    Y = rbY.fit_transform(train_Y)
    svm = SVR(kernel='rbf', C=1e3, gamma=0.0001)
    svm.fit(X, Y)
    svm_pred = svm.predict(rbX.transform(test))
    new_temp = list((rbY.inverse_transform(svm_pred)) / 1000)
    print(new_temp)

    # Get the timestamp for the next 24 hours
    timestamp = []
    last_timestamp = last_timestamp[:-5]
    for i in range(1, 25):
        last_timestamp_dt = datetime.strptime(last_timestamp, '%Y-%m-%dT%H:%M:%S')
        last_timestamp_dt = last_timestamp_dt.replace(tzinfo=None)
        correct_time = last_timestamp_dt + timedelta(hours=int(i))
        timestamp.append(str(correct_time))

    # Plot the prediction (and verfication)
    line_chart = pygal.Line(x_label_rotation=30)
    line_chart.title = '24 hour forecast of indoor temperature in degrees Celsius'
    line_chart.x_labels = map(str, list(timestamp))
    line_chart.add('Prediction', list(new_temp))
    real_temp[:] = [x/1000 for x in real_temp]
    line_chart.add('Actual', list(real_temp))
    return Response(response=line_chart.render(), content_type='image/svg+xml')


# Parses the interval from the form() function and returns the correct plot.
@app.route("/graph_date")
def graph_date():
    global start
    global end
    start_time = start
    end_time = end
    start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    start_show = str(start_dt)
    end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    end_show = str(end_dt)
    return plot(start_show, end_show, 'interval')


# Help function that fetches the inputted form data and saves it in two global variables.
@app.route('/form', methods=['GET', 'POST'])
def form():
    try:
        start_time = request.form['start_time'] + ':00'
        end_time = request.form['end_time'] + ':00'
        global start
        global end
        start = start_time
        end = end_time
        return redirect("/date", code=302)
    finally:
        print('Ok')


# Fetches the outside temperature from SMHI for the specified url.
def get_smhi(interval):
    if interval == 'last-days':
        url = 'http://opendata-download-metobs.smhi.se/api/version/latest/parameter/1/station/52350/period/latest-day/data.json'
    else:
        url = 'http://opendata-download-metobs.smhi.se/api/version/latest/parameter/1/station/52350/period/latest-months/data.json'
    date = []
    temp = []
    response = urllib.request.urlopen(url).read()
    data = json.loads(response.decode())
    for i in range(0, len(data["value"])):
        timestamp = str(data["value"][i]["date"])
        timestamp = int(timestamp[:-3])
        timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        timestamp_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        timestamp_dt = pytz.timezone('UTC').localize(timestamp_dt)
        timestamp_dt = timestamp_dt.astimezone(pytz.timezone('Europe/Stockholm'))
        timestamp_dt = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
        value = data["value"][i]["value"]
        date.append(timestamp_dt)
        temp.append(value)
    return date, temp


# Function that connects to the database and given the inputted arguments returns the correct graph.
# If the arguments are empty strings, it means that we want to show the temperature of the last 24 hours.
def plot(start_show, end_show, interval):
    try:
        conn = http.client.HTTPConnection("")
        payload = "temperature=23&token="
        headers = {
            'content-type': "application/x-www-form-urlencoded",
            'x-access-token': "",
            'cache-control': "no-cache",
            'postman-token': ""
        }
        if interval == "24":
            conn.request("GET", "/api/temperature?unit=hours&count=24", payload, headers)
            smhi_date, smhi_temp = get_smhi('last-days')
            smhi_date.pop(0)
            smhi_temp.pop(0)
        elif interval == 'today':
            now = datetime.now()
            now = pytz.timezone('UTC').localize(now)
            now = now.astimezone(pytz.timezone('Europe/Stockholm'))
            nbr_hrs = str(now.hour)
            conn.request("GET", "/api/temperature?unit=hours&count=" + nbr_hrs, payload, headers)
            smhi_date, smhi_temp = get_smhi('last-days')
            start_time = datetime.now().strftime("%Y-%m-%d 00:00:00")
            k = 0
            while smhi_date[k] <= str(start_time):
                smhi_date.pop(0)
                smhi_temp.pop(0)
        else:
            end_dtg = datetime.strptime(end_show, "%Y-%m-%d %H:%M:%S")
            start_dtg = datetime.strptime(start_show, "%Y-%m-%d %H:%M:%S")
            delta = end_dtg - start_dtg
            nbr_days = str(delta.days)
            end_time = end_dtg.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            conn.request("GET", "/api/temperature?unit=days&enddate=" + end_time + "&count=" + nbr_days, payload,
                         headers)
            smhi_date, smhi_temp = get_smhi('last-months')
            k = 0
            while smhi_date[k] < str(start_dtg):
                smhi_date.pop(0)
                smhi_temp.pop(0)

        smhi_temp = map(float, smhi_temp)

        res = conn.getresponse()
        data = json.loads(res.read().decode('utf-8'))
        temp = []
        timestamp = []
        for x in data['temperatures']:
            temp.append(float(x['temperature']))
            dtg = datetime.strptime(x['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
            dtg = pytz.timezone('UTC').localize(dtg)
            dtg = dtg.astimezone(pytz.timezone('Europe/Stockholm')).replace(tzinfo=None)
            dtg = dtg.strftime('%Y-%m-%d %H:%M:%S')
            timestamp.append(dtg)
        start = datetime.strptime(data['temperatures'][0]['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        start = pytz.timezone('UTC').localize(start)
        start = start.astimezone(pytz.timezone('Europe/Stockholm')).replace(tzinfo=None)
        start = start.strftime('%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(data['temperatures'][len(data['temperatures']) - 1]['time'], "%Y-%m-%dT%H:%M:%S.%fZ")
        end = pytz.timezone('UTC').localize(end)
        end = end.astimezone(pytz.timezone('Europe/Stockholm')).replace(tzinfo=None)
        end = end.strftime('%Y-%m-%d %H:%M:%S')
        title = 'Temperature in degrees Celsius between ' + start + ' and ' + end
        line_chart = pygal.Line(x_label_rotation=30)
        line_chart.title = title
        if len(temp) < 30:
            line_chart.x_labels = map(str, list(timestamp))
        line_chart.add('Inside', list(temp))
        if interval != 'interval':
            line_chart.add('Outside', list(smhi_temp), secondary=True, x_title='Time')
        return Response(response=line_chart.render(), content_type='image/svg+xml')
    finally:
        conn.close()


# Runs the web server.
if __name__ == "__main__":
    app.run(host='0.0.0.0')
