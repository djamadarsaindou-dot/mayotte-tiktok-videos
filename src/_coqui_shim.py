"""Shims de compatibilité pour Coqui TTS sur un environnement récent.

À importer AVANT toute utilisation de TTS.

1. transformers : `isin_mps_friendly` a été supprimé de transformers 4.50+.
   On le restaure (équivalent torch.isin).

2. torchaudio 2.11 : l'I/O audio classique a été retiré et délégué à torchcodec,
   qui ne supporte pas FFmpeg 8 (DLL libtorchcodec_core*.dll introuvables).
   On remplace torchaudio.load / torchaudio.save par une implémentation
   basée sur `soundfile`, qui fonctionne sans torchcodec.
"""
import torch
import transformers.pytorch_utils as _pu

# --- Shim 1 : isin_mps_friendly ---
if not hasattr(_pu, "isin_mps_friendly"):
    def isin_mps_friendly(elements, test_elements):
        return torch.isin(elements, test_elements)
    _pu.isin_mps_friendly = isin_mps_friendly  # type: ignore[attr-defined]


# --- Shim 2 : torchaudio.load/save via soundfile (contourne torchcodec) ---
def _install_torchaudio_soundfile_shim() -> None:
    try:
        import numpy as np
        import soundfile as sf
        import torchaudio
    except Exception:
        return

    def _load(filepath, *args, **kwargs):
        """Renvoie (waveform [channels, frames] float32, sample_rate)."""
        data, sr = sf.read(str(filepath), dtype="float32", always_2d=True)
        # soundfile : [frames, channels] → torchaudio attend [channels, frames]
        tensor = torch.from_numpy(np.ascontiguousarray(data.T))
        return tensor, sr

    def _save(filepath, src, sample_rate, *args, **kwargs):
        """Sauvegarde un tensor [channels, frames] via soundfile."""
        arr = src.detach().cpu().numpy() if hasattr(src, "detach") else np.asarray(src)
        if arr.ndim == 2:
            arr = arr.T  # [channels, frames] → [frames, channels]
        sf.write(str(filepath), arr, int(sample_rate))

    torchaudio.load = _load        # type: ignore[assignment]
    torchaudio.save = _save        # type: ignore[assignment]


_install_torchaudio_soundfile_shim()
