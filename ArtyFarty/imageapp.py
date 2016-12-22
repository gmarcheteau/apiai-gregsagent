import clustercolors
import colornames
import processimage

#get from user
url = raw_input("Image URL: ")

#"http://www.telegraph.co.uk/content/dam/art/2016/10/04/picasso-large_trans++qVzuuqpFlyLIwiB6NTmJwbKTcqHAsmNzJMPMiov7fpk.jpg"

#default url is invalid or no input
if (len(url)<2):
  url="https://lh3.ggpht.com/T1-pgt04AHPA01FPGahJ0CwV7jo4FpM6ZiM6vT5WU22K3aniMabWlqTuqtOox8sVXQ=w300"

image_resized = processimage.url_to_image(url)

clt = clustercolors.fitColorClustering(image_resized)
maincolors = clustercolors.getColorsFromClusters(clt)
clustercolors.showColorClusters(image_resized,maincolors)