import json
from src.util import coords_to_corner_pixels, read_tile_csv, create_json_tile
import os
from tqdm import tqdm

# Given a path to slide_dims.json containing slide sizes and a tiles.csv file containing a list of top tiles,
# create a geojson for each slide containing annotation info with high confidence tiles.
# Currently, tiles sizes are slightly different than expected (i.e. not equal to (source_mag / target_mag) * tile_size
# This is fixed for newer predictions, but for old predictions use slide_dims.json to obtain tile size.

TILE_SIZE = [1024, 1024]
OUTFOLDER = "./output/high_confidence_tiles/"
TILES_CSV = "/Users/rossg/Projects/qupath-hist-tiles/data/tiles.csv"
SLIDE_DIMS_FILE = './data/slide_dims.json'


if __name__ == '__main__':
    with open(SLIDE_DIMS_FILE, 'r') as f:
        slide_dims = json.load(f)

    tile_annotations = {}
    # Read list of the highest confidence tiles
    tiles = read_tile_csv(TILES_CSV)
    for tile in tqdm(tiles):

        # get slide size, nrows and ncols for the current tile
        slide_info = slide_dims[tile["slide_name"]]
        nrows = slide_info["nrows"]
        ncols = slide_info["ncols"]
        slide_size = slide_info["size"]
        tile_size = [slide_size[0] / ncols, slide_size[1] / nrows]

        name_string = f"{tile['mutation']}_{'mt' if tile['prediction'] else 'wt'}_{float(tile['confidence']):.2f}_{'correct' if float(tile['prediction']) == float(tile['ground_truth']) else 'incorrect'}"
        tile_data = create_json_tile(
            tile["coords"],
            tile_size,
            name=name_string,
            prediction=0 if float(tile["output"]) < 0.5 else 1,
            confidence=float(tile["confidence"]),
            class_name="Top " + tile["mutation"] + " tiles",
            accuracy=0 if float(tile["prediction"]) == float(tile["ground_truth"]) else 1
            )

        if tile["slide_name"] in tile_annotations:
            tile_annotations[tile["slide_name"]].append(tile_data)
        else:
            tile_annotations[tile["slide_name"]] = [tile_data]

    # Clear the output folder
    for file in os.listdir(OUTFOLDER):
        os.unlink(os.path.join(OUTFOLDER, file))

    # Save the new files
    for file in tile_annotations:
        with open(OUTFOLDER + file + ".json", 'w') as outfile:
            json.dump(tile_annotations[file], outfile)
