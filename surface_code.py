import stim
from typing import Dict, List, Tuple
from noise import NoiseModel

class SurfaceCode:
    """Encapsulates geometry and circuit-stage builders for a surface code.

    Attributes:
        d: distance
        data: mapping from (i,j) -> qubit index (only data positions)
        data_qubits, x_qubits, z_qubits: lists of qubit indices in index order
        pos_by_index: list mapping qubit index -> (x,y) position
    """

    def __init__(self, d: int):
        self.d = d
        self.data: Dict[Tuple[int, int], int] = {}
        pos_by_index_dict: Dict[int, Tuple[float, float]] = {}
        q = 0

        data_ordered: List[Tuple[Tuple[int, int], int]] = []
        x_ordered: List[Tuple[Tuple[float, float], int]] = []
        z_ordered: List[Tuple[Tuple[float, float], int]] = []

        # data positions
        for i in range(d):
            for j in range(d):
                pos = (i, j)
                self.data[pos] = q
                data_ordered.append((pos, q))
                pos_by_index_dict[q] = pos
                q += 1

        # interior X ancillas
        for i in range(d - 1):
            for j in range(d - 1):
                if (i + j) % 2 == 0:
                    pos = (i + 0.5, j + 0.5)
                    x_ordered.append((pos, q))
                    pos_by_index_dict[q] = pos
                    q += 1

        # left/right X boundary ancillas
        for i in range(d - 1):
            if i % 2 == 0:
                pos = (d - 0.5, i + 0.5)
            else:
                pos = (-0.5, i + 0.5)
            x_ordered.append((pos, q))
            pos_by_index_dict[q] = pos
            q += 1

        # interior Z ancillas
        for i in range(d - 1):
            for j in range(d - 1):
                if (i + j) % 2 == 1:
                    pos = (i + 0.5, j + 0.5)
                    z_ordered.append((pos, q))
                    pos_by_index_dict[q] = pos
                    q += 1

        # top/bottom Z boundary ancillas
        for j in range(d - 1):
            if j % 2 == 1:
                pos = (j + 0.5, d - 0.5)
            else:
                pos = (j + 0.5, -0.5)
            z_ordered.append((pos, q))
            pos_by_index_dict[q] = pos
            q += 1

        self.pos_by_index: List[Tuple[float, float]] = [pos_by_index_dict[i] for i in range(q)]

        self.data_qubits: List[int] = [idx for _, idx in data_ordered]
        self.x_qubits: List[int] = [idx for _, idx in x_ordered]
        self.z_qubits: List[int] = [idx for _, idx in z_ordered]

    def neighbors(self, pos: Tuple[float, float]) -> List[Tuple[float, float]]:
        x, y = pos
        return [(x - 0.5, y - 0.5), (x - 0.5, y + 0.5), (x + 0.5, y - 0.5), (x + 0.5, y + 0.5)]

    @staticmethod
    def get_meas_idx(q: int, measured_qubits: List[int]) -> int:
        measured = list(measured_qubits)
        idx = measured.index(q)
        return idx - len(measured)

    def build_init_circ(self, hadamard_parity: int, initialize: bool) -> stim.Circuit:
        c = stim.Circuit()
        if initialize:
            # QUBIT_COORDS for all qubits (in index order)
            for q, pos in enumerate(self.pos_by_index):
                c.append("QUBIT_COORDS", [q], [pos[0], pos[1]])
            c.append("TICK")
            c.append("R", self.data_qubits)
            c.append("R", self.x_qubits)
            c.append("R", self.z_qubits)
            c.append("TICK")

        c.append("H", [q for q in self.data_qubits if q % 2 == hadamard_parity])
        c.append("TICK")
        return c

    def build_stab_mcirc(self, hadamard_parity: int) -> stim.Circuit:
        c = stim.Circuit()
        c.append("H", self.x_qubits)
        c.append("H", self.z_qubits)
        c.append("TICK")

        order_x = [0, 1, 2, 3]
        order_z = [0, 2, 1, 3]
        for r in range(4):
            for q in self.x_qubits:
                pos = self.pos_by_index[q]
                nbr_pos = self.neighbors(pos)[order_x[r]]
                if nbr_pos in self.data:
                    c.append("CZ", [self.data[nbr_pos], q])

            for q in self.z_qubits:
                pos = self.pos_by_index[q]
                nbr_pos = self.neighbors(pos)[order_z[r]]
                if nbr_pos in self.data:
                    c.append("CZ", [q, self.data[nbr_pos]])

            c.append("TICK")

            if r == 3:
                c.append("H", self.x_qubits)
                c.append("H", self.z_qubits)
                c.append("TICK")
            elif r == 1:
                pass
            else:
                c.append("H", self.data_qubits)
                c.append("TICK")

        return c

    def build_stab_rcirc(self) -> Tuple[stim.Circuit, List[int]]:
        c = stim.Circuit()
        c.append("MR", self.x_qubits)
        c.append("MR", self.z_qubits)
        c.append("TICK")
        rcirc_measured = self.x_qubits + self.z_qubits
        return c, rcirc_measured

    def build_data_rcirc(self, hadamard_parity: int) -> Tuple[stim.Circuit, List[int]]:
        c = stim.Circuit()
        c.append("H", [q for q in self.data_qubits if q % 2 == hadamard_parity])
        c.append("TICK")
        c.append("M", self.data_qubits)
        c.append("TICK")
        data_measured = self.data_qubits
        return c, data_measured

    def build_detectors_init(self, measured_qubits: List[int], deterministic_anc: List[int]) -> stim.Circuit:
        c = stim.Circuit()
        for q in deterministic_anc:
            meas_idx = SurfaceCode.get_meas_idx(q, measured_qubits)
            c.append("DETECTOR", [stim.target_rec(meas_idx)])
        return c

    def build_detectors_round(self, rcirc_measured: List[int]) -> stim.Circuit:
        c = stim.Circuit()
        for q in (self.x_qubits + self.z_qubits):
            meas_idx = SurfaceCode.get_meas_idx(q, rcirc_measured)
            prev_meas_idx = meas_idx - len(rcirc_measured)
            c.append("DETECTOR", [stim.target_rec(meas_idx), stim.target_rec(prev_meas_idx)])
        c.append("TICK")
        return c

    def build_detectors_final(self, data_circ_measured: List[int], rcirc_measured: List[int]) -> stim.Circuit:
        c = stim.Circuit()
        for q in (self.z_qubits + self.x_qubits):
            meas_idx = SurfaceCode.get_meas_idx(q, data_circ_measured)
            prev_meas_idx = meas_idx - len(rcirc_measured)
            c.append("DETECTOR", [stim.target_rec(meas_idx), stim.target_rec(prev_meas_idx)])
        return c

    def build_detectors_stabs(self, data_circ_measured: List[int], deterministic_anc: List[int]) -> stim.Circuit:
        c = stim.Circuit()
        for q in deterministic_anc:
            pos = self.pos_by_index[q]
            meas_idx = SurfaceCode.get_meas_idx(q, data_circ_measured)
            nbrs = [nbr for nbr in self.neighbors(pos) if nbr in self.data]
            nbrs_idxs = [self.data[nbr] for nbr in nbrs]
            data_idx = [SurfaceCode.get_meas_idx(nbr, data_circ_measured) for nbr in nbrs_idxs]
            c.append("DETECTOR", [stim.target_rec(meas_idx), *[stim.target_rec(i) for i in data_idx]])
        return c

    def observable_include(self, data_circ_measured: List[int], basis: str) -> List[object]:
        # Return a list of stim.target_rec for the logical observable locations.
        log_coord = 1 if basis == "Z" else 0
        log_op = [stim.target_rec(SurfaceCode.get_meas_idx(i, data_circ_measured)) for i, pos in enumerate(self.pos_by_index) if pos[log_coord] == 0]
        return log_op

    def build_circuit(self, n_rounds: int, basis: str, initialize: bool = True) -> stim.Circuit:
        hadamard_parity = 1 if basis == "Z" else 0
        deterministic_anc = self.x_qubits if basis == "Z" else self.z_qubits
        init = self.build_init_circ(hadamard_parity, initialize)
        stab_m = self.build_stab_mcirc(hadamard_parity)
        stab_r, rcirc_measured = self.build_stab_rcirc()
        data_r, _ = self.build_data_rcirc(hadamard_parity)

        detectors_init = self.build_detectors_init(rcirc_measured, deterministic_anc)
        detectors_round = self.build_detectors_round(rcirc_measured)
        detectors_final = self.build_detectors_final(rcirc_measured + self.data_qubits, rcirc_measured)
        detectors_stabs = self.build_detectors_stabs(rcirc_measured + self.data_qubits, deterministic_anc)

        stab_circ = stab_m + stab_r

        if n_rounds == 1:
            circuit = init + (stab_circ + detectors_init + data_r + detectors_stabs)
        elif n_rounds == 2:
            circuit = init + (stab_circ + detectors_init) + (stab_circ + data_r + detectors_final + detectors_stabs)
        else:
            circuit = (
                init
                + (stab_circ + detectors_init)
                + (stab_circ + detectors_round) * (n_rounds - 2)
                + (stab_circ + data_r + detectors_final + detectors_stabs)
            )

        # attach logical observable
        log_op = self.observable_include(rcirc_measured + self.data_qubits, basis)
        if log_op:
            circuit.append("OBSERVABLE_INCLUDE", log_op, 0)

        return circuit
    
    def build_ideal_circuit(self, n_rounds, basis) -> stim.Circuit:
        """Build a noisy version of the surface code circuit."""
        prep_circ = stim.Circuit()
        # QUBIT_COORDS for all qubits (in index order)
        for q, pos in enumerate(self.pos_by_index):
            prep_circ.append("QUBIT_COORDS", [q], [pos[0], pos[1]])
        prep_circ.append("TICK")

        prep_circ.append("CX", [x for i, d in enumerate(self.data_qubits) for x in (stim.target_sweep_bit(i), d)])
        prep_circ.append("R", self.x_qubits + self.z_qubits)
        prep_circ.append("TICK")
        
        main_circ = self.build_circuit(n_rounds=n_rounds, basis=basis, initialize=False)
        noisy_circuit = prep_circ + main_circ
        return noisy_circuit
    
    def build_noisy_circuit(self, p: float, n_rounds, basis) -> stim.Circuit:
        """Build a noisy version of the surface code circuit."""
        prep_circ = stim.Circuit()
        # QUBIT_COORDS for all qubits (in index order)
        for q, pos in enumerate(self.pos_by_index):
            prep_circ.append("QUBIT_COORDS", [q], [pos[0], pos[1]])
        prep_circ.append("TICK")

        prep_circ.append("CX", [x for i, d in enumerate(self.data_qubits) for x in (stim.target_sweep_bit(i), d)])
        prep_circ.append("R", self.x_qubits + self.z_qubits)
        prep_circ.append("TICK")
        prep_circ.append("X_ERROR", self.data_qubits + self.x_qubits + self.z_qubits, 2 * p)
        prep_circ.append("TICK")
        
        main_circ = self.build_circuit(n_rounds=n_rounds, basis=basis, initialize=False)
        noisy_main_circ = NoiseModel.SI1000(p).noisy_circuit(main_circ)
        noisy_circuit = prep_circ + noisy_main_circ
        return noisy_circuit

if __name__ == "__main__":
    sc = SurfaceCode(3)
    sc.build_noisy_circuit(0.01)