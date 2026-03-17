from __future__ import annotations
from pathlib import Path
from typing import Any
import os

from core.operators.base import BaseOperator
from core.adapters import LibvgmAdapter, GmeAdapter, VgmstreamAdapter

class IngestTrackOperator(BaseOperator):
    """
    Ingest data into Helix. 
    Supports 'indexing' (metadata only) and 'full' modes.
    Handles multiple entity types (Track, KnowledgeSource, SoundDriver, SoundChip, CPU).
    """
    
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = payload.get("mode", "full")
        target_path = payload.get("path") or payload.get("file_path")
        if not target_path:
            raise ValueError("No path provided for ingestion.")
            
        p = Path(target_path)
        
        # 1. Identity & Type Resolution
        entity_type = self._resolve_entity_type(p, payload)
        
        # 2. Metadata Extraction
        metadata = self._extract_metadata(p, payload, entity_type)
        
        # 3. Attribution Logic (for Music)
        if entity_type == "Track":
            raw_artist = metadata.get("artist", "")
            artists = [a.strip() for a in raw_artist.split(";") if a.strip()]
            n = len(artists)
            attr_type = "solo" if n == 1 else "multi" if n > 1 else "unknown"
            
            contributions = []
            if n > 0:
                conf = 1.0 / n
                for artist in artists:
                    contributions.append({
                        "artist_id": artist,
                        "confidence": conf,
                        "source": "multi_credit" if n > 1 else "solo_credit"
                    })
            
            metadata.update({
                "attribution_type": attr_type,
                "artist_contributions": contributions,
                "original_credit": raw_artist,
                "analysis_status": "pending"
            })

        # 4. Phase Separation: Indexing vs Analysis
        if mode == "index":
            return {
                "entity_type": entity_type,
                "metadata": metadata,
                "path": str(p),
                "status": "indexed"
            }
            
        # 5. Full Analysis (Only for supported types like Track)
        if entity_type == "Track":
            adapter = self._route_to_adapter(p)
            result = adapter.execute(payload)
            result.update(metadata)
            result["analysis_status"] = "analyzed"
            return result
            
        return {
            "entity_type": entity_type,
            "metadata": metadata,
            "status": "indexed" # fallback for non-analyzable types
        }

    def _resolve_entity_type(self, p: Path, payload: dict[str, Any]) -> str:
        if payload.get("type"):
            return payload["type"]
            
        suffix = p.suffix.lower()
        if suffix in {".vgm", ".vgz", ".spc", ".nsf", ".gbs", ".hes", ".psf", ".flac", ".mp3", ".wav", ".opus"}:
            return "Track"
        if suffix in {".pdf", ".txt", ".doc", ".docx", ".pdf"}:
            return "KnowledgeSource"
        if p.is_dir():
            if any(p.name.upper() == d for d in ["GEMS", "SMPS"]):
                return "SoundDriver"
            return "Folder" # Generic
        
        name = p.name.upper()
        if name.startswith("YM") or name.startswith("SN"):
            return "SoundChip"
        if name in {"Z80", "68000", "M68K"}:
            return "CPU"
            
        return "Unknown"

    def _extract_metadata(self, p: Path, payload: dict[str, Any], entity_type: str) -> dict[str, Any]:
        # In a real implementation, this would read foobar metadb or file tags
        # Here we use payload as primary source
        metadata = payload.copy()
        metadata["name"] = metadata.get("name") or p.stem
        metadata["file_path"] = str(p)
        return metadata

    def _route_to_adapter(self, file_path: Path) -> Any:
        libvgm = LibvgmAdapter()
        if libvgm.supports(file_path): return libvgm
        gme = GmeAdapter()
        if gme.supports(file_path): return gme
        vgmstream = VgmstreamAdapter()
        if vgmstream.supports(file_path): return vgmstream
        raise ValueError(f"No adapter found for format: {file_path.suffix}")
