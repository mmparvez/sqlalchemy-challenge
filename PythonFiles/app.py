import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)
# Find the most recent date in the data set.
recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
# Convert list of tuples into normal list
recent_date = list(np.ravel(recent_date))[0]
recent_date = dt.datetime.strptime(recent_date, '%Y-%m-%d')
# Calculate the date one year from the last date in data set.
year_ago = dt.date(recent_date.year, recent_date.month, recent_date.day)\
    - dt.timedelta(days=365)

session.close()


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes for Hawaii Weather Data:<br/><br>"
        f"-- Daily Precipitation Totals for Last Year: <a href=\"/api/v1.0/precipitation\">/api/v1.0/precipitation<a><br/>"
        f"-- Active Weather Stations: <a href=\"/api/v1.0/stations\">/api/v1.0/stations<a><br/>"
        f"-- Daily Temperature Observations for Station USC00519281 for Last Year: <a href=\"/api/v1.0/tobs\">/api/v1.0/tobs<a><br/>"
        f"-- Min, Average & Max Temperatures for Date Range(yyyy-mm-dd): /api/v1.0/temp/start<start>/end<end><br/>"
        f"NOTE: If no end-date is provided, the temp api calculates stats through 2017-08-23<br>" 
    )


@app.route("/api/v1.0/precipitation")
def precipitation(q_dt=year_ago):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Perform a query to retrieve the data and precipitation scores
    year_data = session.query(Measurement.date, Measurement.prcp ).\
     filter(Measurement.date >= q_dt)#.order_by(measurement.date,desc).all()

    session.close()

    precipitation = []
    for result in year_data:
        r = {}
        r[result[0]] = result[1]
        precipitation.append(r)
    
    return jsonify(precipitation)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of stations from the dataset."""
    # Query all stations
    results = session.query(Station.station).all()
    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))

    session.close()

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs(q_dt = year_ago):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of Temperature Observations (tobs) of the most-active station for the previous year"""
    # Query Most Active stations
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    most_act_stn = active_stations[0][0]
    
    #Most active station Tobs
    results = session.query(Measurement.station, Measurement.tobs).\
        filter(Measurement.station == most_act_stn).\
        filter(Measurement.date >= q_dt).all()

    session.close()

    # convert list of tuples to show date and temprature values
    tobs_list = []
    for result in results:
        r = {}
        r[result[0]] = result[1]
        tobs_list.append(r)

    return jsonify(tobs_list)

@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def temp(start, end = year_ago):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""
    # Query for the min, max, and avg temps for the given start date & end date
    start_temps = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs),\
        func.max(Measurement.tobs)).filter(Measurement.date >= start).\
            filter(Measurement.date <= end).all()

    session.close()

    # convert list of tuples to show date and temprature values
    t_list = []
    for result in start_temps:
        r = {}
        r["Min Temp"] = result[0]
        r["Avg Temp"] = result[1]
        r["Max Temp"] = result[2]
        t_list.append(r)

    return jsonify(t_list)


if __name__ == '__main__':
    app.run(debug=True)
