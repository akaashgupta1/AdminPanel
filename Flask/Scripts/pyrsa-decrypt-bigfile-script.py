#!"C:\Users\Mewtwo\Documents\Singapore\NUS\Modules - Semester 5\3002\FinalShop\Flask\Scripts\python.exe"
# EASY-INSTALL-ENTRY-SCRIPT: 'rsa==3.1.2','console_scripts','pyrsa-decrypt-bigfile'
__requires__ = 'rsa==3.1.2'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('rsa==3.1.2', 'console_scripts', 'pyrsa-decrypt-bigfile')()
    )
