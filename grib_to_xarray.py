#!/usr/bin/env python
# coding: utf-8

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
    with pygrib.open(filename) as grbs:
        grb = grbs.select(name = var)[0]
        data, lats, lons = grb.data()
    return data


def convert_to_netcdf(filepath, outfilepath,  var1, var2):
    gribfiles = glob.glob(os.path.join(filepath, "*grb2"))
    gribfiles.sort()
    
    
    grb = pygrib.open(gribfiles[1]).select(name = var1)[0]
    data, lats, lons = grb.data()
    date = datetime.datetime(year=grb.year, month=grb.month, day=grb.day, hour = 0)
    date = pd.Timestamp(date)
    time = date - date
    var1_forecast = np.stack([extract_param(file, var1) for file in gribfiles[1:]])
    var2_forecast = np.stack([extract_param(file, var2) for file in gribfiles[1:]])
    
    x = var1_forecast.shape[1]
    y = var1_forecast.shape[2]
    var1_forecast = var1_forecast.reshape((1, 1, var1_forecast.shape[0], x, y))
    var2_forecast = var2_forecast.reshape((1, 1, var2_forecast.shape[0], x, y))
    data_variables = OrderedDict()
    coords = OrderedDict()
    data_variables = OrderedDict()
    dim_labels = ['forecastdate', 'forecasttime', 'step', 'x', 'y', ]

    coords['latitude'] =  (['x', 'y'], lats)
    coords['longitude'] = (['x', 'y'], lons)
    coords['date'] = date
    coords['time'] = time
    coords['step'] = pd.timedelta_range('3h', freq='3h', periods = var1_forecast.shape[2])


    data_variables[var1] = (dim_labels, var1_forecast)
    data_variables[var2] = (dim_labels, var2_forecast)
    ds = xr.Dataset(data_variables, coords=coords)
    
    outfilename = os.path.join(os.path.join(outfilepath, str(date)[:10] + '_' + str(time)[7:] +".nc"))
    ds.to_netcdf(outfilename)


if __name__ == '__main__':
    
    if len(sys.argv) < 3:
        sys.exit("Use with %s <sourcefilepath> <outfilepath> <var1> <var2>" % sys.argv[0])
    
    sourcepath = sys.argv[1]
    outfilepath = sys.argv[2]
    var1 = sys.argv[3]
    var2 = sys.argv[4]
    convert_to_netcdf(sourcepath, outfilepath, var1, var2)
