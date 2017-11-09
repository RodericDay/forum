import re
from rest_framework import throttling


class ScopedFineRateThrottle(throttling.ScopedRateThrottle):

    def parse_rate(self, rate):
        n, d = map(int, re.match(r'(\d+)/(\d+)seconds', rate).groups())
        return (n, d)
