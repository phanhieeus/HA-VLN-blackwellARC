from pathlib import Path
import sys
import json

sys.path.insert(0, '/kaggle/working/HA-VLN/scripts')
from download_hf import unpack_haps

archive = Path('/kaggle/working/havln-runtime/HAPS2_0.validation.zip')
root = Path('/kaggle/working/HA-VLN/Data')
(root/'downloads').mkdir(exist_ok=True)
manifest = json.loads(Path('/kaggle/working/havln-runtime/HAPS2_0.validation.manifest.json').read_text())
unpack_haps(archive, root, manifest['sha256'])
print('HAPS_EXTRACTION_DONE', flush=True)
