"""
Geometry calculations for Kerto-Ripa elements according to ETA-07/0029.
"""

from app.schemas.kertoripa import KertoRipaCrossSectionInput, RibPosition, KertoRipaSectionType, KertoRipaSpanInput
from app.domain.kertoripa.materials import KERTO_S, KERTO_Q


def calculate_spacing(element_width_mm: float, n_ribs: int, b_w_mm: float) -> float:
    """Calculates the clear distance between adjacent webs (b_f)."""
    if n_ribs < 2:
        return 0.0
    return (element_width_mm - (n_ribs * b_w_mm)) / (n_ribs - 1)


def calculate_ei_ef(b1: float, b2: float, b3: float, h1: float, h2: float, h3: float,
                    E1: float, E2: float, E3: float) -> tuple[float, float, float, float]:
    """
    Calculates the effective bending stiffness (EI_ef) and neutral axis positions.
    b1: top flange effective width
    b2: web width
    b3: bottom flange effective width
    h1: top flange height
    h2: web height
    h3: bottom flange height
    E1, E2, E3: modulus of elasticity for top, web, bottom respectively
    
    Returns:
        EI_ef: Effective bending stiffness in N mm^2
        a1: Distance from neutral axis to top slab centroid
        a2: Distance from neutral axis to web centroid
        a3: Distance from neutral axis to bottom slab centroid
    """
    A1 = b1 * h1
    A2 = b2 * h2
    A3 = b3 * h3
    
    I1 = b1 * h1**3 / 12.0 if h1 > 0 else 0.0
    I2 = b2 * h2**3 / 12.0 if h2 > 0 else 0.0
    I3 = b3 * h3**3 / 12.0 if h3 > 0 else 0.0
    
    # Distance a2 (neutral axis distance from center of web)
    # Using equation A.8
    numerator = E1 * A1 * (h1 + h2) / 2.0 - E3 * A3 * (h2 + h3) / 2.0
    denominator = E1 * A1 + E2 * A2 + E3 * A3
    
    if denominator == 0:
        return 0.0, 0.0, 0.0, 0.0
        
    a2 = numerator / denominator
    
    a1 = 0.5 * h1 + 0.5 * h2 - a2
    a3 = 0.5 * h3 + 0.5 * h2 + a2
    
    EI_ef = (E1 * I1 + E2 * I2 + E3 * I3) + (E1 * A1 * a1**2 + E2 * A2 * a2**2 + E3 * A3 * a3**2)
    
    return EI_ef, a1, a2, a3


class KertoRipaGeometryData:
    """Contains all geometry and cross-section parameters for one structural rib."""
    
    def __init__(self, cs: KertoRipaCrossSectionInput, span: KertoRipaSpanInput, position: RibPosition = RibPosition.MIDDLE):
        self.cs = cs
        self.span = span
        self.position = position
        
        self.b_f = calculate_spacing(cs.element_width_mm, cs.n_ribs, cs.b_w_mm)
        
        # We assume no overhang for edge ribs as standard default unless specified
        self.b_overhang = 0.0 
        
        self.b_ef_top_SLS = 0.0
        self.b_ef_top_ULS = 0.0
        if self.cs.h_f1_mm:
            self.b_ef_top_SLS = self._calculate_b_ef(self.cs.h_f1_mm, is_uls=False, is_top=True)
            self.b_ef_top_ULS = self._calculate_b_ef(self.cs.h_f1_mm, is_uls=True, is_top=True)
            
        self.b_ef_bot_SLS = 0.0
        self.b_ef_bot_ULS = 0.0
        if self.cs.h_f2_mm:
            self.b_ef_bot_SLS = self._calculate_b_ef(self.cs.h_f2_mm, is_uls=False, is_top=False)
            self.b_ef_bot_ULS = self._calculate_b_ef(self.cs.h_f2_mm, is_uls=True, is_top=False)
            
        # Moduli of elasticity
        self.E_web = KERTO_S["E_mean"]
        self.E_top = KERTO_Q["E_mean"] if self.cs.h_f1_mm else 0.0
        
        # Bottom material is Kerto-S for open box, otherwise Kerto-Q
        if self.cs.section_type == KertoRipaSectionType.OPEN_BOX:
            self.E_bot = KERTO_S["E_mean"] if self.cs.h_f2_mm else 0.0
        else:
            self.E_bot = KERTO_Q["E_mean"] if self.cs.h_f2_mm else 0.0
            
        h1 = self.cs.h_f1_mm or 0.0
        h2 = self.cs.h_w_mm
        h3 = self.cs.h_f2_mm or 0.0
        
        # Calculates EI_ef parameters
        self.EI_ef_ULS, self.a1_ULS, self.a2_ULS, self.a3_ULS = calculate_ei_ef(
            b1=self.b_ef_top_ULS, b2=self.cs.b_w_mm, b3=self.b_ef_bot_ULS,
            h1=h1, h2=h2, h3=h3,
            E1=self.E_top, E2=self.E_web, E3=self.E_bot
        )
        
        self.EI_ef_SLS, self.a1_SLS, self.a2_SLS, self.a3_SLS = calculate_ei_ef(
            b1=self.b_ef_top_SLS, b2=self.cs.b_w_mm, b3=self.b_ef_bot_SLS,
            h1=h1, h2=h2, h3=h3,
            E1=self.E_top, E2=self.E_web, E3=self.E_bot
        )

    def _calculate_b_ef(self, h_f: float, is_uls: bool, is_top: bool) -> float:
        """Calculates effective flange width according to A.2 and A.3."""
        L_ef = self.span.L_ef_mm
        b_f = self.b_f
        b_w = self.cs.b_w_mm
        
        if self.position == RibPosition.MIDDLE:
            b_R_geom = 0.5 * b_f
            b_L_geom = 0.5 * b_f
        else:
            b_R_geom = 0.5 * b_f
            b_L_geom = self.b_overhang
        
        # Open Box restrictions (A.2c, A.2d, A.3c, A.3d)
        if not is_top and self.cs.section_type == KertoRipaSectionType.OPEN_BOX and self.cs.b_actual_mm:
            # Flange extent from edge of web
            flange_extent = max(0.0, (self.cs.b_actual_mm - b_w) / 2.0)
            b_R_geom = min(b_R_geom, flange_extent)
            b_L_geom = min(b_L_geom, flange_extent)
            
        b_L = 0.0
        b_R = 0.0
        
        if is_uls:
            # Equations A.3a, A.3b, A.3c, A.3d
            b_L = min(0.05 * L_ef, 12 * h_f, b_L_geom)
            b_R = min(0.05 * L_ef, 12 * h_f, b_R_geom)
        else:
            # Equations A.2a, A.2b, A.2c, A.2d
            b_L = min(0.05 * L_ef, b_L_geom)
            b_R = min(0.05 * L_ef, b_R_geom)
            
        return b_L + b_w + b_R
