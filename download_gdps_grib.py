import sys
import os
from os.path import join, dirname
import requests
from bs4 import BeautifulSoup
import re
import yaml

with open(join(dirname(__file__), "config.yml"), "r") as yfile:
    CFG = yaml.load(yfile, Loader=yaml.FullLoader)

def listFD(url):
    '''
    This function fetches the folders in the given url.
    Here we are fetching data from canadian weather forecast model.
    Returns a python list with all the folder names.

    Parameters:
    --------------------
    url: url of the webpage, we want to fetch data from (string)

    '''
    folders = []
    page = requests.get(url, proxies=CFG["proxies"]).text
    soup = BeautifulSoup(page, 'html.parser')
    for node in soup.find_all('a'):
        if node.get('href')[0].isdigit():
            folders.append(node.get('href'))
    return folders


def get_file_links(url, var):
    '''
    Get the links of the file from the mention url and variable name.
    For canadian weather forcast model weather forecast for different
    parameters are saved in different files.
    We can specify the variable names, we want to download.

    Parameters:
    -----------------------------
    url: url of the webpage(string)
    var: Variable we want to download data for (string)

    '''
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html')
    links = soup.findAll('a')
    new_link = []
    for link in links:
        if re.search(var, link['href']):
                new_link.append(link)
    file_links = [url + link['href'] for link in new_link
                  if link['href'].endswith('.grib2')]
    return file_links


def download_grib_files(file_link, dest_path):
    '''
    Downloads grib file and save it in mentioned folder

    Parameters:
    -------------------------
    file_link: string
    dest_path: string
    '''
    if not os.path.exists(dest_path):
        os.mkdir(dest_path)

    for link in file_link:

        '''
        iterate through all links
        and download them one by one
        '''

        # obtain filename by splitting url and getting
        # last string
        file_name = link.split('/')[-1]
        target_path = os.path.join(dest_path, file_name)
        # create response object
        r = requests.get(link, stream=True)
        with open(target_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    return

def main(url, file_destination, var):
    runs = ['00/', '12/']
    for r in runs:
        fd = listFD(os.path.join(url, r))
        for f in fd:
            filepath = os.path.join(url, r, f)
            filelinks = get_file_links(filepath, var)
            download_grib_files(filelinks, file_destination)



if __name__ == '__main__':
    '''
    We pass the source url, destination url and the
    variable we want to download from command line
    Model runs start at 00 and 12 UTC hours

    Notes:
    --------------------
    gdps url: https://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/

    Names of the variables we want to download as per GDPS:

    GHI: DSWRF_SFC
    Wind speed: WIND_TGL
    Wind direction: WDIR_TGL
    Total cloud: TCDC_SFC
    Temperature: TMP_ISBL

    Complete list of variables are avilable here-
    https://weather.gc.ca/grib/GLB_HR/GLB_latlonp24xp24_P000_deterministic_e.html
    '''

    if len(sys.argv) < 4:
        sys.exit("Use with %s <url> <target path> <variable>" % sys.argv[0])
    #url = sys.argv[1]
    url = CFG["url"]["gdps"]
    file_destination = sys.argv[2]
    var = sys.argv[3]
    main(url, file_destination, var)
