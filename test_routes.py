"""Quick test to verify all routes return 200."""
from urllib.request import urlopen

pages = ['/', '/about', '/services', '/help', '/contact', '/login', '/register']
for p in pages:
    status = urlopen('http://127.0.0.1:5000' + p).status
    print(f'{p}: {status}')
print('\nAll routes OK!')
