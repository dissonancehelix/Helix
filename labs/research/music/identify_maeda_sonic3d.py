import os
from pathlib import Path

def identify_maeda_tracks():
    dir_path = Path(r"C:\Users\dissonance\Music\VGM\S\Sonic 3D Blast")
    maeda_tracks = []
    for p in dir_path.glob("*.tag"):
        with open(p, "rb") as f:
            data = f.read()
            # Tatsuyuki is usually credited in the Artist field of APEv2
            if b"Tatsuyuki Maeda" in data:
                maeda_tracks.append(p.stem.replace(".vgm", ""))
    
    print("Maeda Tracks in Sonic 3D Blast:")
    for t in maeda_tracks:
        print(f"  {t}")
    return maeda_tracks

if __name__ == "__main__":
    identify_maeda_tracks()
