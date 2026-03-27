import { useState, useEffect } from "react";

/** En desarrollo, URL vacía = mismo origen (Vite reenvía /calculate y /analyze al backend). En build, por defecto 127.0.0.1:8000. */
const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "" : "http://127.0.0.1:8000");

function apiUrl(path) {
  const base = API_BASE.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}

function apiErrorMessage(error) {
  const msg = error?.message ?? "";
  if (msg === "Failed to fetch" || error?.name === "TypeError") {
    return (
      "No se pudo conectar con la API. En la raíz del repo: pip install -e .[dev] y luego " +
      "python -m uvicorn app.main:app --reload (puerto 8000)."
    );
  }
  return msg || "Error al comunicarse con la API.";
}

/** Evita fallos al llamar response.json() con cuerpo vacío o no JSON (p. ej. proxy o error HTML). */
async function readJsonFromResponse(response) {
  const text = await response.text();
  const trimmed = text.trim();
  if (!trimmed) {
    return null;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    const preview = trimmed.length > 200 ? `${trimmed.slice(0, 200)}…` : trimmed;
    throw new Error(
      response.ok
        ? "La API devolvió un cuerpo que no es JSON válido."
        : `Error ${response.status}: ${preview}`,
    );
  }
}

const BACKEND_HINT =
  "Arranca la API en otra terminal (desde la raíz del repo): python -m uvicorn app.main:app --reload (si falla, ejecuta antes: pip install -e .[dev]).";

function formatHttpErrorDetail(status, data) {
  if (data == null) {
    if (status >= 500 && status < 600) {
      return (
        "El proxy de Vite no pudo hablar con el backend (suele ser ECONNREFUSED: nada escucha en 127.0.0.1:8000). " +
        BACKEND_HINT
      );
    }
    return `Error HTTP ${status} (respuesta vacía o sin JSON).`;
  }
  if (Array.isArray(data.detail)) {
    const msgs = data.detail
      .map((item) => (typeof item === "string" ? item : item?.msg))
      .filter(Boolean);
    if (msgs.length) return msgs.join(" | ");
  }
  if (typeof data.detail === "string") return data.detail;
  if (data.message != null) return String(data.message);
  return `Error HTTP ${status}`;
}

const TIMBER_CLASS_DATA = {
  C14: { bending_strength_mpa: 14, tensile_strength_parallel_mpa: 8, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 16, compressive_strength_perpendicular_mpa: 2.0, shear_strength_mpa: 3.0, modulus_mean_gpa: 7.0, modulus_5_percentile_gpa: 4.7, modulus_perpendicular_mean_gpa: 0.23, shear_modulus_mean_gpa: 0.44, density_characteristic_kg_per_m3: 290, density_mean_kg_per_m3: 350 },
  C16: { bending_strength_mpa: 16, tensile_strength_parallel_mpa: 10, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 17, compressive_strength_perpendicular_mpa: 2.2, shear_strength_mpa: 3.2, modulus_mean_gpa: 8.0, modulus_5_percentile_gpa: 5.4, modulus_perpendicular_mean_gpa: 0.27, shear_modulus_mean_gpa: 0.50, density_characteristic_kg_per_m3: 310, density_mean_kg_per_m3: 370 },
  C18: { bending_strength_mpa: 18, tensile_strength_parallel_mpa: 11, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 18, compressive_strength_perpendicular_mpa: 2.2, shear_strength_mpa: 3.4, modulus_mean_gpa: 9.0, modulus_5_percentile_gpa: 6.0, modulus_perpendicular_mean_gpa: 0.30, shear_modulus_mean_gpa: 0.56, density_characteristic_kg_per_m3: 320, density_mean_kg_per_m3: 380 },
  C20: { bending_strength_mpa: 20, tensile_strength_parallel_mpa: 12, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 19, compressive_strength_perpendicular_mpa: 2.3, shear_strength_mpa: 3.6, modulus_mean_gpa: 9.5, modulus_5_percentile_gpa: 6.4, modulus_perpendicular_mean_gpa: 0.32, shear_modulus_mean_gpa: 0.59, density_characteristic_kg_per_m3: 330, density_mean_kg_per_m3: 390 },
  C22: { bending_strength_mpa: 22, tensile_strength_parallel_mpa: 13, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 20, compressive_strength_perpendicular_mpa: 2.4, shear_strength_mpa: 3.8, modulus_mean_gpa: 10.0, modulus_5_percentile_gpa: 6.7, modulus_perpendicular_mean_gpa: 0.33, shear_modulus_mean_gpa: 0.63, density_characteristic_kg_per_m3: 340, density_mean_kg_per_m3: 410 },
  C24: { bending_strength_mpa: 24, tensile_strength_parallel_mpa: 14, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 21, compressive_strength_perpendicular_mpa: 2.5, shear_strength_mpa: 4.0, modulus_mean_gpa: 11.0, modulus_5_percentile_gpa: 7.4, modulus_perpendicular_mean_gpa: 0.37, shear_modulus_mean_gpa: 0.69, density_characteristic_kg_per_m3: 350, density_mean_kg_per_m3: 420 },
  C27: { bending_strength_mpa: 27, tensile_strength_parallel_mpa: 16, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 22, compressive_strength_perpendicular_mpa: 2.6, shear_strength_mpa: 4.0, modulus_mean_gpa: 11.5, modulus_5_percentile_gpa: 7.7, modulus_perpendicular_mean_gpa: 0.38, shear_modulus_mean_gpa: 0.72, density_characteristic_kg_per_m3: 370, density_mean_kg_per_m3: 450 },
  C30: { bending_strength_mpa: 30, tensile_strength_parallel_mpa: 18, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 23, compressive_strength_perpendicular_mpa: 2.7, shear_strength_mpa: 4.0, modulus_mean_gpa: 12.0, modulus_5_percentile_gpa: 8.0, modulus_perpendicular_mean_gpa: 0.40, shear_modulus_mean_gpa: 0.75, density_characteristic_kg_per_m3: 380, density_mean_kg_per_m3: 460 },
  C35: { bending_strength_mpa: 35, tensile_strength_parallel_mpa: 21, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 25, compressive_strength_perpendicular_mpa: 2.8, shear_strength_mpa: 4.0, modulus_mean_gpa: 13.0, modulus_5_percentile_gpa: 8.7, modulus_perpendicular_mean_gpa: 0.43, shear_modulus_mean_gpa: 0.81, density_characteristic_kg_per_m3: 400, density_mean_kg_per_m3: 480 },
  C40: { bending_strength_mpa: 40, tensile_strength_parallel_mpa: 24, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 26, compressive_strength_perpendicular_mpa: 2.9, shear_strength_mpa: 4.0, modulus_mean_gpa: 14.0, modulus_5_percentile_gpa: 9.4, modulus_perpendicular_mean_gpa: 0.47, shear_modulus_mean_gpa: 0.88, density_characteristic_kg_per_m3: 420, density_mean_kg_per_m3: 500 },
  C45: { bending_strength_mpa: 45, tensile_strength_parallel_mpa: 27, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 27, compressive_strength_perpendicular_mpa: 3.1, shear_strength_mpa: 4.0, modulus_mean_gpa: 15.0, modulus_5_percentile_gpa: 10.0, modulus_perpendicular_mean_gpa: 0.50, shear_modulus_mean_gpa: 0.94, density_characteristic_kg_per_m3: 440, density_mean_kg_per_m3: 520 },
  C50: { bending_strength_mpa: 50, tensile_strength_parallel_mpa: 30, tensile_strength_perpendicular_mpa: 0.4, compressive_strength_parallel_mpa: 29, compressive_strength_perpendicular_mpa: 3.2, shear_strength_mpa: 4.0, modulus_mean_gpa: 16.0, modulus_5_percentile_gpa: 10.7, modulus_perpendicular_mean_gpa: 0.53, shear_modulus_mean_gpa: 1.00, density_characteristic_kg_per_m3: 460, density_mean_kg_per_m3: 550 },
};

const timberClassOptions = Object.keys(TIMBER_CLASS_DATA).map((grade) => ({ value: grade, label: grade }));

function timberFormValuesFromGrade(grade) {
  const timberClass = TIMBER_CLASS_DATA[grade] ?? TIMBER_CLASS_DATA.C24;
  return {
    grade,
    modulus_of_elasticity_mpa: String(timberClass.modulus_mean_gpa * 1000),
    allowable_bending_stress_mpa: String(timberClass.bending_strength_mpa),
    allowable_shear_stress_mpa: String(timberClass.shear_strength_mpa),
    density_kg_per_m3: String(timberClass.density_mean_kg_per_m3),
  };
}

const initialForm = {
  project_name: "Vivienda unifamiliar",
  geometry: {
    span_m: "4.00",
    spacing_m: "0.40",
    width_mm: "63",
    depth_mm: "200",
  },
  timber: timberFormValuesFromGrade("C24"),
  loads: {
    dead_load_kN_per_m2: "1.5",
    imposed_load_kN_per_m2: "2.0",
    additional_dead_load_kN_per_m2: "0.5",
  },
  criteria: {
    design_standard: "concept-v1",
    max_deflection_ratio: "300",
    active_deflection_ratio: "300",
    instantaneous_deflection_ratio: "300",
    final_deflection_ratio: "300",
  },
  supports: [
    { id: 1, support_type: "pinned", position_m: "0.00" },
    { id: 2, support_type: "roller", position_m: "4.00" },
  ],
};

const supportTypeOptions = [
  { value: "pinned", label: "Articulado" },
  { value: "roller", label: "Rodillo" },
  { value: "fixed", label: "Empotrado" },
];

const actionTypeOptions = [
  { value: "permanent", label: "Permanente" },
  { value: "imposed", label: "Uso" },
  { value: "snow", label: "Nieve" },
  { value: "wind", label: "Viento" },
];

const loadDistributionOptions = [
  { value: "uniform", label: "Uniforme" },
  { value: "line", label: "Lineal" },
  { value: "point", label: "Puntual" },
  { value: "patch", label: "Parche" },
];

const permanentOriginOptions = [
  { value: "self_weight", label: "Peso propio" },
  { value: "non_structural", label: "No estructural" },
  { value: "fixed_equipment", label: "Equipamiento fijo" },
];

const imposedCategoryOptions = [
  { value: "A", label: "A Residencial" },
  { value: "B", label: "B Oficinas" },
  { value: "C", label: "C Reuni�n" },
  { value: "D", label: "D Comercio" },
  { value: "E", label: "E Almacenaje" },
  { value: "F", label: "F Tr�fico ligero" },
  { value: "G", label: "G Tr�fico pesado" },
  { value: "H", label: "H Cubiertas" },
];

const snowPatternOptions = [
  { value: "uniform", label: "Uniforme" },
];

const windPatternOptions = [
  { value: "pressure", label: "Presi�n" },
  { value: "suction", label: "Succi�n" },
];

const imposedCategoryOptionsDisplay = [
  { value: "A", label: "A Residencial" },
  { value: "B", label: "B Oficinas" },
  { value: "C", label: "C Reuni\u00f3n" },
  { value: "D", label: "D Comercio" },
  { value: "E", label: "E Almacenaje" },
  { value: "F", label: "F Tr\u00e1fico ligero" },
  { value: "G", label: "G Tr\u00e1fico pesado" },
  { value: "H", label: "H Cubiertas" },
];

const windPatternOptionsDisplay = [
  { value: "pressure", label: "Presi\u00f3n" },
  { value: "suction", label: "Succi\u00f3n" },
];

const initialProjectActions = [
  {
    id: "g1",
    action_type: "permanent",
    name: "Peso propio",
    value_kN_per_m2: "1.5",
    distribution: "uniform",
    origin: "self_weight",
    imposed_load_category: "A",
    snow_pattern: "uniform",
    wind_pattern: "pressure",
    psi0: "0.7",
    psi1: "0.5",
    psi2: "0.3",
  },
  {
    id: "g2",
    action_type: "permanent",
    name: "Acabados e instalaciones",
    value_kN_per_m2: "0.5",
    distribution: "uniform",
    origin: "non_structural",
    imposed_load_category: "A",
    snow_pattern: "uniform",
    wind_pattern: "pressure",
    psi0: "0.7",
    psi1: "0.5",
    psi2: "0.3",
  },
  {
    id: "q1",
    action_type: "imposed",
    name: "Sobrecarga residencial",
    value_kN_per_m2: "2.0",
    distribution: "uniform",
    origin: "non_structural",
    imposed_load_category: "A",
    snow_pattern: "uniform",
    wind_pattern: "pressure",
    psi0: "0.7",
    psi1: "0.5",
    psi2: "0.3",
  },
];

function createProjectAction(actionType, index) {
  const prefixes = {
    permanent: "g",
    imposed: "q",
    snow: "s",
    wind: "w",
  };
  const names = {
    permanent: "Nueva carga permanente",
    imposed: "Nueva sobrecarga de uso",
    snow: "Nueva carga de nieve",
    wind: "Nueva carga de viento",
  };

  return {
    id: `${prefixes[actionType] ?? "a"}${index}`,
    action_type: actionType,
    name: names[actionType] ?? "Nueva acci�n",
    value_kN_per_m2: "0.0",
    distribution: "uniform",
    origin: actionType === "permanent" ? "non_structural" : "self_weight",
    imposed_load_category: "A",
    snow_pattern: "uniform",
    wind_pattern: "pressure",
    psi0: actionType === "imposed" ? "0.7" : actionType === "snow" ? "0.5" : "0.6",
    psi1: actionType === "imposed" ? "0.5" : actionType === "snow" ? "0.2" : "0.2",
    psi2: actionType === "imposed" ? "0.3" : "0.0",
  };
}

function toNumber(value) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : 0;
}

function summarizeActionsToLegacyLoads(actions) {
  return actions.reduce(
    (accumulator, action) => {
      const value = toNumber(action.value_kN_per_m2);
      if (action.action_type === "permanent") {
        if (action.origin === "self_weight") {
          accumulator.dead_load_kN_per_m2 += value;
        } else {
          accumulator.additional_dead_load_kN_per_m2 += value;
        }
      }
      if (action.action_type === "imposed") {
        accumulator.imposed_load_kN_per_m2 += value;
      }
      return accumulator;
    },
    {
      dead_load_kN_per_m2: 0,
      imposed_load_kN_per_m2: 0,
      additional_dead_load_kN_per_m2: 0,
    },
  );
}

function buildActionCatalogPayload(actions) {
  return {
    actions: actions.map((action) => {
      const basePattern = {
        action_type: action.action_type,
        name: action.name,
        distribution: action.distribution,
        value_kN_per_m2: toNumber(action.value_kN_per_m2),
      };

      const pattern = action.action_type === "permanent"
        ? { ...basePattern, origin: action.origin }
        : action.action_type === "imposed"
        ? { ...basePattern, imposed_load_category: action.imposed_load_category }
        : action.action_type === "snow"
        ? { ...basePattern, snow_pattern: action.snow_pattern }
        : { ...basePattern, wind_pattern: action.wind_pattern };

      return {
        id: action.id,
        pattern,
        ...(action.action_type !== "permanent"
          ? {
              combination_factors: {
                psi0: toNumber(action.psi0),
                psi1: toNumber(action.psi1),
                psi2: toNumber(action.psi2),
              },
            }
          : {}),
      };
    }),
  };
}

function normalizeCombinedResult(body) {
  if (!body?.uls_combinations || !body?.sls_combinations) {
    return body;
  }

  const allCases = [...body.uls_combinations, ...body.sls_combinations];
  const governingCase = allCases.reduce((currentMax, currentCase) => {
    const currentUtilization = Math.max(...currentCase.checks.map((check) => check.utilization));
    const maxUtilization = Math.max(...currentMax.checks.map((check) => check.utilization));
    return currentUtilization > maxUtilization ? currentCase : currentMax;
  });

  const allWarnings = allCases.flatMap((caseItem) => caseItem.warnings ?? []);
  const deduplicatedWarnings = Array.from(
    new Map(allWarnings.map((warning) => [warning.code, warning])).values(),
  );

  return {
    summary: {
      passed: body.summary.passed,
      governing_check: governingCase.summary.governing_check,
    },
    inputs: body.inputs,
    results: governingCase.results,
    checks: governingCase.checks,
    warnings: deduplicatedWarnings,
    combined: body,
  };
}

function getCombinedCases(result) {
  if (!result?.combined) {
    return [];
  }

  const titleByType = {
    uls_fundamental: "ULS fundamental",
    sls_characteristic: "SLS characteristic",
    sls_frequent: "SLS frequent",
    sls_quasi_permanent: "SLS quasi-permanent",
  };

  return [...result.combined.uls_combinations, ...result.combined.sls_combinations].map((caseItem) => {
    const leading = caseItem.combination.leading_action_id ?? "base";
    return {
      id: `${caseItem.combination.combination_type}-${leading}`,
      label: `${titleByType[caseItem.combination.combination_type] ?? caseItem.combination.combination_type}${caseItem.combination.leading_action_id ? ` · ${caseItem.combination.leading_action_id}` : ""}`,
      caseItem,
    };
  });
}

function buildCombinationPreview(actions) {
  const ULS_PERMANENT_GAMMA = 1.35;
  const ULS_VARIABLE_GAMMA = 1.50;
  const permanent = actions.filter((action) => action.action_type === "permanent");
  const variable = actions.filter((action) => action.action_type !== "permanent");

  if (actions.length === 0) {
    return [];
  }

  const permanentExpression = permanent.map((action) => action.id.toUpperCase()).join(" + ");
  const permanentTotal = permanent.reduce((sum, action) => sum + toNumber(action.value_kN_per_m2), 0);
  const basePrefix = permanentExpression ? `${permanentExpression}` : "0";

  if (variable.length === 0) {
    return [
      {
        id: "uls-only",
        title: "ULS fundamental",
        expression: permanent.map((action) => `1.35·${action.id.toUpperCase()}`).join(" + ") || "0",
        total: permanentTotal * ULS_PERMANENT_GAMMA,
      },
    ];
  }

  const combinations = [];

  variable.forEach((leading) => {
    const leadingId = leading.id.toUpperCase();
    const others = variable.filter((action) => action.id !== leading.id);
    const accompanyingUls = others
      .map((action) => `ψ0·${action.id.toUpperCase()}`)
      .join(" + ");
    const accompanyingFrequent = others
      .map((action) => `ψ2·${action.id.toUpperCase()}`)
      .join(" + ");

    combinations.push({
      id: `uls-${leading.id}`,
      title: `ULS fundamental · ${leadingId} principal`,
      expression: [
        permanent.map((action) => `1.35·${action.id.toUpperCase()}`).join(" + "),
        `1.50·${leadingId}`,
        others.map((action) => `1.50·ψ0·${action.id.toUpperCase()}`).join(" + "),
      ].filter(Boolean).join(" + "),
      total:
        permanentTotal * ULS_PERMANENT_GAMMA
        + toNumber(leading.value_kN_per_m2) * ULS_VARIABLE_GAMMA
        + others.reduce(
          (sum, action) => sum + toNumber(action.value_kN_per_m2) * toNumber(action.psi0) * ULS_VARIABLE_GAMMA,
          0,
        ),
    });

    combinations.push({
      id: `sls-char-${leading.id}`,
      title: `SLS characteristic · ${leadingId} principal`,
      expression: [basePrefix, leadingId, accompanyingUls].filter(Boolean).join(" + "),
      total:
        permanentTotal
        + toNumber(leading.value_kN_per_m2)
        + others.reduce((sum, action) => sum + toNumber(action.value_kN_per_m2) * toNumber(action.psi0), 0),
    });

    combinations.push({
      id: `sls-freq-${leading.id}`,
      title: `SLS frequent · ${leadingId} principal`,
      expression: [basePrefix, `ψ1·${leadingId}`, accompanyingFrequent].filter(Boolean).join(" + "),
      total:
        permanentTotal
        + toNumber(leading.value_kN_per_m2) * toNumber(leading.psi1)
        + others.reduce((sum, action) => sum + toNumber(action.value_kN_per_m2) * toNumber(action.psi2), 0),
    });
  });

  combinations.push({
    id: "sls-qp",
    title: "SLS quasi-permanent",
    expression: [
      basePrefix,
      variable.map((action) => `ψ2·${action.id.toUpperCase()}`).join(" + "),
    ].filter(Boolean).join(" + "),
    total:
      permanentTotal
      + variable.reduce((sum, action) => sum + toNumber(action.value_kN_per_m2) * toNumber(action.psi2), 0),
  });

  return combinations;
}

function parseNumberFields(section) {
  return Object.fromEntries(
    Object.entries(section).map(([key, value]) => [key, key === "grade" || key === "design_standard" ? value : Number(value)]),
  );
}

function App() {
  const [activeTab, setActiveTab] = useState("geometry");
  const [form, setForm] = useState(initialForm);
  const [projectActions, setProjectActions] = useState(initialProjectActions);
  const [selectedActionId, setSelectedActionId] = useState(initialProjectActions[0]?.id ?? null);
  const [result, setResult] = useState(null);
  const [selectedCombinationId, setSelectedCombinationId] = useState("");
  const [errors, setErrors] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestError, setRequestError] = useState("");

  useEffect(() => {
    const summarizedLoads = summarizeActionsToLegacyLoads(projectActions);
    setForm((current) => ({
      ...current,
      loads: {
        dead_load_kN_per_m2: String(summarizedLoads.dead_load_kN_per_m2),
        imposed_load_kN_per_m2: String(summarizedLoads.imposed_load_kN_per_m2),
        additional_dead_load_kN_per_m2: String(summarizedLoads.additional_dead_load_kN_per_m2),
      },
    }));
  }, [projectActions]);

  function handleSupportChange(id, field, value) {
    let nextValue = value;
    if (field === "position_m") {
      const span = Number(form.geometry.span_m);
      const numericValue = Number(value);
      if (!Number.isNaN(numericValue) && !Number.isNaN(span)) {
        nextValue = String(Math.max(0, Math.min(numericValue, span)));
      }
    }

    setForm((current) => ({
      ...current,
      supports: current.supports.map((support) =>
        support.id === id ? { ...support, [field]: nextValue } : support,
      ),
    }));
  }

  function addSupport() {
    setForm((current) => {
      const nextId = current.supports.length > 0 ? Math.max(...current.supports.map((support) => support.id)) + 1 : 1;
      return {
        ...current,
        supports: [
          ...current.supports,
          { id: nextId, support_type: "roller", position_m: current.geometry.span_m || "0.00" },
        ],
      };
    });
  }

  function removeSupport(id) {
    setForm((current) => ({
      ...current,
      supports: current.supports.filter((support) => support.id !== id),
    }));
  }

  function handleChange(section, field, value) {
    if (!section) {
      setForm((current) => ({ ...current, [field]: value }));
      return;
    }

    if (section === "timber" && field === "grade") {
      setForm((current) => ({
        ...current,
        timber: {
          ...current.timber,
          ...timberFormValuesFromGrade(value),
        },
      }));
      return;
    }

    setForm((current) => ({
      ...current,
      [section]: {
        ...current[section],
        [field]: value,
      },
    }));
  }

  function addProjectAction(actionType) {
    setProjectActions((current) => {
      const nextAction = createProjectAction(actionType, current.length + 1);
      setSelectedActionId(nextAction.id);
      return [...current, nextAction];
    });
  }

  function removeProjectAction(id) {
    setProjectActions((current) => {
      const filtered = current.filter((action) => action.id !== id);
      if (selectedActionId === id) {
        setSelectedActionId(filtered[0]?.id ?? null);
      }
      return filtered;
    });
  }

  function updateProjectAction(id, field, value) {
    setProjectActions((current) =>
      current.map((action) => (action.id === id ? { ...action, [field]: value } : action)),
    );
  }

  const selectedAction = projectActions.find((action) => action.id === selectedActionId) ?? projectActions[0] ?? null;
  const selectedTimberClass = TIMBER_CLASS_DATA[form.timber.grade] ?? TIMBER_CLASS_DATA.C24;
  const combinationPreview = buildCombinationPreview(projectActions);
  const showSplitPreview = activeTab === "geometry" || activeTab === "section";
  const combinedCases = getCombinedCases(result);
  const selectedCombinedCase =
    combinedCases.find((item) => item.id === selectedCombinationId)?.caseItem
    ?? combinedCases[0]?.caseItem
    ?? null;
  const displayedResults = selectedCombinedCase?.results ?? result?.results ?? null;
  const displayedChecks = selectedCombinedCase?.checks ?? result?.checks ?? [];
  const displayedDeflectionCapacity = displayedChecks
    .filter((check) => check.check.startsWith("deflection"))
    .reduce(
      (currentMin, check) => (currentMin == null ? check.capacity : Math.min(currentMin, check.capacity)),
      null,
    ) ?? displayedResults?.allowable_deflection_mm;
  const displayedWarnings = selectedCombinedCase?.warnings ?? result?.warnings ?? [];
  const displayedGoverningCheck = selectedCombinedCase?.summary.governing_check ?? result?.summary.governing_check ?? "Sin cÃ¡lculo";

  useEffect(() => {
    if (combinedCases.length > 0) {
      setSelectedCombinationId(combinedCases[0].id);
    } else {
      setSelectedCombinationId("");
    }
  }, [result]);

  function validate() {
    const nextErrors = [];
    const numericGroups = [
      ["geometry", ["span_m", "spacing_m", "width_mm", "depth_mm"]],
      ["timber", ["modulus_of_elasticity_mpa", "allowable_bending_stress_mpa", "allowable_shear_stress_mpa"]],
      ["loads", ["dead_load_kN_per_m2", "imposed_load_kN_per_m2", "additional_dead_load_kN_per_m2"]],
      ["criteria", ["max_deflection_ratio", "active_deflection_ratio", "instantaneous_deflection_ratio", "final_deflection_ratio"]],
    ];

    numericGroups.forEach(([section, fields]) => {
      fields.forEach((field) => {
        const value = Number(form[section][field]);
        if (Number.isNaN(value)) {
          nextErrors.push(`El campo ${field} debe ser numérico.`);
        }
      });
    });

    if (!form.timber.grade.trim()) {
      nextErrors.push("La clase de madera es obligatoria.");
    }

    const span = Number(form.geometry.span_m);
    if (!Number.isNaN(span)) {
      form.supports.forEach((support, index) => {
        const position = Number(support.position_m);
        if (Number.isNaN(position)) {
          nextErrors.push(`La posición del apoyo ${index + 1} debe ser numérica.`);
          return;
        }
        if (position < 0 || position > span) {
          nextErrors.push(`La posición del apoyo ${index + 1} debe estar entre 0 y la luz de la viga.`);
        }
      });
    }

    if (form.supports.length < 2) {
      nextErrors.push("Debes definir al menos dos apoyos para una viga estable.");
    }

    return nextErrors;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const nextErrors = validate();
    setErrors(nextErrors);
    setRequestError("");

    if (nextErrors.length > 0) {
      return;
    }

    const payload = {
      project_name: form.project_name,
      geometry: parseNumberFields(form.geometry),
      timber: {
        ...parseNumberFields(form.timber),
        grade: form.timber.grade,
      },
      supports: form.supports.map((support) => ({
        support_type: support.support_type,
        position_m: Number(support.position_m),
      })),
      criteria: {
        ...parseNumberFields(form.criteria),
        design_standard: form.criteria.design_standard,
      },
      action_catalog: buildActionCatalogPayload(projectActions),
    };

    setIsSubmitting(true);

    try {
      const response = await fetch(apiUrl("/calculate/floor-joist/combinations"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const body = await readJsonFromResponse(response);
      if (!response.ok) {
        throw new Error(formatHttpErrorDetail(response.status, body));
      }
      if (body == null) {
        throw new Error("La API devolvió una respuesta vacía.");
      }
      setResult(normalizeCombinedResult(body));
    } catch (error) {
      setRequestError(apiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  const governingCheck = activeTab === "results" ? displayedGoverningCheck : result?.summary.governing_check ?? "Sin cálculo";

  return (
    <div className="page-shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">KLS Timber Studio</p>
          <h1>Calculadora de forjado de madera</h1>
          <p className="hero-text">
            Introduce geometría, material y cargas. La interfaz envía los datos al backend y presenta
            resultados trazables de flexión, cortante y flecha.
          </p>
        </div>
        <div className="hero-card">
          <span className="hero-card-label">Comprobación gobernante</span>
          <strong>{governingCheck}</strong>
          <span className={`status-pill ${result?.summary.passed ? "pass" : "idle"}`}>
            {result ? (result.summary.passed ? "Cumple" : "Revisar") : "Pendiente"}
          </span>
        </div>
      </header>

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === "geometry" ? "active" : ""}`}
          onClick={() => setActiveTab("geometry")}
        >
          <span className="tab-icon">📐</span>
          Geometría
        </button>
        <button
          className={`tab-button ${activeTab === "section" ? "active" : ""}`}
          onClick={() => setActiveTab("section")}
        >
          <span className="tab-icon">▣</span>
          Sección
        </button>
        <button
          className={`tab-button ${activeTab === "material" ? "active" : ""}`}
          onClick={() => setActiveTab("material")}
        >
          <span className="tab-icon">🔧</span>
          Material
        </button>
        <button
          className={`tab-button ${activeTab === "loads" ? "active" : ""}`}
          onClick={() => setActiveTab("loads")}
        >
          <span className="tab-icon">⚖️</span>
          Cargas
        </button>
        <button
          className={`tab-button ${activeTab === "designBasis" ? "active" : ""}`}
          onClick={() => setActiveTab("designBasis")}
        >
          <span className="tab-icon">≡</span>
          Bases de cálculo
        </button>
        <button
          className={`tab-button ${activeTab === "results" ? "active" : ""}`}
          onClick={() => setActiveTab("results")}
        >
          <span className="tab-icon">📊</span>
          Resultados
        </button>
      </div>

      <main className={`layout ${showSplitPreview ? "layout-split-preview" : ""}`}>
        <section className={`panel panel-form ${showSplitPreview ? "panel-form-split" : "panel-full-width"}`}>
          <div className="panel-heading">
            <p>Los valores se envían en el formato que espera la API actual.</p>
          </div>

          <form onSubmit={handleSubmit} className="calc-form">
            {activeTab === "geometry" && (
              <>
                <FormGroup title="Geometría longitudinal" className="form-group-compact-top">
                  <Field label="Luz (m)" value={form.geometry.span_m} onChange={(value) => handleChange("geometry", "span_m", value)} />
                  <Field label="Separación (m)" value={form.geometry.spacing_m} onChange={(value) => handleChange("geometry", "spacing_m", value)} />
                </FormGroup>

                <section className="form-group">
                  <div className="group-title support-group-title">
                    <div>
                      <h3>Apoyos</h3>
                      <p>La coordenada se mide de izquierda a derecha y no puede superar la luz.</p>
                    </div>
                    <button type="button" className="secondary-button" onClick={addSupport}>
                      Añadir apoyo
                    </button>
                  </div>
                  <div className="supports-list">
                    {form.supports.map((support, index) => (
                      <article className="support-row" key={support.id}>
                        <SelectField
                          label={`Tipo de apoyo ${index + 1}`}
                          value={support.support_type}
                          onChange={(value) => handleSupportChange(support.id, "support_type", value)}
                          options={supportTypeOptions}
                        />
                        <Field
                          label="Ubicación (m)"
                          value={support.position_m}
                          onChange={(value) => handleSupportChange(support.id, "position_m", value)}
                        />
                        <button
                          type="button"
                          className="icon-button"
                          onClick={() => removeSupport(support.id)}
                          disabled={form.supports.length <= 2}
                        >
                          Quitar
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
              </>
            )}

            {activeTab === "material" && (
              <>
                <FormGroup title="Madera">
                  <SelectField
                    label="Clase resistente"
                    value={form.timber.grade}
                    onChange={(value) => handleChange("timber", "grade", value)}
                    options={timberClassOptions}
                  />
                </FormGroup>
                <section className="form-group">
                  <div className="group-title">
                    <h3>Propiedades de la clase {form.timber.grade}</h3>
                    <p>Valores asociados directamente a la clase resistente seleccionada.</p>
                  </div>
                  <div className="metrics-grid material-properties-grid">
                    <ResultCard label="Flexión fm,k" value={selectedTimberClass.bending_strength_mpa} unit="MPa" />
                    <ResultCard label="Tracción paralela ft,0,k" value={selectedTimberClass.tensile_strength_parallel_mpa} unit="MPa" />
                    <ResultCard label="Tracción perpendicular ft,90,k" value={selectedTimberClass.tensile_strength_perpendicular_mpa} unit="MPa" />
                    <ResultCard label="Compresión paralela fc,0,k" value={selectedTimberClass.compressive_strength_parallel_mpa} unit="MPa" />
                    <ResultCard label="Compresión perpendicular fc,90,k" value={selectedTimberClass.compressive_strength_perpendicular_mpa} unit="MPa" />
                    <ResultCard label="Cortante fv,k" value={selectedTimberClass.shear_strength_mpa} unit="MPa" />
                    <ResultCard label="Módulo paralelo medio E0,medio" value={selectedTimberClass.modulus_mean_gpa} unit="GPa" />
                    <ResultCard label="Módulo paralelo 5 percentil E0,k" value={selectedTimberClass.modulus_5_percentile_gpa} unit="GPa" />
                    <ResultCard label="Módulo perpendicular medio E90,medio" value={selectedTimberClass.modulus_perpendicular_mean_gpa} unit="GPa" />
                    <ResultCard label="Módulo transversal medio Gmedio" value={selectedTimberClass.shear_modulus_mean_gpa} unit="GPa" />
                    <ResultCard label="Densidad característica ρk" value={selectedTimberClass.density_characteristic_kg_per_m3} unit="kg/m3" />
                    <ResultCard label="Densidad media ρmedio" value={selectedTimberClass.density_mean_kg_per_m3} unit="kg/m3" />
                  </div>
                </section>
              </>
            )}

            {activeTab === "loads" && (
              <>
                <section className="form-group">
                  <div className="group-title loads-group-title">
                    <div>
                      <h3>Acciones del proyecto</h3>
                      <p>Define el catálogo de cargas y revisa cómo se formarían las combinaciones.</p>
                    </div>
                    <div className="action-toolbar">
                      <button type="button" className="secondary-button" onClick={() => addProjectAction("permanent")}>+ Permanente</button>
                      <button type="button" className="secondary-button" onClick={() => addProjectAction("imposed")}>+ Uso</button>
                      <button type="button" className="secondary-button" onClick={() => addProjectAction("snow")}>+ Nieve</button>
                      <button type="button" className="secondary-button" onClick={() => addProjectAction("wind")}>+ Viento</button>
                    </div>
                  </div>

                  <div className="loads-workspace">
                    <div className="actions-list">
                      {projectActions.map((action) => (
                        <article key={action.id} className={`action-card ${selectedAction?.id === action.id ? "active" : ""}`}>
                          <button type="button" className="action-card-main" onClick={() => setSelectedActionId(action.id)}>
                            <div className="action-card-top">
                              <span className={`action-badge type-${action.action_type}`}>{action.id.toUpperCase()}</span>
                              <span className="action-type-label">{actionTypeOptions.find((option) => option.value === action.action_type)?.label}</span>
                            </div>
                            <strong>{action.name}</strong>
                            <p>{formatNumber(toNumber(action.value_kN_per_m2))} kN/m2</p>
                            <span className="action-meta">
                              {action.action_type === "permanent"
                                ? permanentOriginOptions.find((option) => option.value === action.origin)?.label
                                : action.action_type === "imposed"
                                ? `Categoría ${action.imposed_load_category}`
                                : action.action_type === "snow"
                                ? `Patrón ${action.snow_pattern}`
                                : `Patrón ${action.wind_pattern}`}
                            </span>
                          </button>
                          <button type="button" className="icon-button action-remove" onClick={() => removeProjectAction(action.id)} disabled={projectActions.length <= 1}>
                            Quitar
                          </button>
                        </article>
                      ))}
                    </div>

                    <div className="action-editor">
                      {selectedAction ? (
                        <>
                          <div className="action-editor-head">
                            <h4>Editor de acción</h4>
                            <span>{selectedAction.id.toUpperCase()}</span>
                          </div>
                          <div className="field-grid">
                            <SelectField label="Tipo" value={selectedAction.action_type} onChange={(value) => updateProjectAction(selectedAction.id, "action_type", value)} options={actionTypeOptions} />
                            <SelectField label="Distribución" value={selectedAction.distribution} onChange={(value) => updateProjectAction(selectedAction.id, "distribution", value)} options={loadDistributionOptions} />
                            <Field label="Nombre" value={selectedAction.name} onChange={(value) => updateProjectAction(selectedAction.id, "name", value)} />
                            <Field label="Valor (kN/m2)" value={selectedAction.value_kN_per_m2} onChange={(value) => updateProjectAction(selectedAction.id, "value_kN_per_m2", value)} />
                            {selectedAction.action_type === "permanent" && (
                              <SelectField label="Origen" value={selectedAction.origin} onChange={(value) => updateProjectAction(selectedAction.id, "origin", value)} options={permanentOriginOptions} />
                            )}
                            {selectedAction.action_type === "imposed" && (
                              <SelectField label="Categoría de uso" value={selectedAction.imposed_load_category} onChange={(value) => updateProjectAction(selectedAction.id, "imposed_load_category", value)} options={imposedCategoryOptionsDisplay} />
                            )}
                            {selectedAction.action_type === "snow" && (
                              <SelectField label="Patrón de nieve" value={selectedAction.snow_pattern} onChange={(value) => updateProjectAction(selectedAction.id, "snow_pattern", value)} options={snowPatternOptions} />
                            )}
                            {selectedAction.action_type === "wind" && (
                              <SelectField label="Patrón de viento" value={selectedAction.wind_pattern} onChange={(value) => updateProjectAction(selectedAction.id, "wind_pattern", value)} options={windPatternOptionsDisplay} />
                            )}
                          </div>

                          {selectedAction.action_type !== "permanent" && (
                            <div className="field-grid combination-factors">
                              <Field label="ψ0" value={selectedAction.psi0} onChange={(value) => updateProjectAction(selectedAction.id, "psi0", value)} />
                              <Field label="ψ1" value={selectedAction.psi1} onChange={(value) => updateProjectAction(selectedAction.id, "psi1", value)} />
                              <Field label="ψ2" value={selectedAction.psi2} onChange={(value) => updateProjectAction(selectedAction.id, "psi2", value)} />
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="empty-state compact">
                          <h3>Sin acciones</h3>
                          <p>Añade una acción para empezar a construir el catálogo de cargas.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </section>

                
                <section className="form-group">
                  <div className="group-title">
                    <h3>Vista previa de combinaciones</h3>
                  </div>
                  <div className="combination-preview-list">
                    {combinationPreview.map((combination) => (
                      <article key={combination.id} className="combination-card">
                        <div className="combination-card-head">
                          <h4>{combination.title}</h4>
                          <strong>{formatNumber(combination.total)} kN/m2</strong>
                        </div>
                        <p>{combination.expression}</p>
                      </article>
                    ))}
                  </div>
                </section>

                {errors.length > 0 ? (
                  <div className="message error">
                    {errors.map((error) => (
                      <p key={error}>{error}</p>
                    ))}
                  </div>
                ) : null}

                {requestError ? <div className="message error"><p>{requestError}</p></div> : null}

                <button type="submit" className="submit-button" disabled={isSubmitting}>
                  {isSubmitting ? "Calculando..." : "Calcular forjado"}
                </button>
              </>
            )}

            {activeTab === "designBasis" && (
              <>
                <FormGroup title="Bases generales">
                  <Field
                    label="Base de cálculo"
                    value={form.criteria.design_standard}
                    onChange={(value) => handleChange("criteria", "design_standard", value)}
                  />
                  <Field
                    label="Cálculo simple L/x"
                    value={form.criteria.max_deflection_ratio}
                    onChange={(value) => handleChange("criteria", "max_deflection_ratio", value)}
                  />
                </FormGroup>

                <FormGroup title="Flecha SLS characteristic">
                  <Field
                    label="Activa L/x"
                    value={form.criteria.active_deflection_ratio}
                    onChange={(value) => handleChange("criteria", "active_deflection_ratio", value)}
                  />
                  <Field
                    label="Instantánea L/x"
                    value={form.criteria.instantaneous_deflection_ratio}
                    onChange={(value) => handleChange("criteria", "instantaneous_deflection_ratio", value)}
                  />
                </FormGroup>

                <FormGroup title="Flecha SLS quasi-permanent">
                  <Field
                    label="Final L/x"
                    value={form.criteria.final_deflection_ratio}
                    onChange={(value) => handleChange("criteria", "final_deflection_ratio", value)}
                  />
                </FormGroup>

                {errors.length > 0 ? (
                  <div className="message error">
                    {errors.map((error) => (
                      <p key={error}>{error}</p>
                    ))}
                  </div>
                ) : null}

                {requestError ? <div className="message error"><p>{requestError}</p></div> : null}

                <button type="submit" className="submit-button" disabled={isSubmitting}>
                  {isSubmitting ? "Calculando..." : "Calcular forjado"}
                </button>
              </>
            )}

            {activeTab === "results" && (
              <div className="results-preview">
                {result ? (
                  <>
                    {combinedCases.length > 0 && (
                      <section className="form-group form-group-compact-top">
                        <div className="field-grid single">
                          <SelectField
                            label="Caso de carga"
                            value={selectedCombinationId}
                            onChange={setSelectedCombinationId}
                            options={combinedCases.map((item) => ({ value: item.id, label: item.label }))}
                          />
                        </div>
                      </section>
                    )}

                    <div className="summary-band">
                      <div>
                        <span className="metric-label">Estado</span>
                        <strong>{selectedCombinedCase ? (selectedCombinedCase.summary.passed ? "Cumple" : "No cumple") : (result.summary.passed ? "Cumple" : "No cumple")}</strong>
                      </div>
                      <div>
                        <span className="metric-label">Controla</span>
                        <strong>{displayedGoverningCheck}</strong>
                      </div>
                      <div>
                        <span className="metric-label">Norma</span>
                        <strong>{result.inputs.criteria.design_standard}</strong>
                      </div>
                    </div>

                    <div className="metrics-grid">
                      <ResultCard label="Carga lineal" value={displayedResults.line_load_kN_per_m} unit="kN/m" />
                      <ResultCard label="Momento máximo" value={displayedResults.max_moment_kNm} unit="kNm" />
                      <ResultCard label="Cortante máximo" value={displayedResults.max_shear_kN} unit="kN" />
                      <ResultCard label="Flecha" value={displayedResults.deflection_mm} unit="mm" />
                      <ResultCard label="Momento de inercia" value={displayedResults.section_inertia_mm4} unit="mm⁴" />
                      <ResultCard label="Módulo de sección" value={displayedResults.section_modulus_mm3} unit="mm³" />
                      <ResultCard label="Tensión de flexión" value={displayedResults.bending_stress_mpa} unit="MPa" />
                      <ResultCard label="Tensión de cortante" value={displayedResults.shear_stress_mpa} unit="MPa" />
                      <ResultCard label="Flecha admisible" value={displayedDeflectionCapacity} unit="mm" />
                    </div>

                    <div className="checks-list">
                      {displayedChecks.map((check) => (
                        <article className="check-card" key={check.check}>
                          <div className="check-card-header">
                            <h3>{check.check}</h3>
                            <span className={`status-pill ${check.passed ? "pass" : "fail"}`}>
                              {check.passed ? "OK" : "No OK"}
                            </span>
                          </div>
                          <p>Demanda: {formatNumber(check.demand)} {check.unit}</p>
                          <p>Capacidad: {formatNumber(check.capacity)} {check.unit}</p>
                          <p>Utilización: {formatNumber(check.utilization)}</p>
                        </article>
                      ))}
                    </div>

                    <div className="warnings-box">
                      <h3>Advertencias</h3>
                      {displayedWarnings.length > 0 ? (
                        displayedWarnings.map((warning) => (
                          <p key={warning.code}>
                            <strong>{warning.code}</strong>: {warning.message}
                          </p>
                        ))
                      ) : (
                        <p>Sin advertencias en este caso.</p>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <h3>Esperando un cálculo</h3>
                    <p>
                      Cuando envíes el formulario, aquí aparecerán los valores principales y las comprobaciones
                      del backend.
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "section" && (
              <>
                <FormGroup title="Sección transversal" className="form-group-compact-top">
                  <Field label="Ancho (mm)" value={form.geometry.width_mm} onChange={(value) => handleChange("geometry", "width_mm", value)} />
                  <Field label="Canto (mm)" value={form.geometry.depth_mm} onChange={(value) => handleChange("geometry", "depth_mm", value)} />
                </FormGroup>

                <div className="results-preview">
                  <div className="section-summary">
                    <p>Esta pestaña muestra la pieza en sección transversal con las dimensiones activas.</p>
                    <p>Si ya hay cálculo, la vista toma la geometría enviada al backend; si no, usa el formulario actual.</p>
                  </div>
                </div>
              </>
            )}
          </form>
        </section>

        {(activeTab === "geometry" || activeTab === "section" || (activeTab === "results" && result)) && (
          <section className={`panel panel-diagrams ${showSplitPreview ? "panel-diagrams-split" : "panel-full-width"}`}>
            <div className="panel-heading">
              <h2>{activeTab === "geometry" ? "Viga y apoyos" : activeTab === "section" ? "Sección transversal" : "Diagramas"}</h2>
              <p>
                {activeTab === "geometry"
                  ? "Vista previa de la viga con la configuración de apoyos"
                  : activeTab === "section"
                  ? "Vista geométrica de la pieza activa"
                  : "Análisis estructural automático con elementos finitos"}
              </p>
            </div>
            <DiagramsSection result={result} selectedCase={selectedCombinedCase} view={activeTab} form={form} />
          </section>
        )}
      </main>
    </div>
  );
}

function FormGroup({ title, children, className = "" }) {
  return (
    <section className={`form-group ${className}`.trim()}>
      <div className="group-title">
        <h3>{title}</h3>
      </div>
      <div className="field-grid">{children}</div>
    </section>
  );
}

function Field({ label, value, onChange }) {
  return (
    <label>
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label>
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ResultCard({ label, value, unit }) {
  return (
    <article className="result-card">
      <span className="metric-label">{label}</span>
      <strong>{formatNumber(value)} {unit}</strong>
    </article>
  );
}

function DiagramSummaryCard({ label, value, unit, positionM }) {
  return (
    <article className="result-card">
      <span className="metric-label">{label}</span>
      <div className="result-inline-value">
        <strong>{formatNumber(value)}</strong>
        <strong>{unit}</strong>
      </div>
      <span className="result-subtext">x = {formatNumber(positionM)} m</span>
    </article>
  );
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-ES", {
    maximumFractionDigits: 3,
  }).format(value);
}

function DiagramsSection({ result, selectedCase = null, view = "results", form }) {
  // Usar parámetros del cálculo si existe, sino valores por defecto
  const activeResults = selectedCase?.results ?? result?.results ?? null;
  const calculatedParams = result && activeResults ? {
    length: result.inputs.geometry.span_m,
    elements: 100, // mantener fijo internamente
    load: -activeResults.line_load_kN_per_m, // negativo para downward
    modulus: result.inputs.timber.modulus_of_elasticity_mpa,
  } : null;
  const sectionDimensions = result
    ? {
        widthMm: result.inputs.geometry.width_mm,
        depthMm: result.inputs.geometry.depth_mm,
      }
    : {
        widthMm: Number(form?.geometry.width_mm ?? 63),
        depthMm: Number(form?.geometry.depth_mm ?? 200),
      };
  const supports = view === "results" && result
    ? result.inputs.supports
    : (form?.supports ?? []).map((support) => ({
        support_type: support.support_type,
        position_m: Number(support.position_m),
      }));

  const [diagramData, setDiagramData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDiagrams = async (params) => {
    setLoading(true);
    setError(null);

    const payload = {
      project_name: result?.inputs.project_name ?? form?.project_name ?? null,
      span: {
        length_m: params.length,
        element_count: params.elements,
      },
      material: {
        modulus_of_elasticity_mpa: params.modulus,
      },
      section: {
        width_mm: result ? result.inputs.geometry.width_mm : 63.0,
        depth_mm: result ? result.inputs.geometry.depth_mm : 200.0,
      },
      supports: supports.length > 0
        ? supports
        : [
            { position_m: 0.0, support_type: "pinned" },
            { position_m: params.length, support_type: "roller" },
          ],
      loads: [
        {
          load_type: "distributed",
          start_m: 0.0,
          end_m: params.length,
          value_kN_per_m: params.load,
        },
      ],
    };

    try {
      const response = await fetch(apiUrl("/analyze/beam"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await readJsonFromResponse(response);
      if (!response.ok) {
        throw new Error(formatHttpErrorDetail(response.status, data));
      }
      if (data == null) {
        throw new Error("La API de análisis devolvió una respuesta vacía.");
      }
      setDiagramData(data);
    } catch (err) {
      setError(err.message);
      setDiagramData(null);
    } finally {
      setLoading(false);
    }
  };

  // Cargar diagramas cuando cambia el result
  useEffect(() => {
    if (view === "results" && result && calculatedParams) {
      loadDiagrams(calculatedParams);
    }
  }, [view, result, selectedCase]);

  return (
    <section className="panel panel-diagrams">
      <div className="panel-heading">
        <h2>Diagramas estructurales</h2>
        <p>
          {view === "geometry"
            ? "Vista previa inmediata basada en la geometría y los apoyos definidos"
            : view === "section"
            ? "Vista geométrica de la sección activa"
            : "Diagramas sincronizados con la combinación seleccionada"
          }
          {loading && " - Actualizando..."}
        </p>
      </div>

      {error && view === "results" && (
        <div className="message error">
          <p>{error}</p>
        </div>
      )}

      {view === "geometry" && (
            <article className="diagram-card beam-view-card">
              <div className="diagram-card-header">
                <h3>Viga y apoyos</h3>
                <span>Configuración actual</span>
              </div>
              <BeamSupportPreview
                spanM={Number(form?.geometry.span_m ?? 4)}
                supports={supports}
              />
              <div className="diagram-card-footer">
                <span>Luz: {formatNumber(Number(form?.geometry.span_m ?? 4))} m</span>
                <span>{supports.length} apoyos definidos</span>
              </div>
            </article>
      )}

      {view === "section" && (
        <SectionCard widthMm={sectionDimensions.widthMm} depthMm={sectionDimensions.depthMm} />
      )}

      {diagramData && (
        <>

          {view === "results" && (
            <div className="metrics-grid metrics-grid-compact">
              <DiagramSummaryCard
                label="Flecha máxima"
                value={diagramData.summary.max_deflection_mm}
                unit="mm"
                positionM={diagramData.summary.max_deflection_position_m}
              />
              <DiagramSummaryCard
                label="Momento máximo"
                value={diagramData.summary.max_moment_kNm}
                unit="kNm"
                positionM={diagramData.summary.max_moment_position_m}
              />
              <DiagramSummaryCard
                label="Cortante máximo"
                value={diagramData.summary.max_shear_kN}
                unit="kN"
                positionM={diagramData.summary.max_shear_position_m}
              />
            </div>
          )}

          {view === "results" && (
            <article className="diagram-card beam-view-card">
              <div className="diagram-card-header">
                <h3>Viga y deformada</h3>
                <span>Vista general</span>
              </div>
              <BeamView nodes={diagramData.nodes} supports={supports} />
              <div className="diagram-card-footer">
                La línea clara representa el eje no deformado y la línea azul la deformada amplificada.
              </div>
            </article>
          )}

          {view === "results" && (
            <div id="diagram-grid" className="diagram-grid">
              {diagramData.diagrams
                .filter((diagram) => diagram.diagram_type !== "rotation")
                .map((diagram) => (
                <DiagramCard key={diagram.diagram_type} diagram={diagram} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function SectionCard({ widthMm, depthMm }) {
  return (
    <article className="diagram-card section-view-card">
      <div className="diagram-card-header">
        <h3>Sección transversal</h3>
        <span>Geometría activa</span>
      </div>
      <CrossSectionView
        widthMm={widthMm}
        depthMm={depthMm}
      />
      <div className="diagram-card-footer">
        <span>Ancho: {formatNumber(widthMm)} mm</span>
        <span>Canto: {formatNumber(depthMm)} mm</span>
      </div>
    </article>
  );
}

function BeamSupportPreview({ spanM, supports }) {
  const width = 900;
  const height = 260;
  const padding = 48;
  const baseY = height / 2;
  const normalizedSpan = spanM > 0 ? spanM : 1;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="beam-svg" aria-label="Vista de viga con apoyos">
      <line x1={padding} y1={baseY} x2={width - padding} y2={baseY} className="beam-baseline" />
      {supports.map((support, index) => {
        const rawPosition = Number.isFinite(support.position_m) ? support.position_m : 0;
        const clampedPosition = Math.max(0, Math.min(rawPosition, normalizedSpan));
        const x = padding + (clampedPosition / normalizedSpan) * (width - padding * 2);
        return (
          <g key={`${support.support_type}-${index}`}>
            {renderSupportShape(support.support_type, x, baseY)}
            <text x={x} y={baseY - 18} textAnchor="middle" className="beam-label">
              {formatNumber(rawPosition)} m
            </text>
          </g>
        );
      })}
      <text x={padding} y={baseY + 58} className="beam-scale-label">0 m</text>
      <text x={width - padding} y={baseY + 58} textAnchor="end" className="beam-scale-label">
        {formatNumber(spanM)} m
      </text>
    </svg>
  );
}

function renderSupportShape(type, x, baseY) {
  if (type === "fixed") {
    return (
      <g>
        <rect x={x - 12} y={baseY - 36} width="16" height="72" className="beam-support fixed" />
        <line x1={x + 4} y1={baseY - 36} x2={x + 4} y2={baseY + 36} className="beam-support-hatch" />
        <line x1={x - 6} y1={baseY - 28} x2={x + 4} y2={baseY - 36} className="beam-support-hatch" />
        <line x1={x - 6} y1={baseY - 14} x2={x + 4} y2={baseY - 22} className="beam-support-hatch" />
        <line x1={x - 6} y1={baseY} x2={x + 4} y2={baseY - 8} className="beam-support-hatch" />
        <line x1={x - 6} y1={baseY + 14} x2={x + 4} y2={baseY + 6} className="beam-support-hatch" />
        <line x1={x - 6} y1={baseY + 28} x2={x + 4} y2={baseY + 20} className="beam-support-hatch" />
      </g>
    );
  }

  return (
    <g>
      <polygon points={`${x - 16},${baseY + 34} ${x + 16},${baseY + 34} ${x},${baseY + 8}`} className="beam-support" />
      {type === "roller" && (
        <>
          <circle cx={x - 8} cy={baseY + 42} r="4" className="beam-support" />
          <circle cx={x + 8} cy={baseY + 42} r="4" className="beam-support" />
        </>
      )}
    </g>
  );
}

function DiagramCard({ diagram }) {
  const translateType = {
    shear: "Diagrama de cortante",
    moment: "Diagrama de momentos",
    deflection: "Deformada",
  };

  const maxAbs = Math.max(...diagram.points.map(p => Math.abs(p.value)));

  return (
    <article className="diagram-card">
      <div className="diagram-card-header">
        <h3>{translateType[diagram.diagram_type] || diagram.diagram_type}</h3>
        <span>{diagram.unit}</span>
      </div>
      <LineChart points={diagram.points} type={diagram.diagram_type} unit={diagram.unit} />
      <div className="diagram-card-footer">
        Valor máximo: {formatNumber(maxAbs)} {diagram.unit}
      </div>
    </article>
  );
}

function LineChart({ points, type, unit }) {
  const width = 520;
  const height = 220;
  const padding = 26;
  const [hoverPoint, setHoverPoint] = useState(null);
  const invertPositiveDirection = type === "moment";
  const normalizedPoints = (() => {
    if (type !== "shear" || points.length < 2) {
      return points;
    }

    const nextPoints = [...points];
    const firstPoint = nextPoints[0];
    const secondPoint = nextPoints[1];
    if (firstPoint.x_m === secondPoint.x_m && Math.abs(firstPoint.value) > 1e-9) {
      nextPoints.unshift({ x_m: firstPoint.x_m, value: 0 });
    }

    const lastPoint = nextPoints[nextPoints.length - 1];
    const previousPoint = nextPoints[nextPoints.length - 2];
    if (lastPoint.x_m === previousPoint.x_m && Math.abs(lastPoint.value) > 1e-9) {
      nextPoints.push({ x_m: lastPoint.x_m, value: 0 });
    }

    return nextPoints;
  })();

  const xValues = normalizedPoints.map(p => p.x_m);
  const yValues = normalizedPoints.map(p => p.value);
  const displayValues = yValues.map((value) => (invertPositiveDirection ? -value : value));
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...displayValues, 0);
  const maxY = Math.max(...displayValues, 0);
  const ySpan = maxY - minY || 1;
  const xSpan = maxX - minX || 1;
  const zeroY = padding + ((maxY - 0) / ySpan) * (height - padding * 2);
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  function getChartY(value) {
    const displayValue = invertPositiveDirection ? -value : value;
    return padding + ((maxY - displayValue) / ySpan) * chartHeight;
  }

  function getChartX(value) {
    return padding + ((value - minX) / xSpan) * chartWidth;
  }

  function buildPathData() {
    if (!normalizedPoints.length) {
      return "";
    }

    return normalizedPoints
      .map((point, index) => {
        const x = getChartX(point.x_m);
        const y = getChartY(point.value);
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  }

  const pathData = buildPathData();
  const axisStartX = normalizedPoints.length ? getChartX(normalizedPoints[0].x_m) : padding;
  const axisEndX = normalizedPoints.length ? getChartX(normalizedPoints[normalizedPoints.length - 1].x_m) : width - padding;

  function interpolatePoint(targetX) {
    if (normalizedPoints.length === 1) {
      return normalizedPoints[0];
    }

    if (targetX <= normalizedPoints[0].x_m) {
      return normalizedPoints[0];
    }

    if (targetX >= normalizedPoints[normalizedPoints.length - 1].x_m) {
      return normalizedPoints[normalizedPoints.length - 1];
    }

    for (let index = 0; index < normalizedPoints.length - 1; index += 1) {
      const left = normalizedPoints[index];
      const right = normalizedPoints[index + 1];
      if (targetX >= left.x_m && targetX <= right.x_m) {
        const segmentSpan = right.x_m - left.x_m || 1;
        const ratio = (targetX - left.x_m) / segmentSpan;
        return {
          x_m: targetX,
          value: left.value + (right.value - left.value) * ratio,
        };
      }
    }

    return normalizedPoints[normalizedPoints.length - 1];
  }

  function getScreenPoint(point) {
    return {
      x: padding + ((point.x_m - minX) / xSpan) * chartWidth,
      y: getChartY(point.value),
    };
  }

  function handlePointerMove(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const relativeX = ((event.clientX - bounds.left) / bounds.width) * width;
    const clampedX = Math.max(padding, Math.min(relativeX, width - padding));
    const targetX = minX + ((clampedX - padding) / chartWidth) * xSpan;
    const interpolated = interpolatePoint(targetX);
    const screenPoint = getScreenPoint(interpolated);
    setHoverPoint({
      ...interpolated,
      ...screenPoint,
    });
  }

  function handlePointerLeave() {
    setHoverPoint(null);
  }

  const tooltipX = hoverPoint ? Math.min(width - 110, Math.max(18, hoverPoint.x + 12)) : 0;
  const tooltipY = hoverPoint ? Math.max(18, hoverPoint.y - 16) : 0;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={`diagram-svg ${type}`}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <line
        x1={axisStartX}
        x2={axisEndX}
        y1={zeroY}
        y2={zeroY}
        className="axis-line"
      />
      <path
        d={pathData}
        className="diagram-line"
      />
      {hoverPoint && (
        <>
          <line
            x1={hoverPoint.x}
            x2={hoverPoint.x}
            y1={zeroY}
            y2={hoverPoint.y}
            className="diagram-hover-line"
          />
          <circle
            cx={hoverPoint.x}
            cy={hoverPoint.y}
            r="5"
            className="diagram-hover-point"
          />
          <g transform={`translate(${tooltipX}, ${tooltipY})`} className="diagram-tooltip">
            <rect width="96" height="38" rx="10" ry="10" className="diagram-tooltip-box" />
            <text x="10" y="16" className="diagram-tooltip-text">
              x = {formatNumber(hoverPoint.x_m)} m
            </text>
            <text x="10" y="30" className="diagram-tooltip-text">
              {formatNumber(hoverPoint.value)} {unit}
            </text>
          </g>
        </>
      )}
    </svg>
  );
}

function BeamView({ nodes, supports = [] }) {
  const width = 900;
  const height = 260;
  const padding = 40;

  const xMin = nodes[0].x_m;
  const xMax = nodes[nodes.length - 1].x_m;
  const xSpan = xMax - xMin || 1;
  const baseY = height / 2;
  const maxAbsDeflection = Math.max(...nodes.map(n => Math.abs(n.vertical_displacement_mm))) || 1;
  const scaleY = 70 / maxAbsDeflection;

  const baselinePoints = `${padding},${baseY} ${width - padding},${baseY}`;
  const deformedPoints = nodes.map(node => {
    const x = padding + ((node.x_m - xMin) / xSpan) * (width - padding * 2);
    const y = baseY - node.vertical_displacement_mm * scaleY;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="beam-svg">
      <polyline points={baselinePoints} className="beam-baseline" />
      <polyline points={deformedPoints} className="beam-deformed" />
      {nodes.map((node, index) => {
        const x = padding + ((node.x_m - xMin) / xSpan) * (width - padding * 2);
        const y = baseY - node.vertical_displacement_mm * scaleY;
        const isSupport = index === 0 || index === nodes.length - 1;
        return (
          <circle
            key={index}
            cx={x}
            cy={y}
            r={isSupport ? 4.5 : 2.5}
            className="beam-node"
          />
        );
      })}
      {supports.map((support, index) => {
        const x = padding + ((support.position_m - xMin) / xSpan) * (width - padding * 2);
        return (
          <g key={`${support.support_type}-${support.position_m}-${index}`}>
            {renderSupportShape(support.support_type, x, baseY)}
          </g>
        );
      })}
    </svg>
  );
}

function CrossSectionView({ widthMm, depthMm }) {
  const width = 420;
  const height = 320;
  const marginX = 52;
  const marginY = 32;
  const drawableWidth = width - marginX * 2;
  const drawableHeight = height - marginY * 2;
  const scale = Math.min(drawableWidth / widthMm, drawableHeight / depthMm) * 0.9;
  const sectionWidth = widthMm * scale;
  const sectionHeight = depthMm * scale;
  const rectX = (width - sectionWidth) / 2;
  const rectY = (height - sectionHeight) / 2;
  const topY = rectY;
  const bottomY = rectY + sectionHeight;
  const leftX = rectX;
  const rightX = rectX + sectionWidth;
  const midX = leftX + sectionWidth / 2;
  const midY = topY + sectionHeight / 2;
  const verticalAxisTop = topY - 22;
  const horizontalAxisRight = rightX + 34;
  const bottomDimY = bottomY + 28;
  const leftDimX = leftX - 24;
  const dimTick = 7;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="section-svg" aria-label="Vista de sección transversal">
      <defs>
        <marker id="axisArrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="#2f6dff" />
        </marker>
      </defs>

      <text x={8} y={16} className="section-title">
        {formatNumber(widthMm)}/{formatNumber(depthMm)}
      </text>

      <rect
        x={rectX}
        y={rectY}
        width={sectionWidth}
        height={sectionHeight}
        className="section-shape"
        fill="#e58a00"
      />

      <line
        x1={leftX}
        y1={bottomDimY}
        x2={rightX}
        y2={bottomDimY}
        className="dimension-line"
      />
      <line x1={leftX} y1={bottomDimY - dimTick} x2={leftX} y2={bottomDimY + dimTick} className="dimension-line" />
      <line x1={rightX} y1={bottomDimY - dimTick} x2={rightX} y2={bottomDimY + dimTick} className="dimension-line" />
      <text x={midX} y={bottomDimY - 4} className="dimension-text" textAnchor="middle">
        {formatNumber(widthMm)}
      </text>

      <line
        x1={leftDimX}
        y1={topY}
        x2={leftDimX}
        y2={bottomY}
        className="dimension-line"
      />
      <line x1={leftDimX - dimTick} y1={topY} x2={leftDimX + dimTick} y2={topY} className="dimension-line" />
      <line x1={leftDimX - dimTick} y1={bottomY} x2={leftDimX + dimTick} y2={bottomY} className="dimension-line" />
      <text
        x={leftDimX - 8}
        y={midY}
        className="dimension-text dimension-text-vertical"
        dominantBaseline="middle"
        textAnchor="middle"
      >
        {formatNumber(depthMm)}
      </text>

      <line
        x1={midX}
        y1={midY}
        x2={midX}
        y2={verticalAxisTop}
        className="section-axis"
        markerEnd="url(#axisArrow)"
      />
      <line
        x1={midX}
        y1={midY}
        x2={horizontalAxisRight}
        y2={midY}
        className="section-axis"
        markerEnd="url(#axisArrow)"
      />
      <circle cx={midX} cy={midY} r="2.4" className="section-center" />
      <text x={midX - 8} y={verticalAxisTop - 4} className="axis-label" textAnchor="middle">
        y
      </text>
      <text x={horizontalAxisRight + 8} y={midY + 4} className="axis-label" dominantBaseline="middle">
        z
      </text>
    </svg>
  );
}

function buildFallbackResponse(payload) {
  const length = payload.span.length_m;
  const elements = payload.span.element_count;
  const q = payload.loads[0].value_kN_per_m;
  const e = payload.material.modulus_of_elasticity_mpa;
  const inertia = (63 * Math.pow(200, 3)) / 12;
  const loadMagnitude = Math.abs(q);
  const maxMoment = (loadMagnitude * Math.pow(length, 2)) / 8;
  const maxShear = (loadMagnitude * length) / 2;
  const maxDeflection = (5 * loadMagnitude * Math.pow(length * 1000, 4)) / (384 * e * inertia);
  const nodeCount = elements + 1;
  const step = length / elements;

  const nodes = [];
  const shearPoints = [];
  const momentPoints = [];
  const deflectionPoints = [];
  const appendPoint = (points, x, value) => {
    const lastPoint = points[points.length - 1];
    if (lastPoint && lastPoint.x_m === x && Math.abs(lastPoint.value - value) < 1e-9) {
      return;
    }
    points.push({ x_m: x, value });
  };

  for (let index = 0; index < nodeCount; index += 1) {
    const x = index * step;
    const shear = maxShear - loadMagnitude * x;
    const moment = (loadMagnitude * x * (length - x)) / 2;
    const deflection = -((loadMagnitude * 1000 * x * 1000) / (24 * e * inertia)) * (Math.pow(length * 1000, 3) - 2 * length * 1000 * Math.pow(x * 1000, 2) + Math.pow(x * 1000, 3));

    nodes.push({
      node_id: index,
      x_m: x,
      vertical_displacement_mm: deflection,
      rotation_rad: 0,
    });
    if (index === 0) {
      appendPoint(shearPoints, x, 0);
      appendPoint(shearPoints, x, maxShear);
      appendPoint(momentPoints, x, 0);
    } else if (index === nodeCount - 1) {
      appendPoint(shearPoints, x, shear);
      appendPoint(shearPoints, x, 0);
      appendPoint(momentPoints, x, 0);
    } else {
      appendPoint(shearPoints, x, shear);
      appendPoint(momentPoints, x, moment);
    }
    deflectionPoints.push({ x_m: x, value: deflection });
  }

  return {
    summary: {
      total_nodes: nodeCount,
      total_elements: elements,
      max_deflection_mm: maxDeflection,
      max_deflection_position_m: length / 2,
      max_moment_kNm: maxMoment,
      max_moment_position_m: length / 2,
      max_shear_kN: maxShear,
      max_shear_position_m: 0,
    },
    nodes,
    diagrams: [
      {
        diagram_type: "shear",
        unit: "kN",
        points: shearPoints,
      },
      {
        diagram_type: "moment",
        unit: "kNm",
        points: momentPoints,
      },
      {
        diagram_type: "deflection",
        unit: "mm",
        points: deflectionPoints,
      },
    ],
  };
}

export default App;
