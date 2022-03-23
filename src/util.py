import csv


def read_predictions(path):
    predictions = []
    with open(path, newline='') as f:
        read_tsv = csv.reader(f, delimiter="\t")
        for row in read_tsv:
            for i in range(len(row)):
                if row[i] != "nan":
                    row[i] = float(row[i])
                    row[i] = min(1, row[i])
                    row[i] = max(0, row[i])
            predictions.append(row)
    return predictions


def coords_to_corner_pixels(coords, tile_size):
    """Converts the integer coordinates to pixel coords at the four corners of the tile"""
    tl = [coords[0] * tile_size[0], coords[1] * tile_size[1]]
    tr = [tl[0] + tile_size[0], tl[1]]
    bl = [tl[0], tl[1] + tile_size[1]]
    br = [int(tl[0]) + int(tile_size[0]), int(tl[1]) + int(tile_size[1])]
    return tl, tr, bl, br


def read_tile_csv(filename):
    # Read tiles csv into an array of dicts
    tiles = []
    with open(filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # skip the column names
        for row in csvreader:
            tile = {"name": row[0], "confidence": row[1], "output": row[2],  "mutation": row[3], "prediction": row[4],
                    "coords": [int(row[5]), int(row[6])]}
            tiles.append(tile)
    return tiles


def prob2rgb(prob):
    if prob < 0.5:
        colour = prob * 2 * 255
        colour = min(255, colour)
        return [colour, colour, 255]
    else:
        colour = (1 - prob) * 2 * 255
        colour = min(255, colour)
        return [255, colour, colour]





def create_json_tile_heatmap(coords, tile_size, colour=None):
    # Create a json object with all the ROI info
    tl, tr, bl, br = coords_to_corner_pixels(coords, tile_size)
    json_object = {
        "type": "Feature",
        "id": "PathAnnotationObject",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    tl,
                    tr,
                    br,
                    bl,
                    tl,
                ]
            ]
        },
        "properties": {
            "isLocked": True,
            "color": colour,
        }
    }
    return json_object




def create_json_tile(coords, tile_size, name="tile", prediction="NA", confidence="NA", class_name="Other"):
    """Creates a json object with all the ROI info in a geojson format"""
    tl, tr, bl, br = coords_to_corner_pixels(coords, tile_size)
    json_object = {
        "type": "Feature",
        "id": "PathAnnotationObject",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    tl,
                    tr,
                    br,
                    bl,
                    tl,
                ]
            ]
        },
        "properties": {
            "name": name,
            "isLocked": True,
            "classification": {
                "name": class_name,
            },
            "measurements": [
                {
                    "name": "Confidence",
                    "value": confidence,
                },
                {
                    "name": "Prediction",
                    "value": prediction
                }
            ]
        }
    }
    return json_object


def create_json_tile2(coords, slide_size, nrows, ncols, name="tile", prediction="NA", confidence="NA", class_name="Other"):
    """
    Create a json object with all the ROI info in a geojson format
    Returns ROI info using slide_size instead of tile size
    """
    tile_size = [slide_size[0] / ncols, slide_size[1] / nrows]
    tl, tr, bl, br = coords_to_corner_pixels(coords, tile_size)
    json_object = {
        "type": "Feature",
        "id": "PathAnnotationObject",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    tl,
                    tr,
                    br,
                    bl,
                    tl,
                ]
            ]
        },
        "properties": {
            "name": name,
            "isLocked": True,
            "classification": {
                "name": class_name,
            },
            "measurements": [
                {
                    "name": "Confidence",
                    "value": confidence,
                },
                {
                    "name": "Prediction",
                    "value": prediction
                }
            ]
        }
    }
    return json_object
