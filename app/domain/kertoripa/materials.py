"""
Kerto-Ripa material properties and design constants based on ETA-07/0029.
"""

from typing import Dict

# Kerto-S (Ribs / Webs)
KERTO_S = {
    "E_mean": 13800.0,
    "E_05": 11600.0,
    "f_m_k": 44.0,       # Characteristic bending strength
    "f_c_0_k": 35.0,     # Compressive strength parallel to grain
    "f_t_0_k": 35.0,     # Tensile strength parallel to grain
    "f_v_0_edge_k": 4.1, # Edgewise shear strength
    "f_v_0_flat_k": 2.3, # Flatwise shear strength
    "f_c_90_k": 6.0,     # Compressive strength perpendicular to grain
    "f_t_90_k": 0.5,     # Tensile strength perpendicular to grain
    "G_mean": 600.0,     # Mean shear modulus
    "E_90_mean": 430.0,  # Mean modulus of elasticity perpendicular to grain
    "rho_k": 480.0       # Characteristic density
}

# Kerto-Q (Flanges / Slabs)
KERTO_Q = {
    "E_mean": 10500.0,
    "E_05": 8800.0,
    "f_c_0_k": 26.0,     # Compressive strength parallel to grain
    "f_t_0_k": 26.0,     # Tensile strength parallel to grain
    "f_v_0_flat_k": 1.3, # Flatwise shear strength (rolling shear)
    "f_m_0_flat_k": 32.0,# Flatwise bending strength
    "f_c_90_flat_k": 2.8,# Flatwise compressive strength perpendicular to grain
    "E_90_mean": 2000.0, # Mean modulus of elasticity perpendicular to grain
    "G_mean": 600.0,     # Mean shear modulus
    "rho_k": 480.0       # Characteristic density
}

# Load Duration and Service Class factors (according to standard LVL values)
K_MOD_VALUES: Dict[str, Dict[str, float]] = {
    "permanent": {"service_class_1": 0.60, "service_class_2": 0.60, "service_class_3": 0.50},
    "long_term": {"service_class_1": 0.70, "service_class_2": 0.70, "service_class_3": 0.55},
    "medium_term": {"service_class_1": 0.80, "service_class_2": 0.80, "service_class_3": 0.65},
    "short_term": {"service_class_1": 0.90, "service_class_2": 0.90, "service_class_3": 0.70},
    "instantaneous": {"service_class_1": 1.10, "service_class_2": 1.10, "service_class_3": 0.90},
}

K_DEF_VALUES: Dict[str, float] = {
    "service_class_1": 0.60,
    "service_class_2": 0.80,
    "service_class_3": 2.00,
}

def get_k_mod(load_duration: str, service_class: str) -> float:
    """Returns the modification factor k_mod for the given load duration and service class."""
    return K_MOD_VALUES.get(load_duration, {}).get(service_class, 0.80)

def get_k_def(service_class: str) -> float:
    """Returns the deformation factor k_def for the given service class."""
    return K_DEF_VALUES.get(service_class, 0.60)

# Default Partial Safety Factors (Gamma) - Finnish NA values used in the manual
GAMMA_M_LVL = 1.2
GAMMA_M_CONN = 1.2
