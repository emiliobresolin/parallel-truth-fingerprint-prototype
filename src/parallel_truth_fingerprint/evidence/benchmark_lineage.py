"""Shared immutable benchmark-source/track admission guards."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class BenchmarkTrackAdmission:
    dataset_family:str; source_manifest_id:str; inventory_id:str; partition_id:str|None; status:str; reasons:tuple[str,...]; authorization_effect:str="none"
def admit_benchmark_track(*,dataset_family:str,source_manifest_id:str|None,inventory_id:str|None,official_source:bool,fixture_only:bool)->BenchmarkTrackAdmission:
    reasons=[]
    if dataset_family not in {"adfa_ld","lid_ds_2021","hai_23_05"}:reasons.append("BMARK-FAMILY")
    if not official_source:reasons.append("BMARK-OFFICIAL-SOURCE")
    if fixture_only:reasons.append("BMARK-FIXTURE-NOT-FORMAL")
    if not source_manifest_id or not source_manifest_id.startswith("sha256:"):reasons.append("BMARK-SOURCE-MANIFEST")
    if not inventory_id or not inventory_id.startswith("sha256:"):reasons.append("BMARK-INVENTORY")
    return BenchmarkTrackAdmission(dataset_family,source_manifest_id or "",inventory_id or "",None,"qualified" if not reasons else "blocked",tuple(reasons))
