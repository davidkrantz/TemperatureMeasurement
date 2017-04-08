from flask import Flask
import pygal
from mysql.connector import MySQLConnection, Error
import MySQLdb as mdb
from datetime import timedelta, datetime
from flask import request

app = Flask(__name__)

# Main page showing the temperature of the last 24 hours
@app.route("/")
def main():
    try:
        con = mdb.connect('localhost',
                          'pi_insert',
                          'password',
                          'measurements')
        cursor = con.cursor()
        query = "SELECT `dtg`, `temperature` FROM `temperature` ORDER BY `dtg` DESC LIMIT 0,24"
        cursor.execute(query)
        temp = []
        timestamp = []
        for dtg, temperature in cursor:
            temp.append(temperature)
            timestamp.append(dtg + timedelta(hours=2))
        mean = sum(temp) / float(len(temp))
        mean_temp = [mean] * len(temp)
        line_chart = pygal.Line(x_label_rotation=30)
        line_chart.title = 'Temperature in degrees Celsius of the last 24 hours'
        line_chart.x_labels = map(str, list(reversed(timestamp)))
        line_chart.add('Inside', list(reversed(temp)))
        line_chart.add('Mean', mean_temp, show_dots=False, stroke_style={'width': 2, 'dasharray': '3, 6, 12, 24'})
        html = """
                <html>
                     <head>
                          <title>%s</title>
                     </head>
                      <body>
                                <button onclick="window.location.href='/'">Last 24 hours</button>
                                <button onclick="window.location.href='/today'">Today</button>
                                <form action="/input" method="POST">
                                    Select a start and end date and time:
                                    <input type="datetime-local" name="start_time" min="2018-03-17">
                                    <input type="datetime-local" name="end_time" max="2018-03-19">
                                    <input type="submit" name="my-form" value="Show">
                                </form>
                         %s
                     </body>
                </html>
                """ % (line_chart.title, line_chart.render())
        return html

    except Error as e:
        print(e)

    finally:
        cursor.close()
        con.close()

# Fetches the timestamps and temperatures from the database corresponding to the inputed dates
@app.route("/input", methods=['GET', 'POST'])
def input():
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    start_string = str(start_time)
    end_string = str(end_time)
    start_string += ':00'
    end_string += ':00'
    start_string = start_string.replace('T', ' ')
    end_string = end_string.replace('T', ' ')
    try:
        con = mdb.connect('localhost',
                          'pi_insert',
                          'password',
                          'measurements')
        cursor = con.cursor()
        query = "SELECT `dtg`, `temperature` FROM `temperature` WHERE `dtg` BETWEEN '"
        query += start_string
        query += "' and '"
        query += end_string
        query += "' ORDER BY `dtg` DESC"
        cursor.execute(query)
        temp = []
        timestamp = []
        for dtg, temperature in cursor:
            temp.append(temperature)
            timestamp.append(dtg + timedelta(hours=2))
        mean = sum(temp) / float(len(temp))
        mean_temp = [mean] * len(temp)
        line_chart = pygal.Line(x_label_rotation=30)
        line_chart.title = 'Temperature in degrees Celsius between ' + start_string + ' and ' + end_string
        if len(temp) < 30:
            line_chart.x_labels = map(str, list(reversed(timestamp)))
        line_chart.add('Inside', list(reversed(temp)))
        line_chart.add('Mean', mean_temp, show_dots=False, stroke_style={'width': 2, 'dasharray': '3, 6, 12, 24'})
        html = """
                <html>
                     <head>
                          <title>%s</title>
                     </head>
                      <body>
                            <button onclick="window.location.href='/'">Last 24 hours</button>
                            <button onclick="window.location.href='/today'">Today</button>
                                <form action="/input" method="POST">
                                    Select a start and end date and time:
                                    <input type="datetime-local" name="start_time" min="2018-03-17">
                                    <input type="datetime-local" name="end_time" max="2018-03-19">
                                    <input type="submit" name="my-form" value="Show">
                                </form>
                         %s
                     </body>
                </html>
                """ % (line_chart.title, line_chart.render())
        return html

    except Error as e:
        print(e)

    finally:
        cursor.close()
        con.close()

# Page that shows the temperature during the current day
@app.route("/today", methods=['GET', 'POST'])
def today():
    start_time = datetime.utcnow().strftime('%Y:%m:%d')
    end_time = datetime.now().strftime('%Y:%m:%d %H:%M:%S')
    start_string = str(start_time)
    end_string = str(end_time)
    start_string += ' 00:00:00'
    try:
        con = mdb.connect('localhost',
                          'pi_insert',
                          'password',
                          'measurements')
        cursor = con.cursor()
        query = "SELECT `dtg`, `temperature` FROM `temperature` WHERE `dtg` BETWEEN '"
        query += start_string
        query += "' and '"
        query += end_string
        query += "' ORDER BY `dtg` DESC"
        cursor.execute(query)
        temp = []
        timestamp = []
        for dtg, temperature in cursor:
            temp.append(temperature)
            timestamp.append(dtg + timedelta(hours=2))
        mean = sum(temp) / float(len(temp))
        mean_temp = [mean] * len(temp)
        end_string = str((datetime.now() + timedelta(hours=2)).strftime('%Y:%m:%d %H:%M:%S'))
        line_chart = pygal.Line(x_label_rotation=30)
        line_chart.title = 'Temperature in degrees Celsius between ' + start_string + ' and ' + end_string
        line_chart.x_labels = map(str, list(reversed(timestamp)))
        line_chart.add('Inside', list(reversed(temp)))
        line_chart.add('Mean', mean_temp, show_dots=False, stroke_style={'width': 2, 'dasharray': '3, 6, 12, 24'})
        html = """
                    <html>
                         <head>
                              <title>%s</title>
                         </head>
                          <body>
                                <button onclick="window.location.href='/'">Last 24 hours</button>
                                <button onclick="window.location.href='/today'">Today</button>
                                    <form action="/input" method="POST">
                                        Select a start and end date and time:
                                        <input type="datetime-local" name="start_time" min="2018-03-17">
                                        <input type="datetime-local" name="end_time" max="2018-03-19">
                                        <input type="submit" name="my-form" value="Show">
                                    </form>
                             %s
                         </body>
                    </html>
                    """ % (line_chart.title, line_chart.render())
        return html

    except Error as e:
        print(e)

    finally:
        cursor.close()
        con.close()

# Runs the website
if __name__ == "__main__":
    app.run(host='0.0.0.0')
