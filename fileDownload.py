#!/usr/bin/env python
# coding: utf-8

import os
import os.path
import requests 
from bs4 import BeautifulSoup 
import pygrib
import tarfile
from pvlib.forecast import GFS
import pandas as pd
import numpy as np
import datetime
from pvlib.location import Location
import glob
import matplotlib.pyplot as plt
from pylab import rcParams



def get_file_links(url): 
      
    # create response object 
    r = requests.get(url) 
    # create beautiful-soup object 
    soup = BeautifulSoup(r.content,'html')  
    # find all links on web-page 
    links = soup.findAll('a') 
    # filter the link sending with .grb2
    tar_links = [url + link['href'] for link in links if link['href'].endswith('.tar')] 
    return tar_links

def download_tar_files(file_link, dest_path): 
    
    try:
        os.mkdir(dest_path)
    except OSError:
        print ("Path %s already exists" % dest_path)
    else:
        print ("Successfully created the directory %s " % dest_path)
  
    for link in file_link: 
  
        '''iterate through all links in video_links 
        and download them one by one'''  
        # obtain filename by splitting url and getting  
        # last string     
        file_name = link.split('/')[-1]    
        target_path = os.path.join(dest_path, file_name)
          
        # create response object 
        r = requests.get(link, stream = True) 
          
        # download started 
        with open(target_path, 'wb') as f: 
            for chunk in r.iter_content(chunk_size = 1024*1024): 
                if chunk: 
                    f.write(chunk)  
  
    print("All files are downloaded!")
    return

def extract_grib_files(dir_name, file_ext):

    for item in os.listdir(dir_name): # loop through items in dir
        if item.endswith(file_ext): # check for ".zip" extension
            file_name = item # get full path of files
            print(file_name)
            tar=tarfile.open(os.path.join(dir_name, file_name))
            tar.extractall(dir_name)
            tar.close()
            os.remove(os.path.join(dir_name,file_name))
            
            
def grib_to_df(filename, location, var, var2):
    '''
    Converts grib data to dataframe for given location
    
    Parameters
    -------------------------------------------------
    filename: complete path of grib file
    location: bounding box of the location you are looking for
    '''
    lat1 = location[0]
    lat2 = location[2]
    lon1 = location[1]
    lon2 = location[3]
    
    grbs = pygrib.open(filename)
    
    try:
        with pygrib.open(filename) as grbs:
            grb = grbs.select(name=var)[0]
            data, lats, lons = grb.data(lat1=lat1, lat2=lat2, lon1=lon1, lon2=lon2)
            data_flat = np.reshape(data, (np.product(data.shape),))
            
            grb_2 = grbs.select(name=var2)[0]
            data2 = grb_2.data(lat1=lat1, lat2=lat2, lon1=lon1, lon2=lon2)[0]
            data2_flat = np.reshape(data2, (np.product(data2.shape),))
            
            lats_flat = np.reshape(lats, (np.product(lats.shape),))
            lons_flat = np.reshape(lons, (np.product(lons.shape),))
            
            #datetime1 = pd.to_datetime("%d0%d0%d 0"  str(data.year)+str('0')+str(data.month)+str('0') + str(data.day)+str(' 0')+str(data.hour))
            
            name2step = lambda name :pd.Timedelta(hours=int(name[-8:-5]))
            base = datetime.datetime(year=grb.year, month=grb.month, day=grb.day, hour=grb.hour)
            valid = base + name2step(filename)
            
            df = pd.DataFrame({'validtime': valid,
                               'basetime': base,
                               'latitude': lats_flat,
                               'longitude': lons_flat,
                                var:data_flat,
                                var2: data2_flat})
            #df['datetime'] = pd.to_datetime(df['datetime'], format='%m/%d/%Y %I:%M:%S %p')
            return df

    except ValueError:
        	print("Parameter not found: {}".format(filename))  
        
def convert_tar_to_csv(sourcepath, destinationpath, filename, location):
    files = glob.glob(os.path.join(sourcepath, "*grb2"))
    files.sort()
    outfile = glob.glob(os.path.join(destinationpath, filename))
    dflist = [grib_to_df(file, location, "Downward short-wave radiation flux", "Temperature") for file in files]
    df = pd.concat(dflist).set_index("validtime")
    df.to_csv(outfile, index=False)
    for file in files:
        os.remove(file)


if __name__ == '__main__':    
    url = "https://www1.ncdc.noaa.gov/pub/has/model/HAS011478636/"
    grb_filepath = '/home/saptaparni/gfsdata/'
    tar_links = get_file_links(url)
    download_tar_files(tar_links, grb_filepath)
    extract_grib_files(grb_filepath, '.tar')
    
    # bounding box of the location for which you want to get GHI values
    #location = [48,8,48.1,8]
    # csv file name format: <YYYY_STARTMONTH_ENDMONTH.csv>
    #filename = '2018_01_03.csv'
    # file path to save the csv files
    #csv_filepath = '/scratch/data/gfscsvfiles/'
    #convert_tar_to_csv(grb_filepath, csv_filepath, filename)
    
