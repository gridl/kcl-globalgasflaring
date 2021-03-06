#!/home/users/dnfisher/soft/virtual_envs/ggf/bin/python2

"""
Merge gas flare detections to monthly samples .
The first step in the algorithm is to reduce the resolution of the data:
1. Iterate over all detection files,
2. Adjust the lats, lons to the specified resolution
3. Reduce the flares based on the adjusted lats and lons, taking the mean.
4. Append the reduced flares to the dataframe
This dataframe will give all the monthly observations.  We need to take the mean for the
orbit, as this will give a proper representation of the flare over the cluster.
The second step in the algorithm is to aggregate the reduced resolution data to monthly
2. Append a counter to the dataframe
3. Reduce by lats and lons, taking the median frp, and the count, also record lats and lons.
 Taking the median over the month is better as we can assume that the flare burns consistently
 and that the majority of changes are caused by variation in cloud cover.  Taking the median
 will give the cloud free result assuming there is optically thin cloud < 60% of the time.
"""

import os
import glob
import logging

import pandas as pd
import numpy as np

import src.config.filepaths as fp


def select_csv_files_for_month(sensor, year, month):
    return glob.glob(os.path.join(fp.path_to_cems_output_l2, sensor, year, month, "*", "*_hotspots.csv"))


def get_arcmin(x):
    '''
    rounds the data decimal fraction of a degree
    to the nearest arc minute
    '''
    neg_values = x < 0

    abs_x = np.abs(x)
    floor_x = np.floor(abs_x)
    decile = abs_x - floor_x
    minute = np.around(decile * 60)  # round to nearest arcmin
    minute_fraction = minute*0.01  # convert to fractional value (ranges from 0 to 0.6)

    max_minute = minute_fraction > 0.59

    floor_x[neg_values] *= -1
    floor_x[neg_values] -= minute_fraction[neg_values]
    floor_x[~neg_values] += minute_fraction[~neg_values]
    
    # deal with edge cases, and just round them all up
    if np.sum(max_minute) > 0:
        floor_x[max_minute] = np.around(floor_x[max_minute])

    # now to get rid of rounding errors and allow comparison multiply by 100 and convert to int
    floor_x = (floor_x * 100).astype(int)

    return floor_x


def myround(x, dec=20, base=.000005):
    return np.round(base * np.round(x / base), dec)


def generate_month_df(csv_files_for_month, resolution):
    month_flares = []
    for f in csv_files_for_month:
        try:
            orbit_df = pd.read_csv(f, usecols=['lats', 'lons'], dtype={'lats': float, 'lons': float})
            orbit_df['lons_arcmin'] = get_arcmin(orbit_df['lons'].values)
            orbit_df['lats_arcmin'] = get_arcmin(orbit_df['lats'].values)
            orbit_df['lons'] = myround(orbit_df['lons'].values, base=resolution)
            orbit_df['lats'] = myround(orbit_df['lats'].values, base=resolution)
            # keep only unique flaring locations seen in the orbit
            orbit_df.drop_duplicates(subset=['lats_arcmin', 'lons_arcmin'], inplace=True)
            month_flares.append(orbit_df)
        except Exception, e:
            logger.warning('Could not load csv ' + f + ' file with error: ' + str(e))
    print orbit_df.head()
    return pd.concat(month_flares, ignore_index=True)


def unique_month_locations(month_df):
    # keep only unique flaring locations seen in the month
    month_df.drop_duplicates(subset=['lats_arcmin', 'lons_arcmin'], inplace=True)


def main():
    # aggregation resolution
    resolution = 60. / 3600  # arseconds ~2km

    for sensor in ['sls']:
        year_dir = os.path.join(fp.path_to_cems_output_l2, sensor)
        years = os.listdir(year_dir)
        for year in years:
            month_dir = os.path.join(year_dir, year)
            months = os.listdir(month_dir)
            for month in months:
                csv_files_for_month = select_csv_files_for_month(sensor, year, month)
                try:
                    month_df = generate_month_df(csv_files_for_month, resolution)
                    unique_month_locations(month_df)
                    # dump to csv
                    path_to_out = os.path.join(fp.path_to_cems_output_l3, sensor, year)
                    if not os.path.exists(path_to_out):
                        os.makedirs(path_to_out)
                    month_df.to_csv(os.path.join(path_to_out, month + '.csv'), index=False)
                except Exception, e:
                    print 'failed with error', e
                    continue

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.ERROR, format=log_fmt)
    logger = logging.getLogger(__name__)
    main()
