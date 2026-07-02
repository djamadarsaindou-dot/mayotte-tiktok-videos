"""Bench XTTS v2 sur GPU (RTX 5060) — même phrase que les tests CPU.

Comparaison attendue : ~56-99 s par synthèse en CPU (mesuré cette nuit)
contre quelques secondes en CUDA.
"""
import sys
import time
from pathlib import Path

import torch

# Shims de compatibilité du projet (transformers isin_mps_friendly +
# torchaudio load/save via soundfile) — à importer AVANT TTS.api
sys.path.insert(0, r"C:\Users\djama\Documents\Claude\Projects"
                   r"\Site internet - Montage vidéo")
import src._coqui_shim  # noqa: E402,F401

PHRASE = ("À Mayotte, le lagon de mille cinq cents kilomètres carrés cache "
          "une double barrière de corail que seuls dix endroits au monde "
          "possèdent. Et pourtant, presque personne ne le sait.")
REF = Path(r"C:\Users\djama\Documents\Claude\Projects"
           r"\Site internet - Montage vidéo\assets\voice\reference_fr_8s.wav")
OUT = Path(r"C:\Users\djama\Documents\Claude\Projects"
           r"\Site internet - Montage vidéo\output\voice_samples"
           r"\test_E_xtts_gpu.wav")

print(f"cuda: {torch.cuda.is_available()} | {torch.cuda.get_device_name(0)}")

t0 = time.time()
from TTS.api import TTS  # noqa: E402

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
print(f"chargement modele : {time.time()-t0:.0f}s")

# 1er run (compilation kernels) puis 2 runs mesures
for run in range(1, 4):
    t1 = time.time()
    tts.tts_to_file(text=PHRASE, speaker_wav=str(REF), language="fr",
                    file_path=str(OUT), temperature=0.60)
    print(f"synthese GPU run{run} : {time.time()-t1:.1f}s")
print(f"VRAM utilisee : {torch.cuda.max_memory_allocated()/1e9:.2f} GB")
print("FIN_BENCH_GPU")
