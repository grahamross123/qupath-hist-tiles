// Imports the correct annotations for a given image from a folder containing multiple geojson files.


TILE_DIR = "/Users/rossg/Projects/qupath-hist-tiles/output/high_confidence_tiles"
ALL_CLASSES = ["Top PBRM1 tiles", "Top BAP1 tiles"]


// Delete all previous top tile objects
deletePreviousTiles(ALL_CLASSES)


// Get all files in the tile annotations folder
def baseDir = new File(TILE_DIR);
files = baseDir.listFiles();

// Get the name of the current image
imageData = getCurrentImageData()
currentName = GeneralTools.getNameWithoutExtension(imageData.getServer().getMetadata().getName()).toString()

for (file in files) {
    fileString = file.toString()
    // Check if the tile annotation filepath contains the name of the current image
    if (fileString.contains(currentName)) {
        // If it does then import the annotations
        importAnnotations(fileString)
    }
}


// Function to add objects from json file into the current image
def importAnnotations(file) {
    def gson = GsonTools.getInstance(true)
    def json = new File(file).text
    
    // Read the annotations
    def type = new com.google.gson.reflect.TypeToken<List<qupath.lib.objects.PathObject>>() {}.getType()
    def deserializedAnnotations = gson.fromJson(json, type)
    
    addObjects(deserializedAnnotations)
 }
 
 
 // Function to delete all objects in an array of class names
 def deletePreviousTiles(classnames) {
    for (className in classnames) {
        removal = getAnnotationObjects().findAll{it.getPathClass().toString().contains(className)}
        removeObjects(removal, true)
    }
}
