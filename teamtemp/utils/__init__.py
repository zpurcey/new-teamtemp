import random
import string


chars = string.ascii_letters + string.digits

def random_string(length):
    return ''.join(random.choice(chars) for x in range(length))
