from dotenv import load_dotenv
load_dotenv()

import os
print(os.environ.get('DEBUG'))  # Should print 'True'