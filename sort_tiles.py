import csv
import os
from tqdm import tqdm
import random
from src.Omero import Omero
from src.omero_credentials import USERNAME, PASSWORD, HOST

# Run sort_tiles.py to take a folder of prediction tsv files and return a csv containing the
# highest confidence tiles with the given parameters.

CONFIDENCE_THRESHOLD = 0.99
NUM_TILES_PER_SLIDE = 100

# PREDICTION_FOLDER = "/Volumes/ddt/working/DeepHiPa/resources/models_pbrm1_bap1_no_whole_patient/omero_shufflenet_v2_x1_0_lr0.1_mag20_patch512x512_1/epoch_50_1637176378/maps"
PREDICTION_FOLDER = "/Users/rossg/Documents/HistSlideVis_data/models_pbrm1_bap1_no_whole_patient/omero_shufflenet_v2_x1_0_lr0.1_mag20_patch512x512_1/epoch_50_1634986138"
OUT_FILE = "./data/tiles.csv"
ALL_MUTATIONS = ["BAP1", "PBRM1"]
PROJECT_ID = 355


def get_ground_truth_and_slide_id(all_slides, slide_name, mutation, omero):
    for slide in all_slides:
        if slide["name"] == slide_name:
            slide_id = slide["id"]
            break
    if not slide_id:
        return None
    ground_truth = omero.get_ground_truth(slide_id, [mutation]).get(mutation)

    if ground_truth is None or not ground_truth.isdigit():
        print("Ground truth is not an integer")
        return

    return int(ground_truth), slide_id


def read_predictions_1d(path, filename, mutation, all_slides, omero, confidence_threshold=0.99):
    slide_name, _ = filename.split('.ome')
    slide_tiles = []

    ground_truth, slide_id = get_ground_truth_and_slide_id(all_slides, slide_name, mutation, omero)

    with open(path, newline='') as f:
        read_tsv = csv.reader(f, delimiter="\t")

        for i, row in enumerate(read_tsv):

            for j, cell in enumerate(row):

                # Skip all non-numeric predictions
                if cell == "nan":
                    continue
                cell = float(cell)

                # Filter by high confidence tiles
                confidence = abs(cell - 0.5) * 2
                if confidence < confidence_threshold:
                    continue

                # Obtain the predicted value
                if cell > 0.5:
                    prediction = 1
                else:
                    prediction = 0

                # Skip tiles which are predicted as no mutation
                if cell < 0.5:
                    continue

                slide_tiles.append({
                    "slide_name": slide_name,
                    "confidence": confidence,
                    "output": cell,
                    "mutation": mutation,
                    "prediction": prediction,
                    "x_coord": j,
                    "y_coord": i,
                    "ground_truth": ground_truth,
                    "slide_id": slide_id
                    })

    return slide_tiles


def filter_tiles(top_tiles, num_tiles_per_slide=100):
    # Copy top tiles and add random value to each
    tiles_tmp = top_tiles[:]
    for tile in tiles_tmp:
        tile["random_value"] = random.random()

    # Sort by confidence and random value so tiles with the same confidence will appear randomly
    top_tiles = sorted(top_tiles, key=lambda d: (d["confidence"], d["random_value"]), reverse=True)

    filtered_tiles = []
    slide_count = {}

    for i, tile in enumerate(top_tiles):
        slide_name = tile["slide_name"]

        if slide_name not in slide_count:
            slide_count[slide_name] = 0

        if slide_count[slide_name] >= num_tiles_per_slide:
            continue

        del tile["random_value"]
        filtered_tiles.append(tile)

        slide_count[slide_name] += 1

    return filtered_tiles


def save_tiles(evaluate=True, confidence_threshold=0.99):
    prediction_files = [file for file in os.listdir(PREDICTION_FOLDER) if ".tsv" in file]

    top_tiles = []

    omero = Omero(HOST, USERNAME, PASSWORD)
    omero.connect()
    omero.switch_user_group()
    all_slides = omero.get_slide_names(PROJECT_ID)

    for filename in tqdm(prediction_files):
        path = os.path.join(PREDICTION_FOLDER, filename)
        for mutation in ALL_MUTATIONS:
            if mutation in filename:
                top_tiles += read_predictions_1d(path, filename, mutation, all_slides, omero, confidence_threshold=confidence_threshold)

    filtered_tiles = filter_tiles(top_tiles, num_tiles_per_slide=NUM_TILES_PER_SLIDE)

    with open(OUT_FILE, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=filtered_tiles[0].keys())
        writer.writeheader()
        writer.writerows(filtered_tiles)

    if evaluate:
        evaluate_tiles(filtered_tiles)


def evaluate_tiles(top_tiles):
    mutation_counts = {}
    slide_counts = {}
    for mutation in ALL_MUTATIONS:
        mutation_counts[mutation] = 0

    for tile in top_tiles:
        # Count the number of top tiles for each mutation
        for mutation in ALL_MUTATIONS:
            if tile["mutation"] == mutation:
                mutation_counts[mutation] += 1

        # Count the number of tiles in each slide
        if tile["slide_name"] not in slide_counts:
            slide_counts[tile["slide_name"]] = 1
        else:
            slide_counts[tile["slide_name"]] += 1

    # Calculate percentage of total tiles in each slide
    len_tiles = len(top_tiles)
    slide_percentages = []
    for slide_name in slide_counts:
        slide_percentages.append({"slide_name": slide_name, "percentage": slide_counts[slide_name] / len_tiles})
    slide_percentages = sorted(slide_percentages, key=lambda d: d['percentage'], reverse=True)

    # Print results
    print(f"Total number of tiles:\t{len_tiles}")
    for mutation in mutation_counts:
        print(f"Number of {mutation} tiles:\t{mutation_counts[mutation]}")
    print("")
    print("Percentage of total tiles in each slide:")
    for slide_percentage in slide_percentages:
        print(f"{slide_percentage['slide_name']}\t\t{round(slide_percentage['percentage'] * 100, 2)}%")


if __name__ == "__main__":
    random.seed(0)
    save_tiles(evaluate=True, confidence_threshold=CONFIDENCE_THRESHOLD)
