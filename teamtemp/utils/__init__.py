import string
import random

def random_string(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for x in range(length))
