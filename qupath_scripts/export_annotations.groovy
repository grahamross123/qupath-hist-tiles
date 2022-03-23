// Run the script for a given image to export all annotations to OUTNAME as a geojson file.

OUTNAME = "./annotations.json"

// write to file
boolean prettyPrint = false // false results in smaller file sizes and thus faster loading times, at the cost of nice formating
def gson = GsonTools.getInstance(prettyPrint)
def annotations = getAnnotationObjects()
println gson.toJson(annotations) // you can check here but this will be HUGE and take a long time to parse

// automatic output filename, otherwise set explicitly
String imageLocation = getCurrentImageData().getServer().getPath()

File file = new File(outfname)
file.withWriter('UTF-8') {
    gson.toJson(annotations,it)
}