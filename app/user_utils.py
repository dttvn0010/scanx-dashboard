import random
import string

def genPassword():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
