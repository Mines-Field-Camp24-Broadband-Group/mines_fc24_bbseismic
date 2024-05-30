#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 16:44:59 2019

@author: echon

"""
import sys
import os
from datetime import datetime as dt
import obspy
from obspy.clients.fdsn.mass_downloader import RectangularDomain, \
    Restrictions, MassDownloader    

def getData(start,outfile,day_index):    
    # Rectangular domain 
    domain = RectangularDomain(minlatitude=34.00, maxlatitude=36.58,
                               minlongitude=-100.00, maxlongitude=-94.28)
    
    restrictions = Restrictions(
        # Get data for a range of dates.
        starttime=obspy.UTCDateTime(start),
        endtime=obspy.UTCDateTime(start)+86400,
    #    starttime=obspy.UTCDateTime(2018, 11, 29),
    #    endtime=obspy.UTCDateTime(2018, 11, 30),
        
        # Chunk it to have two files per day.
        chunklength_in_sec=86400/4,
        
        # Considering the enormous amount of data associated with continuous
        # requests, you might want to limit the data based on SEED identifiers.
        # If the location code is specified, the location priority list is not
        # used; the same is true for the channel argument and priority list.
        #network="TA,AK,AT,AV,PN", station="*", location="", channel="BH?",
        #network="XU", station="*", #location="", 
        ##network="PN", station="*", location="",
        #channel="BH?,CH?,EH?,HH?",
        #channel_priorities=('HH[ZNE12]', 'BH[ZNE12]', 'SH[ZNE12]'), 
        #network="TA,AK,AT,AV,PN", station="*", location="", channel="BH?,EH?,HH?,SH?",
    
    
        # The typical use case for such a data set are noise correlations where
        # gaps are dealt with at a later stage.
        reject_channels_with_gaps=False,
        # Same is true with the minimum length. All data might be useful.
        minimum_length=0.0,
        # Guard against the same station having different names.
        minimum_interstation_distance_in_m=100.0)
    
    # Restrict the number of providers if you know which serve the desired
    # data. If in doubt just don't specify - then all providers will be
    # queried.
    mdl = MassDownloader(providers=["IRIS"])
    write_tf=os.path.join(outfile,'waveforms'+'{:s}'.format(day_index))
    write_ts=os.path.join(write_tf,'stations'+'{:s}'.format(day_index))
    mdl.download(domain, restrictions, mseed_storage=write_tf,
                 threads_per_client=3, stationxml_storage=write_ts)
    return

def datenum(d):
    # Returns a datenum, equivalent to the MATLAB function datenum
    # Input is output format of python function datenum.strptime
    return 366 + d.toordinal() \
    + (d - dt.fromordinal(d.toordinal())).total_seconds()/(24*60*60)

#d = dt.strptime(d_str,'%Y-%m-%d')
#dn = datenum(d)

out=os.path.join('../data/','oklahoma_eqs_5-30')

    
for n in range(1,91):
    i = n
    ii=str(i)
    dayMult=i*86400
    #day=dt.strptime('2018-11-01','%Y-%m-%d')
    #day=datenum(day)+dayMult
    day=obspy.UTCDateTime(2024,5,29)+dayMult
    getData(day,out,ii)