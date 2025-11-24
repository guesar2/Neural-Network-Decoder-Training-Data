from pathlib import Path
import stim
from circuit_gen import build_surface_code_circuit, build_noisy_surface_code_circuit
from noise import NoiseModel
import numpy as np
import os
import sinter 


def save_b8(shots: list[list[bool]]) -> bytes:
    output = b""
    for shot in shots:
        bytes_per_shot = (len(shot) + 7) // 8
        v = 0
        for b in reversed(shot):
            v <<= 1
            v += int(b)
        output += v.to_bytes(bytes_per_shot, "little")
    return output

def save_01(shots: list[list[bool]]) -> str:
    output = ""
    for shot in shots:
        for sample in shot:
            output += '1' if sample else '0'
        output += "\n"
    return output

def parse_b8(data: bytes, bits_per_shot: int) -> list[list[bool]]:
    shots = []
    bytes_per_shot = (bits_per_shot + 7) // 8
    for offset in range(0, len(data), bytes_per_shot):
        shot = []
        for k in range(bits_per_shot):
            byte = data[offset + k // 8]
            bit = (byte >> (k % 8)) % 2 == 1
            shot.append(bit)
        shots.append(shot)
    return shots

def parse_01(data: str) -> list[list[bool]]:
    shots = []
    for line in data.split("\n"):
        if not line:
            continue
        shot = []
        for c in line:
            assert c in "01"
            shot.append(c == "1")
        shots.append(shot)
    return shots


def generate_measurements(directory: Path, shots: int, format: str = "b8"):
    measurements_path = str(directory / f"measurements.{format}")
    circuit = stim.Circuit.from_file(str(directory / "circuit_noisy.stim"))
    with open(measurements_path, "a") as f:
        circuit.compile_sampler().sample_write(
            shots=shots, filepath=measurements_path, format=format
        )


def generate_sweep_b8_data(distance: int, shots: int):
    # either all qubits are 1 or all qubits are 0
    random_sweep = np.random.choice([True, False], size=(shots, 1))
    random_sweep = np.repeat(random_sweep, distance * distance, axis=1)
    sweep_b8 = save_b8(random_sweep)
    return sweep_b8

def generate_sweep_data(distance: int, shots: int, dist: "str"):
    n_bits = distance * distance
    if dist == "rnd":
        sweep = np.random.choice([True, False], size=(shots, 1))
        sweep = np.repeat(sweep, n_bits, axis=1)
    elif dist == "half-half":
        ones = np.ones((shots // 2, n_bits))
        zeros = np.zeros((shots // 2, n_bits))
        sweep = np.vstack([ones, zeros])
    else:
        sweep = None
    return sweep
    
def save_sweep(distance: int, shots: int, path: Path, write_mode: str = "wb", dist: str = "rnd", format: str = "b8"):
    sweep_data = generate_sweep_data(distance, shots, dist)
    if format == "b8":
        data = save_b8(sweep_data)
    elif format == "01":
        data = save_01(sweep_data)
    else:
        data = None
    sweep_path = str(path / f"sweep.{format}")
    with open(sweep_path, write_mode) as f:
        f.write(data)

def generate_extra_data(directory: Path, format: str = "b8", skip_sweep: bool = True):
    measurements_path = str(directory / f"measurements.{format}")
    detectors_path = str(directory / f"detection_events.{format}")
    obs_path = str(directory / f"obs_flips_actual.01")
    if not skip_sweep:
        sweep_path = str(directory / f"sweep.{format}")
    circuit = stim.Circuit.from_file(str(directory / "circuit_ideal.stim"))
    converter = circuit.compile_m2d_converter()
    if skip_sweep:
        converter.convert_file(
            measurements_filepath=measurements_path,
            measurements_format=format,
            detection_events_filepath=detectors_path,
            detection_events_format=format,
            obs_out_filepath=obs_path,
            obs_out_format="01",
        )
    else:
        converter.convert_file(
            measurements_filepath=measurements_path,
            measurements_format=format,
            sweep_bits_filepath=sweep_path,
            sweep_bits_format=format,
            detection_events_filepath=detectors_path,
            detection_events_format=format,
            obs_out_filepath=obs_path,
            obs_out_format="01",
        )


def generate_data(directory: Path, shots: int):
    measurements_path = str(directory / "measurements.b8")
    detectors_path = str(directory / "detection_events.b8")
    obs_path = str(directory / "obs_flips_actual.01")
    circuit = stim.Circuit.from_file(str(directory / "circuit_noisy.stim"))
    circuit.compile_sampler().sample_write(
        shots=shots, filepath=measurements_path, format="b8"
    )

    converter = circuit.compile_m2d_converter()

    converter.convert_file(
        measurements_filepath=measurements_path,
        measurements_format="b8",
        detection_events_filepath=detectors_path,
        detection_events_format="b8",
        obs_out_filepath=obs_path,
        obs_out_format="01",
    )


def get_directory(distance: int, rounds: int, p: float, basis: str) -> Path:
    return Path(f"./simulated_data/b{basis}_d{distance}_r{rounds:02d}_p{p}")


def write_circuit_files(distance: int, rounds: int, p: float, basis: str, path = None):
    if path is None:
        path = Path(f"./simulated_data/b{basis}_d{distance}_r{rounds:02d}_p{p}")
    path.mkdir(exist_ok=True)
    circuit_ideal = build_surface_code_circuit(d=distance, n_rounds=rounds, basis=basis)
    circuit_ideal.to_file(str(path / "circuit_ideal.stim"))
    circuit_noisy = build_noisy_surface_code_circuit(
        d=distance, p=p, n_rounds=rounds, basis=basis
    )
    circuit_noisy.to_file(str(path / "circuit_noisy.stim"))




