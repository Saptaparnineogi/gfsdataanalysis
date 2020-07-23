## These python scripts are developed as a part of my work at Fraunhofer ISE

The scripts can be used to download and convert weather forecast data from two sources. We are dealing with GFS weather forecast system (used in USA) and GDPS weather forecast system (used in Canada).
Weather forecast data comes in grib file format, so preprocessing of those data was a major part of this task. I have written the scripts to download the files automatically from server and also to convert the data from grib files to easily interpretable NETCDF files.

### Running the scripts

Download gfs data from noaa. Use with:

```
$ python fileDownload.py https://www1.ncdc.noaa.gov/pub/has/model/*YOUR_ID*/ path/to/files/
```

Convert downloaded grib files to netcdf files

```
$ python3 grib_to_xarray.py path/to/source/files /path/tp/output/files/
```
Download weather forecast data from GDPS. Use with:
```
$ python3 download_gdps_grib.py https://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon <file destination> <variable>
```
Convert downloaded grib files from GDPS to netcdf files

```
$ python3 convert_gdps_xarray.py path/to/source/files /path/tp/output/files/
```


