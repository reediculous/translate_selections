#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
import numpy as np

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def load_config(config_path: Path) -> str:
    try:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        data_folder_path = cfg.get("data_folder_path")
        if not data_folder_path:
            raise ValueError("Missing 'data_folder_path' in config.json")
        return data_folder_path
    except Exception as e:
        eprint(f"[ERROR] Failed to read config.json: {e}")
        sys.exit(1)

def load_selections(selections_path: Path):
    try:
        with selections_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        eprint(f"[ERROR] Failed to read selections.json: {e}")
        sys.exit(1)

def resolve_filepath(base_data_path: Path, original_path: str) -> Path:
    """
    Replace prefix in original_path with data_folder_path (relative).
    """
    fname = os.path.basename(original_path)
    return base_data_path / fname

def main():
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "config.json"
    selections_path = script_dir / "selections.json"
    pulses_out_path = script_dir / "pulses.txt"

    # load config
    rel_data_folder = load_config(config_path)
    base_data_path = (script_dir / rel_data_folder).resolve()

    selections = load_selections(selections_path)

    # Open output file and write header once
    with pulses_out_path.open("w", encoding="utf-8") as out:
        out.write("time\tcurrent\tvoltage\n")

        for entry_idx, entry in enumerate(selections):
            orig_file = entry.get("file_name")
            if not orig_file:
                eprint(f"[WARN] Entry {entry_idx} missing 'file_name'; skipping.")
                continue

            filepath = resolve_filepath(base_data_path, orig_file)

            if not filepath.exists():
                eprint(f"[WARN] File not found: {filepath} (from {orig_file}); skipping.")
                continue

            try:
                arr = np.load(filepath)
                if "data" not in arr:
                    eprint(f"[WARN] 'data' array not found in {filepath}; skipping.")
                    continue
                data = arr["data"]
            except Exception as e:
                eprint(f"[WARN] Failed to load {filepath}: {e}; skipping.")
                continue

            # Extract v, t, i (per your mapping)
            try:
                v = data[1]
                t = data[0]
                i = data[2]
            except Exception as e:
                eprint(f"[WARN] Unexpected data shape in {filepath}: {e}; skipping.")
                continue

            n = min(len(t), len(i), len(v))
            if n == 0:
                eprint(f"[WARN] Empty arrays in {filepath}; skipping.")
                continue

            sels = entry.get("selections", [])
            if not isinstance(sels, list) or not sels:
                eprint(f"[WARN] No selections for {filepath}; skipping.")
                continue

            for sel_idx, sel in enumerate(sels):
                try:
                    start = int(sel["start_index"])
                    end = int(sel["end_index"])
                except Exception:
                    eprint(f"[WARN] Invalid selection indices in entry {entry_idx}, selection {sel_idx}; skipping.")
                    continue

                start_clamped = max(0, min(start, n - 1))
                end_clamped = max(0, min(end, n - 1))
                if end_clamped < start_clamped:
                    eprint(f"[WARN] end_index < start_index for {filepath} sel {sel_idx}; skipping.")
                    continue

                t_seg = t[start_clamped:end_clamped + 1]
                i_seg = i[start_clamped:end_clamped + 1]
                v_seg = v[start_clamped:end_clamped + 1]

                t0 = float(t_seg[0])
                t_rel = t_seg - t0

                out.write("start\t\t\n")
                for k in range(len(t_rel)):
                    out.write(f"{t_rel[k]}\t{i_seg[k]}\t{v_seg[k]}\n")

    print(f"Done. Pulses written to: {pulses_out_path}")

if __name__ == "__main__":
    main()
