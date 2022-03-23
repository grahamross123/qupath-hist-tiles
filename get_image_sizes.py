from src.Omero import Omero
from src.omero_credentials import USERNAME, PASSWORD, HOST
import pandas as pd
import json
import os
from tqdm import tqdm

# Run get_image_sizes.py to obtain a json file containing the width, height, number of rows and number of
# columns of each of the slides containing high confidence tiles in tiles.csv (output from sort_tiles.py)

PROJECT_ID = 355
PREDICTION_FOLDER = "/Users/rossg/Documents/HistSlideVis_data/models_pbrm1_bap1_no_whole_patient/omero_shufflenet_v2_x1_0_lr0.1_mag20_patch512x512_1/epoch_50_1634986138"
TILES_CSV_PATH = "/Users/rossg/Projects/qupath-hist-tiles/data/tiles.csv"
OUT_FILE = './data/slide_dims.json'


def get_dims(image_id, omero):
    image_object = omero.get_image_object(image_id)
    return [image_object.getSizeX(), image_object.getSizeY()]


def find_image_id(image_name, dataset_id, omero):
    images = omero.get_slides_from_dataset(dataset_id)
    for image in images:
        if image_name == image['name']:
            return image["id"]


def get_rows_cols(image_name, prediction_files):
    for prediction_file in prediction_files:
        if image_name in prediction_file:
            filepath = os.path.join(PREDICTION_FOLDER, prediction_file)
            prediction_df = pd.read_csv(filepath, sep='\t')
            nrows = len(prediction_df.axes[0]) + 1  # add one as first row should be included
            ncols = len(prediction_df.axes[1])
            return nrows, ncols
    print("file not found")


if __name__ == "__main__":
    omero = Omero(HOST, USERNAME, PASSWORD)
    omero.connect()
    omero.switch_user_group()

    prediction_files = sorted(os.listdir(PREDICTION_FOLDER))


    datasets = omero.get_datasets(PROJECT_ID)

    slides = pd.read_csv(TILES_CSV_PATH)
    slide_names = slides.slide_name.unique()

    slide_dims = {}
    for slide_name in tqdm(slide_names):
        for dataset in datasets:
            if dataset["name"] in slide_name:
                image_id = find_image_id(slide_name, dataset["id"], omero)
                nrows, ncols = get_rows_cols(slide_name, prediction_files)
                slide_dims[slide_name] = {
                    "size": get_dims(image_id, omero),
                    "nrows": nrows,
                    "ncols": ncols}

    with open(OUT_FILE, 'w') as fp:
        json.dump(slide_dims, fp)
    omero.disconnect()
