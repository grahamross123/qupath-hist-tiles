// Imports the specified geojson annotations into the given image

FILEPATH="./multiple_annotations.json"

def gson = GsonTools.getInstance(true)
def json = new File(FILEPATH).text

// Read the annotations
def type = new com.google.gson.reflect.TypeToken<List<qupath.lib.objects.PathObject>>() {}.getType()
def deserializedAnnotations = gson.fromJson(json, type)

addObjects(deserializedAnnotations)