#!/usr/bin/env python
# coding: utf-8

import sys
import os
import os.path
import pygrib
import pandas as pd
import numpy as np
import datetime
import re
import glob
from pylab import rcParams
import xarray as xr
import pygrib
from collections import OrderedDict

VAR = {"GHI": "DSWRF_SFC",
       "Wind speed": "WIND_TGL",
       "Wind direction": "WDIR_TGL",
       "Total cloud": "TCDC_SFC",
       "Temperature": "TMP_ISBL"}


def get_filenames(source):
    '''
    Create filenames for GDPS forecast files

    Parameters
    --------------------------------------
    source: path to grib files
    '''
    fns = glob.glob(os.path.join(source, "CMC_*.grib2"))
    fns.sort()
    df = pd.DataFrame()
    df["names"] = fns
    df["dates"] = df["names"].apply(lambda x: pd.Timestamp(x[-21:-13]))
    return df


def extract_param(filename):
    '''
    Extract parameters from grib files and return it as an array.
    Note:
    ------
    As for GDPS there is only one variable in each file,
    so we don't need to specify the variable name here.
    '''
    try:
        with pygrib.open(filename) as grbs:
            grb = grbs.select()[0]
            data, lats, lons = grb.data()
        return data
    except ValueError:
        print("Parameter not found: {}".format(filename))


def convert_to_netcdf(files, outfilepath):

    '''
    This function convert grib files to netcdf file
    for GDPS data.
    GDPS is generating different grib files for different variables,
    this function creates single netcdf file with all required
    vriables for one GDPS forecast.

    Parameter:
    -----------------------------------

    files: path to grib files
    outfilepath: path to store the netcdf files

    '''

    gribfiles = files
    gribfiles.sort()
    data_variables = OrderedDict()
    coords = OrderedDict()
    ghi_dims = ['forecastdate', 'forecasttime', 'step_ghi', 'x', 'y']
    cloud_dims = ['forecastdate', 'forecasttime', 'step_cloud', 'x', 'y']
    temp_dims = ['forecastdate', 'forecasttime', 'step_temp', 'air_pressure', 'x', 'y']
    wind_dims = ['forecastdate', 'forecasttime', 'step_wind', 'ground_level', 'x', 'y']
    g_level = set()
    pressure_mb = set()
    for v in VAR.values():
        var_files = [file for file in gribfiles if v in file]
        if len(var_files) != 0:
            grb = pygrib.open(var_files[1]).select()[0]
            data, lats, lons = grb.data()
            date = datetime.datetime(year=grb.year, month=grb.month, day=grb.day, hour=0)
            date = pd.Timestamp(date)
            time = date - date
            start = str(grb).find(':')
            end = str(grb).find(':', str(grb).find(":") + 1)
            coords['latitude'] = (['x', 'y'], lats)
            coords['longitude'] = (['x', 'y'], lons)
            coords['date'] = date
            coords['time'] = time
            if v == "DSWRF_SFC":
                var = str(grb)[start + 1:end]
                forecast = np.stack([extract_param(f) for f in var_files[0:]])
                x = forecast.shape[1]
                y = forecast.shape[2]
                forecast = forecast.reshape((1, 1, forecast.shape[0], x, y))
                coords['step_ghi'] = pd.timedelta_range('3h', freq='3h', periods=forecast.shape[2])
                data_variables[var] = (ghi_dims, forecast)
            elif v == "TCDC_SFC":
                var = str(grb)[start + 1:end]
                forecast = np.stack([extract_param(f) for f in var_files[0:]])
                x = forecast.shape[1]
                y = forecast.shape[2]
                forecast = forecast.reshape((1, 1, forecast.shape[0], x, y))
                coords['step_cloud'] = pd.timedelta_range('0h', freq='3h', periods=forecast.shape[2])
                data_variables[var] = (cloud_dims, forecast)
            elif v == 'TMP_ISBL':
                pressure_mb = set()
                var = str(grb)[start+1:end]
                for f in var_files:
                    pressure_mb.add(int(f.split('_')[4]))
                pressure_mb = list(pressure_mb)
                forecast = np.stack([extract_param(f) for f in var_files[0:]])
                x = forecast.shape[1]
                y = forecast.shape[2]
                print(forecast.shape)
                forecast = forecast.reshape((1, 1, forecast.shape[0]//len(pressure_mb), len(pressure_mb), x, y))
                coords['air_pressure'] = pressure_mb
                coords['step_temp'] = pd.timedelta_range('0h', freq='3h', periods=forecast.shape[2])
                data_variables[var] = (temp_dims, forecast)
            elif v == 'WIND_TGL':
                var = str(grb)[start + 10:end]
                for f in var_files:
                    g_level.add(int(f.split('_')[4]))
                g_level = list(g_level)
                forecast = np.stack([extract_param(f) for f in var_files[0:]])
                x = forecast.shape[1]
                y = forecast.shape[2]
                forecast = forecast.reshape((1, 1, forecast.shape[0] // len(g_level), len(g_level), x, y))
                coords['ground_level'] = g_level
                coords['step_wind'] = pd.timedelta_range('0h', freq='3h', periods=forecast.shape[2])
                data_variables[var] = (wind_dims, forecast)
            elif v == 'WDIR_TGL':
                var = str(grb)[start + 10:end]
                forecast = np.stack([extract_param(f) for f in var_files[0:]])
                x = forecast.shape[1]
                y = forecast.shape[2]
                forecast = forecast.reshape((1, 1, forecast.shape[0] // len(g_level), len(g_level), x, y))
                coords['step_wind'] = pd.timedelta_range('0h', freq='3h', periods=forecast.shape[2])
                data_variables[var] = (wind_dims, forecast)
    ds = xr.Dataset(data_variables, coords=coords)
    print(ds)
    print(outfilepath)
    ds.to_netcdf(outfilepath)


def main(sourcepath, outfilepath):
    df = get_filenames(sourcepath)
    for date in df.dates.unique():
        namelist = list(df[df.dates == date]["names"])
        ncname = pd.Timestamp(date).strftime("CMC_%Y%m%d_00.nc")
        outfilename = os.path.join(outfilepath, ncname)
        print("processing ", date, " using %d gribfiles" % (len(namelist)))
        try:
            convert_to_netcdf(namelist, outfilename)
        except Exception as err:
            print(err)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit("Use with %s <source path> <target path>" % sys.argv[0])
    sourcepath = sys.argv[1]
    outfilepath = sys.argv[2]
    main(sourcepath, outfilepath)
