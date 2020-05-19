"""
Script to download and store full, 'current' GDPS forecast.

Notes
-----

Since there are two new GDPS forecast per day, it is likely a good idea to have this
script run twice a day to get them.

This can e.g. be done using a cronjob i.e.

0 */12 * * * python get_current_gdps.py

"""
import download_gdps_grib

VAR = {"GHI": "DSWRF_SFC",
       "Wind speed": "WIND_TGL",
       "Wind direction": "WDIR_TGL",
       "Total cloud": "TCDC_SFC",
       "Temperature": "TMP_ISBL"
      }

LOCATIONLIST = {"Freiburg": (47.9990, 7.8421)}

URL = "https://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/"
GRIBDST = "path/to/gribfiles"
NCDST = "path/to/ncfiles"
RESULTDST = "path/to/resultfiles"

def get_current_forecast():
    """ Download current forecasts for all defined variables """
    for val in VAR.values():
        download_gdps_grib.main()


def convert_current_forecast():
    # PLACEHOLDER
    pass


def extract_current_forecast(locationlist):
    # PLACEHOLDER
    pass



def main():
    # Download grib files
    get_current_forecast()

    # Convert grib to netCDF.
    convert_current_forecast()

    # Extract relevant data for specified locations
    extract_current_forecast(LOCATIONLIST)

if __name__ == '__main__':
    main()
