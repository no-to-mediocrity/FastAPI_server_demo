import datetime
import random
import string

timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=4))