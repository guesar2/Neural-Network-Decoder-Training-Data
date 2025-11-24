import tools
from pathlib import Path

for d in [3, 5, 7]:
    for p in [0.0035, 0.004, 0.0045]:
        for rounds in [1, 25]:
            for basis in ["X", "Z"]:
                
                dir = Path(f"/home/guesar/training_data/simulated_data/b{basis}_d{d}_r{rounds:02d}_p{p}")
                dir.mkdir(exist_ok=True)

                tools.generate_extra_data(dir, format="b8")
