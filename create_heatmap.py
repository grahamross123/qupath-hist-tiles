import json
import math
from src.util import read_predictions, coords_to_corner_pixels, prob2rgb, create_json_tile, create_json_tile_heatmap

# Creates a heatmap of annotations for a given slide and prediction tsv file.
# For earlier predictions, use slide_dims json file to obtain tile size.


TILE_SIZE = [1024, 1024]
PREDICTION_FILE = "/Users/rossg/Documents/HistSlideVis_data/predictions_new_best/K177_PR002.ome_PBRM1.tsv"
OUTPATH = "output/heatmap.json"
SLIDE_INFO = {"size": [141471, 128612], "nrows": 126, "ncols": 139}


if __name__ == '__main__':
    json_objects = []

    # get slide size, nrows and ncols for the current tile
    nrows = SLIDE_INFO["nrows"]
    ncols = SLIDE_INFO["ncols"]
    slide_size = SLIDE_INFO["size"]
    tile_size = [slide_size[0] / ncols, slide_size[1] / nrows]
    print(tile_size)

    # Read entire output csv
    predictions = read_predictions(PREDICTION_FILE)

    for i in range(len(predictions)):
        for j in range(len(predictions[i])):
            pred = float(predictions[i][j])

            # Skip NaN values
            if math.isnan(pred):
                continue

            json_objects.append(create_json_tile_heatmap([j, i], tile_size, colour=prob2rgb(pred)))

    with open(OUTPATH, 'w') as outfile:
        json.dump(json_objects, outfile)
