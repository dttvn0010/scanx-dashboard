from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
import numpy as np
import sys

def resizeProfileImage(imgField):
    imageFile = BytesIO(imgField.read())
    image = Image.open(imageFile)
    w, h = image.size
    sz = min(w, h, settings.PROFILE_IMAGE_SIZE)

    image_data = np.array(image)
    if len(image_data.shape) == 3:
        image_data = image_data[:,:,:3]
        
    if h > w:
        image_data = image_data[:w]
    
    image = Image.fromarray(image_data).resize((sz, sz), Image.ANTIALIAS)

    output = BytesIO()
    image.save(output, 'JPEG', quality=90)
    fileName = f"{imgField.name.split('.')[0]}.jpg"
    return InMemoryUploadedFile(output,'ImageField', fileName , 'image/jpeg', sys.getsizeof(output), None)