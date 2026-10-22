"""Explicit, one-time download of public Kokoro weights; inference is offline."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
FILES = {
    'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx',
    'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin',
    'MODEL_CARD.md': 'https://huggingface.co/hexgrad/Kokoro-82M/raw/main/README.md',
    'VOICES.md': 'https://huggingface.co/hexgrad/Kokoro-82M/raw/main/VOICES.md',
    'KOKORO_ONNX_LICENSE.txt': 'https://raw.githubusercontent.com/thewh1teagle/kokoro-onnx/main/LICENSE',
}
EXPECTED = {
    'kokoro-v1.0.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a',
    'voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d',
}

if __name__ == '__main__':
    records = []
    for name, url in FILES.items():
        dest = ROOT / name
        if not dest.exists():
            temporary = dest.with_suffix(dest.suffix + '.part')
            print('Downloading', name, flush=True)
            urllib.request.urlretrieve(url, temporary)
            temporary.replace(dest)
        with dest.open('rb') as source:
            digest=hashlib.file_digest(source,'sha256').hexdigest()
        if name in EXPECTED and digest != EXPECTED[name]:
            raise ValueError(f'Weight hash mismatch: {name}; do not use it.')
        records.append({'name': name, 'url': url, 'bytes': dest.stat().st_size,'sha256':digest})
    (ROOT / 'model-manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print('Public model files ready. No account or API used.', flush=True)
