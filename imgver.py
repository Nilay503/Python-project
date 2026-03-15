from PIL import Image
from PIL.ExifTags import TAGS

#open the image file
#file = input("enter the file path")
image = Image.open("your file name here")

#exif metadata
exifdata = image.getexif()

print(exifdata)

#looping through all the value in exif data

for tagid in exifdata:
    #getting the tag name
    tagname = TAGS.get(tagid,tagid)
    #for the value
    value = exifdata.get(tagid)
    #printing the value
    print(f"{tagname:25}: {value}")

