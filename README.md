### mosaic

Creates a [photo mosaic](https://en.wikipedia.org/wiki/Photographic_mosaic) from CIFAR-10 images. See [davidheineman.com](https://davidheineman.com) for an example.

**Usage:**

```sh
pip install -r requirements.txt
python src/cifar.py cifar10 img
python src/run.py image_path img/dog --baseWidth 10000 --step 32
```

**Example:**

![mosaic](example.png)