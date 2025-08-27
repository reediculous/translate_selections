#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_pulses(pulses_path: Path):
    pulses = []
    current_pulse_t = []
    current_pulse_i = []

    with pulses_path.open("r", encoding="utf-8") as f:
        header = next(f)  # skip "time\tcurrent\tvoltage"
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("start"):
                # save previous pulse if exists
                if current_pulse_t and current_pulse_i:
                    pulses.append((np.array(current_pulse_t), np.array(current_pulse_i)))
                current_pulse_t = []
                current_pulse_i = []
                continue
            try:
                t, i, v = line.split("\t")
                current_pulse_t.append(float(t))
                current_pulse_i.append(float(i))
            except ValueError:
                continue
        # save last pulse
        if current_pulse_t and current_pulse_i:
            pulses.append((np.array(current_pulse_t), np.array(current_pulse_i)))
    return pulses

def main():
    script_dir = Path(__file__).resolve().parent
    pulses_path = script_dir / "pulses.txt"

    if not pulses_path.exists():
        print(f"[ERROR] pulses.txt not found at {pulses_path}")
        return

    pulses = load_pulses(pulses_path)

    if not pulses:
        print("[WARN] No pulses found in pulses.txt")
        return

    # Plot each pulse
    for idx, (t, i) in enumerate(pulses, start=1):
        plt.figure()
        plt.plot(t, i, label=f"Pulse {idx}")
        plt.xlabel("Time")
        plt.ylabel("Current")
        plt.title(f"Pulse {idx}")
        plt.legend()
        plt.grid(True)

        plt.show()

if __name__ == "__main__":
    main()
