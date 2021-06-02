import numpy as np
import matplotlib.pyplot as plt
from VQE import VQE
from qiskit.algorithms import VQE as VQE_qiskit
from qiskit.providers.aer import QasmSimulator
from qiskit.providers.aer.noise import NoiseModel
from GroupingAlgorithm import *
from utils import *
# Importing standard Qiskit libraries
from qiskit import IBMQ
from qiskit.providers.aer import AerSimulator
from qiskit import Aer
from qiskit.circuit.library import EfficientSU2
from qiskit.utils.quantum_instance import QuantumInstance
from qiskit.algorithms import NumPyMinimumEigensolver
from qiskit_nature.circuit.library import HartreeFock
from qiskit_nature.transformers import FreezeCoreTransformer
from qiskit_nature.drivers import PyQuanteDriver
from qiskit_nature.problems.second_quantization.electronic import ElectronicStructureProblem
from qiskit_nature.mappers.second_quantization import ParityMapper
from qiskit_nature.converters.second_quantization.qubit_converter import QubitConverter
from qiskit.algorithms.optimizers import SPSA
from qiskit_nature.circuit.library import UCCSD
from time import time
from qiskit.test.mock import FakeVigo
device_backend = FakeVigo()
import os

from joblib import Parallel, delayed

os.environ['QISKIT_IN_PARALLEL'] = 'TRUE'

# from palettable.cartocolors.sequential import BluGrn_7, OrYel_7, Magenta_7

# plt.rc('text', usetex=True)
# plt.rc('font', family='serif')


# %%

def molecule(d, quantum_instance, conectivity):
    E = np.zeros(4)

    def callback(a, b):
        print(a)

    def callback_2(a, b, c, d):
        print(c)

    qubit_op, init_state, converter, num_particles, num_spinorbitals = LiH(d, initial_state=True)
    num_qubits = qubit_op.num_qubits

    # Exact energy
    E[0] = NumPyMinimumEigensolver().compute_minimum_eigenvalue(qubit_op).eigenvalue.real
    print('Exact energy: {}'.format(E[0]))
    # VQE
    optimizer = SPSA(maxiter=100, last_avg=1)
    ansatz = init_state.compose(EfficientSU2(num_qubits, ['ry', 'rz'], entanglement='linear', reps=1))
    # ansatz = UCCSD(converter, num_particles, num_spinorbitals, initial_state=init_state)
    num_var = ansatz.num_parameters
    # initial_params = np.random.rand(num_var)
    initial_params = [0.01] * num_var

    # solver_TPB = VQE(ansatz, optimizer, initial_params, grouping='TPB', quantum_instance=quantum_instance,
    #                  callback=callback)
    # solver_ENT = VQE(ansatz, optimizer, initial_params, grouping='Entangled', quantum_instance=quantum_instance,
    #                  callback=callback)
    # solver_HEEM = VQE(ansatz, optimizer, initial_params, grouping='Entangled', conectivity=conectivity,
    #                   quantum_instance=quantum_instance, callback=callback)
    algorithm = VQE_qiskit(ansatz,
                           optimizer=optimizer,
                           quantum_instance=quantum_instance,
                           callback=callback_2,
                           initial_point=initial_params)

    print('-' * 100)
    print('Computing TPB:')
    start = time()
    # E[1] = solver_TPB.compute_minimum_eigenvalue(qubit_op).eigenvalue.real
    result = algorithm.compute_minimum_eigenvalue(qubit_op)
    finish = time()

    print('Total time {}'.format(finish - start))

    # print('-' * 100)
    # print('Computing ENT:')
    # E[2] = solver_ENT.compute_minimum_eigenvalue(qubit_op).eigenvalue.real
    #
    # print('-' * 100)
    # print('Computing HEEM:')
    # E[3] = solver_HEEM.compute_minimum_eigenvalue(qubit_op).eigenvalue.real

    return E


# %%
def molecule_potentials_comparison(distances, quantum_instance, conectivity, file_name_out):
    E_EXACT = np.zeros_like(distances)
    E_TPB = np.zeros_like(distances)
    E_ENT = np.zeros_like(distances)
    E_HEEM = np.zeros_like(distances)

    results = Parallel(n_jobs=10)(delayed(molecule)(d, quantum_instance, conectivity) for d in distances)
    for i in range(len(distances)):
        E_EXACT[i] = results[i][0]
        E_TPB[i] = results[i][1]
        E_ENT[i] = results[i][2]
        E_HEEM[i] = results[i][3]

    # Save results
    np.savez(file_name_out, distances=distances, E_EXACT=E_EXACT, E_TPB=E_TPB, E_ENT=E_ENT, E_HEEM=E_HEEM)

    return True


# %% Test - molecule_potentials_comparison
IBMQ.load_account()
provider = IBMQ.get_provider(hub='ibm-q', group='open', project='main')
backend_santiago = provider.get_backend('ibmq_santiago')

distances = [0.5, 1.5, 5]  # np.linspace(0.5,5,3)
backend = Aer.get_backend('qasm_simulator')
device = QasmSimulator.from_backend(device_backend)
coupling_map = device.configuration().coupling_map
noise_model = NoiseModel.from_backend(device)
basis_gates = noise_model.basis_gates
NUM_SHOTS = 2 ** 13  # Number of shots for each circuit
qi = QuantumInstance(backend=backend, coupling_map=coupling_map, noise_model=noise_model, shots=NUM_SHOTS)

file_name_out = 'data/LiH_' + qi.backend_name + '_NUM_SHOTS=' + str(NUM_SHOTS) + '_dist=' + str(
    distances[0]) + '_to_' + str(distances[-1])

# molecule_potentials_comparison(distances, qi, conectivity, file_name_out)
test = molecule(0.2, qi, None)

# # %% Load and print data
# data = np.load(file_name_out + '.npz')
#
# E_EXACT = data['E_EXACT']
# E_TPB = data['E_TPB']
# E_ENT = data['E_ENT']
# E_HEEM = data['E_HEEM']
#
# fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 4.5))
# ax.set_xlabel(r'$d$ ')
# ax.set_ylabel(r'$E$ ')
#
# ax.plot(distances, E_TPB)
# ax.plot(distances, E_ENT)
# ax.plot(distances, E_HEEM)
# ax.plot(distances, E_EXACT, color='black', linestyle='--')
#
# ax.legend(['$TPB$', '$ENT$', '$HEEM$'])
#
# plt.savefig("Figures\E vs d.pdf")