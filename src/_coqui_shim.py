"""Shim de compatibilité pour Coqui TTS sur transformers récent.

Coqui TTS 0.27.5 utilise `isin_mps_friendly` qui a été supprimé de transformers 4.50+.
On le restaure ici (équivalent à torch.isin pour notre usage CPU/CUDA).

À importer AVANT toute utilisation de TTS.
"""
import torch
import transformers.pytorch_utils as _pu

if not hasattr(_pu, "isin_mps_friendly"):
    def isin_mps_friendly(elements, test_elements):
        return torch.isin(elements, test_elements)
    _pu.isin_mps_friendly = isin_mps_friendly  # type: ignore[attr-defined]
