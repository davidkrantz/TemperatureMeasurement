from flask import Flask, request, Response, redirect, render_template, g
import pygal
from mysql.connector import MySQLConnection, Error
import MySQLdb as mdb
from datetime import datetime
import pytz

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
    return plot(" ", " ", " ", " ")


# Returns a graph of the temperature from the current day.
@app.route("/graph_today", methods=['GET', 'POST'])
def graph_today():
    start_time = datetime.now().strftime("%Y-%m-%d 00:00:00")
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    start_show = str(start_dt)
    start_dt = pytz.timezone('Europe/Stockholm').localize(start_dt)
    start_dt = start_dt.astimezone(pytz.UTC).replace(tzinfo=None)
    end_time = datetime.now().strftime('%Y-%m-%d 23:59:59')
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    end_show = str(end_dt)
    end_dt = pytz.timezone('Europe/Stockholm').localize(end_dt)
    end_dt = end_dt.astimezone(pytz.UTC).replace(tzinfo=None)
    start_string = str(start_dt)
    end_string = str(end_dt)
    return plot(start_string, end_string, start_show, end_show)


# Parses the interval from the form() function and returns the correct plot.
@app.route("/graph_date")
def graph_date():
    global start
    global end
    start_time = start
    end_time = end
    start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    start_show = str(start_dt)
    start_dt = pytz.timezone('Europe/Stockholm').localize(start_dt)
    start_dt = start_dt.astimezone(pytz.UTC).replace(tzinfo=None)
    end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    end_show = str(end_dt)
    end_dt = pytz.timezone('Europe/Stockholm').localize(end_dt)
    end_dt = end_dt.astimezone(pytz.UTC).replace(tzinfo=None)
    start_string = str(start_dt)
    end_string = str(end_dt)
    return plot(start_string, end_string, start_show, end_show)


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

    except Error as e:
        print(e)


# Function that connects to the MySQL database and given the inputted arguments returns the correct graph.
# If the arguments are empty strings, it means that we want to show the temperature of the last 24 hours.
def plot(start_string, end_string, start_show, end_show):
    try:
        con = mdb.connect('localhost',
                          'pi_insert',
                          'password',
                          'measurements')
        cursor = con.cursor()
        if start_string == " ":
            query = "SELECT `dtg`, `temperature` FROM `temperature` ORDER BY `dtg` DESC LIMIT 0,24"
            title = 'Temperature in degrees Celsius of the last 24 hours'
        else:
            query = "SELECT `dtg`, `temperature` FROM `temperature` WHERE `dtg` BETWEEN '" + start_string + "' and '" \
                    + end_string + "' ORDER BY `dtg` DESC"
            title = 'Temperature in degrees Celsius between ' + start_show + ' and ' + end_show
        cursor.execute(query)
        temp = []
        timestamp = []
        for dtg, temperature in cursor:
            temp.append(temperature)
            dtg = pytz.timezone('UTC').localize(dtg)
            dtg = dtg.astimezone(pytz.timezone('CET'))
            timestamp.append(dtg.replace(tzinfo=None))
        mean = sum(temp) / float(len(temp))
        mean_temp = [mean] * len(temp)
        line_chart = pygal.Line(x_label_rotation=30)
        line_chart.title = title
        if len(temp) < 30:
            line_chart.x_labels = map(str, list(reversed(timestamp)))
        line_chart.add('Inside', list(reversed(temp)))
        line_chart.add('Mean', mean_temp, show_dots=False, stroke_style={'width': 2, 'dasharray': '3, 6, 12, 24'})
        return Response(response=line_chart.render(), content_type='image/svg+xml')

    except Error as e:
        print(e)

    finally:
        cursor.close()
        con.close()


# Runs the web server.
if __name__ == "__main__":
    app.run(host='0.0.0.0')
