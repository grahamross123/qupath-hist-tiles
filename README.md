# QuPath Histology Tiles

This repo contains the scripts to search through the output TSV files from the DeepHiPa pipeline and create annotation geojson files containing the highest confidence tiles.
It also includes a script to convert a TSV prediction file into a heatmap which can be imported into QuPath.

## Usage
### High confidence tiles
1. Run `sort_tiles.py` to obtain a csv with a list of the highest confidence tiles from a specified folder of TSV files from the model.
2. Run `get_images_sizes.py` to obtain a json file containing the width and height of each slide and the number of rows and columns in the TSV file for that slide.
3. Run `create_top_tiles.py` to obtain a json file for each slide containing the annotation info for the highest confidence tiles.
4. In QuPath, run the `qupath_scripts/import_all_tiles.groovy` script as a batch process for all images in the project to import the correct annotations for each image.

### Heatmap
1. Run `create_heatmap.py` to create a json file containing the annotations for a single output TSV file from the model.
2. In QuPath, open the correct image and run the `qupath_scripts/import_annotations.groovy` script (or drag and drop the json file into the viewer) to import the heatmap.
