import serialize
from holopy.core.metadata import Image
from holopy.core import save
import sys
import os


def convert_image_yaml(yaml):
    h = serialize.load(yaml)
    d = Image(h, spacing=h.spacing, medium_index=h.optics.index, illum_wavelen=h.optics.wavelen, illum_polarization=h.optics.polarization)
    name, ext = os.path.splitext(yaml)
    save(name, d)


if __name__ == '__main__':
    for name in sys.argv[1:]:
        convert_image_yaml(name)
