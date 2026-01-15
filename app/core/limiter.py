from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter
# Uses in-memory storage by default which is sufficient for simple brute-force protection
limiter = Limiter(key_func=get_remote_address)
