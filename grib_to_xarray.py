#!/usr/bin/env python
# coding: utf-8

# Script to extract 'Downward short-wave radiation flux' and 'Temperature' from grib files and to generate netcdf files for each forecast


import os
import os.path
import pygrib
import pandas as pd
import numpy as np
import glob
import xarray as xr
from collections import OrderedDict
import argparse


def extract_param(filename, var):
    '''
    extract specified parameters from grib files and return it as an array
    '''
#    try:
#        with pygrib.open(filename) as grbs:
#            grb = grbs.select(name = var)[0]
#            data, lats, lons = grb.data()
#        return data
#    except ValueError: # This wont work, even if the exception is caught, the function now returns None.
#        print("Parameter not found: {}".format(var))

    with pygrib.open(filename) as grbs:
        try:
            grb = grbs.select(name=var)
        except ValueError:
            raise ValueError("Variable not found: {}".format(var))

        if len(grb) > 1:
            raise ValueError('File contains more than one variable'
                             'with name {}'.format(var))
        else:
            data, lats, lons = grb[0].data()
    return data



def convert_to_netcdf(files, outfilename,  var1, var2):

    '''
    Fetch var1 and var2 from grib files and converts it to netcdf file
    -----------------------------------

    filepath: complete path of grib file
    outfilename: file name to store the netcdf files
    var1: Downward short-wave radiation flux
    var2: Temperature

    '''
    gribfiles = files #glob.glob(os.path.join(filepath, "*grb2"))
    gribfiles.sort()

    # start extracting variables at step 3h, since step 0h does not contain all
    # variables, e.g. no 'Downward short-wave radiation flux'
    # maybe step 0h contains only instant values and no averages?
    grb = pygrib.open(gribfiles[1]).select(name=var1)[0]
    data, lats, lons = grb.data()
    date = pd.Timestamp(year=grb.year, month=grb.month, day=grb.day)
    time = pd.Timedelta(hours=grb.hour, minutes=grb.minute)
    var1_forecast = np.stack([extract_param(file, var1) for file in gribfiles[1:]])
    var2_forecast = np.stack([extract_param(file, var2) for file in gribfiles[1:]])
    #var3_forecast = np.stack([extract_param(file, var3) for file in gribfiles[1:]])

    x = var1_forecast.shape[1]
    y = var1_forecast.shape[2]
    var1_forecast = var1_forecast.reshape((1, 1, var1_forecast.shape[0], x, y))
    var2_forecast = var2_forecast.reshape((1, 1, var2_forecast.shape[0], x, y))
    #var3_forecast = var3_forecast.reshape((1, 1, var3_forecast.shape[0], x, y))

    # check if data has regular lat, lon grid
    # do lats change only in 0th dimension?
    lat0 = (lats[:, 0:1] * np.ones(lats.shape[1]) == lats).all()
    # do lons change only in 1st dimension?
    lon1 = (lons[0:1, :].T * np.ones(lons.shape[0]) == lons.T).all()


    data_variables = OrderedDict()
    coords = OrderedDict()
    if lat0 and lon1:
        dim_labels = ['date', 'time', 'step', 'latitude', 'longitude']
        coords['latitude'] =  lats[:, 0]
        coords['longitude'] = lons[0, :]
    else:
        dim_labels = ['date', 'time', 'step', 'x', 'y']
        coords['latitude'] =  (['x', 'y'], lats)
        coords['longitude'] = (['x', 'y'], lons)
    coords['date'] = [date]
    coords['time'] = [time]
    coords['step'] = pd.timedelta_range('3h', freq='3h', periods=var1_forecast.shape[2])

    data_variables[var1] = (dim_labels, var1_forecast)
    data_variables[var2] = (dim_labels, var2_forecast)
    #data_variables[var3] = (dim_labels, var3_forecast)
    ds = xr.Dataset(data_variables, coords=coords)
    ds.to_netcdf(outfilename)

def get_filenames(source):
    fns = glob.glob(os.path.join(source, "*.grb2"))
    fns.sort()

    df = pd.DataFrame()
    df["names"] = fns
    df['datetimes'] = df["names"].apply(
            lambda x: pd.Timestamp('{}T{}'.format(x[-22:-14], x[-13:-9])))

    return df

def filter_filenames(df, startdate, enddate, time):
    """Filter DataFrame of filenames by date and/or time, set parameters
    to None for no filtering.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with columns 'names' and 'datetimes'
    startdate : str / None
        Format should be convertible to pd.Timestamp
    enddate : str / None
        Format should be convertible to pd.Timestamp
    time : str / None
        Format should be convertible to pd.Timedelta

    Returns
    -------
    df : pd.DataFrame
        Filtered DataFrame
    """
    if startdate is not None:
        sd = pd.Timestamp(startdate)
        df = df[df['datetimes'].dt.floor('1d') >= sd]
    if enddate is not None:
        ed = pd.Timestamp(enddate)
        df = df[df['datetimes'].dt.floor('1d') <= ed]
    if time is not None:
        t = pd.Timedelta(time)
        df = df[df['datetimes']-df['datetimes'].dt.floor('1d') == t]
    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("sourcepath", help="source file path")
    parser.add_argument("outfilepath", help="output file path")
    parser.add_argument("-s", "--start", default=None,
                        help="Start date of files to convert")
    parser.add_argument("-e", "--end", default=None,
                        help="End date of files to convert")
    parser.add_argument("-t", "--time", default=None,
                        help="Time of day of files to convert")
    args = parser.parse_args()

    sourcepath = args.sourcepath
    outfilepath = args.outfilepath

    var1 = 'Downward short-wave radiation flux'
    var2 = '2 metre temperature'
    #var2 = 'Temperature'

    print(sourcepath)

    df = get_filenames(sourcepath)
    df = filter_filenames(df, startdate=args.start, enddate=args.end,
                          time=args.time)
    for dati in df.datetimes.unique():
        namelist = list(df[df.datetimes == dati]["names"])
        ncname = pd.Timestamp(dati).strftime("GFS_%Y%m%d_%H%M.nc")
        outfilename = os.path.join(outfilepath, ncname)
        print("processing ", dati, " using %d gribfiles" % (len(namelist)))
        try:
            convert_to_netcdf(namelist, outfilename, var1, var2)
        except Exception as err:
            print(err)


