# Narração local — Qwen3-TTS VoiceDesign

**Histórico rejeitado:** o usuário ouviu `audition.wav` e respondeu “Ainda soa artificial”. O modelo foi instalado e executado nesta máquina, mas não é a voz da entrega. Depois, o usuário autorizou Edge online gratuito e escolheu Thalita. Não retomar esta voz como aprovada.

Substituição do teste Kokoro rejeitado. Voz feminina descrita por texto, sem imitar uma pessoa real. Modelo e código Apache-2.0, [fonte oficial](https://github.com/QwenLM/Qwen3-TTS). O modelo público suporta português. Qualidade, sotaque e pronúncia precisam de revisão auditiva; suporte ao idioma não garante resultado aprovado.

## Setup testado no Windows / NVIDIA

Python 3.12, GPU RTX 3060 Ti de 8 GB, CUDA 12.8. Ambiente isolado; não precisa instalar o toolkit CUDA separado. Downloads iniciais de aproximadamente 8 GB entre runtime e pesos. Não há inferência remota, conta, créditos ou clonagem de pessoa.

```powershell
python -m venv motion-001/local-qwen/.venv
& motion-001/local-qwen/.venv/Scripts/python.exe -m pip install --no-cache-dir torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
& motion-001/local-qwen/.venv/Scripts/python.exe -m pip install --no-cache-dir -r motion-001/local-qwen/requirements.txt
& motion-001/local-qwen/.venv/Scripts/python.exe motion-001/local-qwen/download_model.py
& motion-001/local-qwen/.venv/Scripts/python.exe motion-001/local-qwen/synthesize.py --audition
# Depois do teste inicial:
& motion-001/local-qwen/.venv/Scripts/python.exe motion-001/local-qwen/synthesize.py
```

`download_model.py` fixa a revisão pública dos pesos e registra hashes SHA256. `synthesize.py` usa somente arquivos locais, SDPA e BF16; não depende de FlashAttention. Arquivos grandes e ambiente ficam fora do Git.

O caminho CUDA é específico deste computador. No Mac, usar PyTorch apropriado à máquina e adaptar `device_map`/dtype após verificar suporte; MPS não foi testado aqui. O render Blender/HyperFrames continua separado da voz, permitindo reutilizar os WAVs exportados em outra máquina.
