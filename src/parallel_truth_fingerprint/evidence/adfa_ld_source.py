"""Byte-accountable ADFA-LD qualification and inventory; no downloads."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path

@dataclass(frozen=True)
class AdfaInventory:
    source_id:str; archive_sha256:str; extracted_files:tuple[tuple[str,str,int],...]; status:str; discrepancies:tuple[str,...]; authorization_effect:str="none"
def inventory_adfa_ld(root:Path, *, source_id:str, expected_archive_sha256:str|None=None)->AdfaInventory:
    if not root.is_dir(): return AdfaInventory(source_id,"",(),"blocked",("ADFA-SOURCE-MISSING",))
    files=tuple(sorted((str(p.relative_to(root)).replace("\\","/"),hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size) for p in root.rglob("*") if p.is_file()))
    digest=hashlib.sha256("".join(f"{n}:{h}:{s}\n" for n,h,s in files).encode()).hexdigest()
    problems=[]
    if not files:problems.append("ADFA-INVENTORY-EMPTY")
    if expected_archive_sha256 and digest!=expected_archive_sha256.removeprefix("sha256:"):problems.append("ADFA-HASH-MISMATCH")
    return AdfaInventory(source_id,"sha256:"+digest,files,"qualified" if not problems else "blocked",tuple(problems))
