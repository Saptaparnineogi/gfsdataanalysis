#!/usr/bin/env python
# coding: utf-8

# Script to extract 'Downward short-wave radiation flux' and 'Temperature' from grib files and to generate netcdf files for each forecast


import os
import os.path
import requests
from bs4 import BeautifulSoup
import pygrib
import tarfile
import pandas as pd
import numpy as np
import datetime
import glob
import matplotlib.pyplot as plt
from pylab import rcParams
import xarray as xr
import itertools
from collections import OrderedDict
import sys


def extract_param(filename, var):
    '''
    extract specified parameters from grib files and return it as an array
    '''
    try:
        with pygrib.open(filename) as grbs:
            grb = grbs.select(name = var)[0]
            data, lats, lons = grb.data()
        return data
    except ValueError: # This wont work, even if the exception is caught, the function now returns None.
        print("Parameter not found: {}".format(var))


def convert_to_netcdf(files, outfilepath,  var1, var2):

    '''
    Fetch var1 and var2 from grib files and converts it to netcdf file
    -----------------------------------

    filepath: complete path of grib file
    outfilepath: path to store the netcdf files
    var1: Downward short-wave radiation flux
    var2: Temperature

    '''
    gribfiles = files #glob.glob(os.path.join(filepath, "*grb2"))
    gribfiles.sort()

    grb = pygrib.open(gribfiles[1]).select(name = var1)[0]
    data, lats, lons = grb.data()
    date = datetime.datetime(year=grb.year, month=grb.month, day=grb.day, hour = 0)
    date = pd.Timestamp(date)
    time = date - date
    var1_forecast = np.stack([extract_param(file, var1) for file in gribfiles[1:]])
    var2_forecast = np.stack([extract_param(file, var2) for file in gribfiles[1:]])
    #var3_forecast = np.stack([extract_param(file, var3) for file in gribfiles[1:]])

    x = var1_forecast.shape[1]
    y = var1_forecast.shape[2]
    var1_forecast = var1_forecast.reshape((1, 1, var1_forecast.shape[0], x, y))
    var2_forecast = var2_forecast.reshape((1, 1, var2_forecast.shape[0], x, y))
    #var3_forecast = var3_forecast.reshape((1, 1, var3_forecast.shape[0], x, y))


    data_variables = OrderedDict()
    coords = OrderedDict()
    data_variables = OrderedDict()
    dim_labels = ['date', 'time', 'step', 'x', 'y', ]

    coords['latitude'] =  (['x', 'y'], lats)
    coords['longitude'] = (['x', 'y'], lons)
    coords['date'] = [date]
    coords['time'] = [time]
    coords['step'] = pd.timedelta_range('3h', freq='3h', periods = var1_forecast.shape[2])


    data_variables[var1] = (dim_labels, var1_forecast)
    data_variables[var2] = (dim_labels, var2_forecast)
    #data_variables[var3] = (dim_labels, var3_forecast)
    ds = xr.Dataset(data_variables, coords=coords)
    #start = gribfiles[0].find('gfs_')
    #end = start + 19
    #outfilename = os.path.join(os.path.join(outfilepath, gribfiles[0][start:end] +".nc"))
    #print(outfilename)
    ds.to_netcdf(outfilepath)

def get_filenames(source):
    fns = glob.glob(os.path.join(source, "*.grb2"))
    fns.sort()

    df = pd.DataFrame()
    df["names"] = fns
    df["dates"] = df["names"].apply(lambda x : pd.Timestamp(x[-22:-14]))

    return df

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Use with %s <source file path> <output file path>" % sys.argv[0])

    sourcepath = sys.argv[1]
    outfilepath = sys.argv[2]

    var1 = 'Downward short-wave radiation flux'
    var2 = 'Temperature'
    print(sourcepath)
    #for i in range(1, 31):
    #    files = glob.glob(os.path.join(sourcepath, "gfs_3_2020*{}_*.grb2".format(i)))
    #    print(os.path.join(sourcepath, "gfs_3_2020*{}_*.grb2".format(i)))
    #    if len(files) != 0:
    #        print(files[0])
    #        convert_to_netcdf(files, outfilepath, var1, var2)
    #        break
    df = get_filenames(sourcepath)
    for date in df.dates.unique():
        namelist = list(df[df.dates == date]["names"])
        ncname = pd.Timestamp(date).strftime("GFS_%Y%m%d_000.nc")
        outfilename = os.path.join(outfilepath, ncname)
        print("processing ", date, " using %d gribfiles" % (len(namelist)))
        try:
            convert_to_netcdf(namelist, outfilename, var1, var2)
        except Exception as err:
            print(err)


