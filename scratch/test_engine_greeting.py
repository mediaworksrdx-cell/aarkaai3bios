import sys
sys.path.append('.')
from modules import aarkaa_engine
import logging

logging.basicConfig(level=logging.INFO)

ans, conf = aarkaa_engine.primary_check("Hello", "en")
print("Response for 'Hello' (en):")
print(ans)

ans, conf = aarkaa_engine.primary_check("Hello", "de")
print("Response for 'Hello' (de):")
print(ans)
