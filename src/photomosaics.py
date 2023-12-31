from PIL import Image
import json, os, sys, random, math


class PhotoMosaic:
    def __init__(self, imageFile, imagesFolder, step=100, targetWidth=5000):
        self.folder = os.path.basename(os.path.normpath(imagesFolder))
        self.step = step
        self.targetWidth = targetWidth
        self.imageFile = os.path.basename(imageFile)
        self.image = self.get_image(imageFile, resize=True)
        self.width, self.height = self.image.size
        self.imageDictionary = self.load_images(imagesFolder, dimension=(self.step, self.step))
        self.matrix = self.get_matrix()
        self.editedImage = self.photo_mosaic()

    def get_matrix(self) -> list:
        """Returns a 2D list of RGB tuples of image"""
        print("Loading matrix...")
        pixels = list(self.image.getdata())
        return [pixels[y:y+self.width] for y in range(0, len(pixels), self.width)]

    def get_image(self, path: str, thumbnail: tuple = None, squareImage: bool = None, resize: bool = None) -> Image:
        """Return an Image object"""
        with Image.open(path) as image:
            if squareImage:  # if we need to get a square image
                width, height = image.size
                if width != height:  # check if image is square
                    toCrop = min((width, height))  # get minimum of width or height
                    image = self.crop_center(image, toCrop, toCrop)  # get cropped, square image

            if resize:  # if we need to resize the image, resize it to baseWidth
                image = self.resize_image(image)

            if thumbnail:  # if some thumbnail dimension is given, then resize it
                image.thumbnail(thumbnail)

            if image.mode == 'P':  # if transparent, convert to RGBA
                image = image.convert('RGBA')
            else:  # else force convert to RGB
                image = image.convert('RGB')

            return image

    def resize_image(self, image: Image) -> Image:
        """Resize image to a bigger size so sub-images are more visible"""
        width, height = image.size
        baseWidth = self.targetWidth
        widthPercent = baseWidth / width
        newHeight = int(height * widthPercent)
        return image.resize((baseWidth, newHeight), Image.ANTIALIAS)

    @staticmethod
    def get_cache(cacheFile) -> dict:
        """Return a cached dictionary from json file if exists"""
        try:
            with open(cacheFile, 'r') as jsonFile:
                return json.load(jsonFile)
        except FileNotFoundError:
            return {}

    @staticmethod
    def store_cache(cacheFile, cachedInfo):
        """Store average of images' RGB values as cache for future use"""
        with open(cacheFile, 'w') as jsonFile:
            json.dump(cachedInfo, jsonFile, indent=4, sort_keys=True)

    def load_images(self, folderPath: str, dimension: tuple) -> dict:
        """Load all images in given path and return dictionary containing them"""
        print("Loading images...")
        previous_path = os.getcwd()
        os.chdir(folderPath)
        cacheUpdated = False
        cacheFile = '_'.join(self.folder.lower().split()) + '_cache.json'
        cachedInfo = self.get_cache(cacheFile)
        imagesDictionary = {}

        for file in os.listdir():
            if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            image = self.get_image(file, thumbnail=dimension, squareImage=True)
            if file in cachedInfo.keys():
                average = tuple(cachedInfo[file])
            else:
                pixels = list(image.getdata())
                average = self.get_average(pixels)
                cachedInfo[file] = average
                cacheUpdated = True
            if average not in imagesDictionary:
                imagesDictionary[average] = [image]
            else:
                imagesDictionary[average].append(image)

        if cacheUpdated:
            self.store_cache(cacheFile, cachedInfo)

        os.chdir(previous_path)
        return imagesDictionary

    def best_match(self, rgbTuple: tuple) -> Image:
        """Return best possible image from imageDict that matches rgbTuple based on euclidean distance"""
        bestKeys = []
        bestDistance = None
        for otherTuple in self.imageDictionary.keys():
            currentDistance = self.euclidean_distance(rgbTuple, otherTuple)
            if not bestDistance or currentDistance < bestDistance:
                bestDistance = currentDistance
                bestKeys.insert(0, otherTuple)
        key = bestKeys[0]
        return random.choice(self.imageDictionary[key])

    def photo_mosaic(self) -> Image:
        """Return a manipulated image with mosaic implemented"""
        print("Creating a mosaic...")
        editedImage = Image.new(self.image.mode, (self.width, self.height))
        for y in range(0, self.height, self.step):
            y2 = y + self.step if y + self.step < self.height else self.height
            for x in range(0, self.width, self.step):
                x2 = x + self.step if x + self.step < self.width else self.width
                subMatrix = []
                for z in range(y, y2):
                    subList = self.matrix[z][x:x2]
                    subMatrix.append(subList)
                flat_list = [rgbTuple for row in subMatrix for rgbTuple in row]
                average = self.get_average(flat_list)
                img = self.best_match(average)
                editedImage.paste(img, (x, y))
            self.progress_bar(y, self.height)
        print()
        return editedImage

    def save_image(self):
        """Save image to a folder"""
        folderName = "out"
        previous_path = os.getcwd()
        if not os.path.exists(folderName):
            os.mkdir(folderName)
        os.chdir(folderName)
        name, ext = self.imageFile.split('.')
        counter = 0
        output_image = f"{name}-mosaic.{ext}"
        if os.path.exists(output_image):
            while os.path.exists(output_image):
                output_image = f"{name}-mosaic{counter}.{ext}"
                counter += 1
        path = os.path.join(os.getcwd(), output_image)
        self.editedImage.save(path)
        print(f"Photo mosaic has been successfully saved to {path}.")
        os.chdir(previous_path)

    def show_image(self):
        """Show image in default picture viewer"""
        self.editedImage.show()

    @staticmethod
    def euclidean_distance(l1: tuple, l2: tuple) -> float:
        """Return euclidean distance between two RGB tuples"""
        r = (l1[0] - l2[0]) ** 2
        g = (l1[1] - l2[1]) ** 2
        b = (l1[2] - l2[2]) ** 2
        return math.sqrt(r + g + b)

    @staticmethod
    def get_average(flatList: list) -> tuple:
        """Return average RGB tuple from a list of given RGB values"""
        r, g, b = 0, 0, 0
        length = len(flatList)
        for elem in flatList:
            r += elem[0]
            g += elem[1]
            b += elem[2]
        r, g, b = r / length, g / length, b / length
        return r, g, b

    @staticmethod
    def crop_center(pil_img: Image, crop_width: float, crop_height: float) -> Image:
        """Return a center-cropped image - copied from Pillow documentation"""
        img_width, img_height = pil_img.size
        return pil_img.crop(((img_width - crop_width) // 2,
                             (img_height - crop_height) // 2,
                             (img_width + crop_width) // 2,
                             (img_height + crop_height) // 2))

    @staticmethod
    def progress_bar(y: int, height: int):
        """Display a progress bar when rendering mosaic"""
        percentage = math.ceil(y / height * 100)
        sys.stdout.write('\r')
        sys.stdout.write("[%-20s] %d%% rendered." % ('=' * (percentage // 5), percentage))
        sys.stdout.flush()

