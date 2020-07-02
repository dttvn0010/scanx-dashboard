import random
import string

def genPassword(k=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))
