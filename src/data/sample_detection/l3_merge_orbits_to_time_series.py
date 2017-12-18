import os
import glob
import logging
import re
from collections import defaultdict

import pandas as pd

import src.config.filepaths as fp

def main():

    csv_filepaths = glob.glob(fp.path_to_cems_output_l2 + '*/*/*/*/*_sampling.csv')
    
    # filter the csv filepaths to process
    csv_filepaths = [f for f in csv_filepaths if not re.search(r'at2/2002/[0][5-9]/', f)]
    csv_filepaths = [f for f in csv_filepaths if not re.search(r'at2/2002/[1][0-2]/', f)]
    csv_filepaths = [f for f in csv_filepaths if not re.search(r'at2/2003/*/', f)]
    csv_filepaths = [f for f in csv_filepaths if not re.search(r'at1/199[6-7]/*/', f)]
    csv_filepaths = [f for f in csv_filepaths if not re.search(r'at1/1995/[0][6-9]/', f)]
    csv_filepaths = [f for f in csv_filepaths if not re.search(r'at1/1995/[1][0-2]/', f)]

    sample_counter = defaultdict(int)
    cloud_free_counts = defaultdict(int)
    flare_counts = defaultdict(int)
    lats = defaultdict(float)
    lons = defaultdict(float)

    # now lets get count the samples
    for f in csv_filepaths:
        try:
            sample_df = pd.read_csv(f)

            for index, row in sample_df.iterrows():
                sample_counter[row.flare_ids] += 1
                lats[row.flare_ids] = row.matched_lats
                lons[row.flare_ids] = row.matched_lons
                if row.obs_types == 2:
                    cloud_free_counts[row.flare_ids] += 1
                if row.obs_types == 1:
                    flare_counts[row.flare_ids] += 1

        except Exception, e:
            logger.warning('Could not load csv file with error: ' + str(e))

    out_df = pd.DataFrame({"sample_counts": sample_counter,
                           "cloud_free_counts": cloud_free_counts,
                           "flare_counts": flare_counts,
                           "sample_lats": lats,
                           "sample_lons": lons})

    # dump to csv
    if not os.path.exists(os.path.join(fp.path_to_cems_output_l3, 'all_sensors')):
        os.makedirs(os.path.join(fp.path_to_cems_output_l3, 'all_sensors'))

    out_df.to_csv(os.path.join(fp.path_to_cems_output_l3, 'all_sensors', 'all_sampling.csv'))


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    logger = logging.getLogger(__name__)
    main()