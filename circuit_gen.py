import stim
from surface_code import SurfaceCode


def build_surface_code_circuit(
    d: int, n_rounds: int, basis: str, prep: bool = True
) -> stim.Circuit:
    """Backward-compatible wrapper that builds a surface-code Stim circuit.

    Delegates to `SurfaceCode` which exposes methods building individual stages.
    """
    sc = SurfaceCode(d)
    return sc.build_ideal_circuit(n_rounds=n_rounds, basis=basis)

def build_noisy_surface_code_circuit(
    d: int, p: float, n_rounds: int, basis: str
) -> stim.Circuit:
    """Backward-compatible wrapper that builds a noisy surface-code Stim circuit.

    Delegates to `SurfaceCode` which exposes methods building individual stages.
    """
    sc = SurfaceCode(d)
    return sc.build_noisy_circuit(p=p, n_rounds=n_rounds, basis=basis)