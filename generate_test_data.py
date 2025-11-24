import tools
from pathlib import Path


d = 3
rounds = 1
p = 0.5
basis = "Z"
shots = 10

dir = Path(f"/home/guesar/training_data/test_data/b{basis}_d{d}_r{rounds:02d}_p{p}")
dir.mkdir(exist_ok=True)

tools.write_circuit_files(d, rounds, p, basis, dir)
#tools.save_sweep(d, shots, path = dir, write_mode="w", format="01")
tools.generate_measurements(dir, shots, format="01")
tools.generate_extra_data(dir, format="01")



 


