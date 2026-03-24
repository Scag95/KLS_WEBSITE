import { useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

const initialForm = {
  project_name: "Vivienda unifamiliar",
  geometry: {
    span_m: "4.00",
    spacing_m: "0.40",
    width_mm: "63",
    depth_mm: "200",
  },
  timber: {
    grade: "C24",
    modulus_of_elasticity_mpa: "11000",
    allowable_bending_stress_mpa: "11.0",
    allowable_shear_stress_mpa: "1.2",
  },
  loads: {
    dead_load_kN_per_m2: "1.5",
    imposed_load_kN_per_m2: "2.0",
    additional_dead_load_kN_per_m2: "0.5",
  },
  criteria: {
    design_standard: "concept-v1",
    max_deflection_ratio: "300",
  },
};

function parseNumberFields(section) {
  return Object.fromEntries(
    Object.entries(section).map(([key, value]) => [key, key === "grade" || key === "design_standard" ? value : Number(value)]),
  );
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestError, setRequestError] = useState("");

  function handleChange(section, field, value) {
    if (!section) {
      setForm((current) => ({ ...current, [field]: value }));
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

  function validate() {
    const nextErrors = [];
    const numericGroups = [
      ["geometry", ["span_m", "spacing_m", "width_mm", "depth_mm"]],
      ["timber", ["modulus_of_elasticity_mpa", "allowable_bending_stress_mpa", "allowable_shear_stress_mpa"]],
      ["loads", ["dead_load_kN_per_m2", "imposed_load_kN_per_m2", "additional_dead_load_kN_per_m2"]],
      ["criteria", ["max_deflection_ratio"]],
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
      loads: parseNumberFields(form.loads),
      criteria: {
        ...parseNumberFields(form.criteria),
        design_standard: form.criteria.design_standard,
      },
    };

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/calculate/floor-joist`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const body = await response.json();
        const detail = body.detail?.map((item) => item.msg).join(" | ") || "La API devolvió un error.";
        throw new Error(detail);
      }

      const body = await response.json();
      setResult(body);
    } catch (error) {
      setRequestError(error.message || "No se pudo conectar con la API.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const governingCheck = result?.summary.governing_check ?? "Sin cálculo";

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

      <main className="layout">
        <section className="panel panel-form">
          <div className="panel-heading">
            <h2>Entradas</h2>
            <p>Los valores se envían en el formato que espera la API actual.</p>
          </div>

          <form onSubmit={handleSubmit} className="calc-form">
            <div className="field-grid single">
              <label>
                <span>Proyecto</span>
                <input
                  value={form.project_name}
                  onChange={(event) => handleChange(null, "project_name", event.target.value)}
                />
              </label>
            </div>

            <FormGroup title="Geometría">
              <Field label="Luz (m)" value={form.geometry.span_m} onChange={(value) => handleChange("geometry", "span_m", value)} />
              <Field label="Separación (m)" value={form.geometry.spacing_m} onChange={(value) => handleChange("geometry", "spacing_m", value)} />
              <Field label="Ancho (mm)" value={form.geometry.width_mm} onChange={(value) => handleChange("geometry", "width_mm", value)} />
              <Field label="Canto (mm)" value={form.geometry.depth_mm} onChange={(value) => handleChange("geometry", "depth_mm", value)} />
            </FormGroup>

            <FormGroup title="Madera">
              <Field label="Clase" value={form.timber.grade} onChange={(value) => handleChange("timber", "grade", value)} />
              <Field
                label="Módulo E (MPa)"
                value={form.timber.modulus_of_elasticity_mpa}
                onChange={(value) => handleChange("timber", "modulus_of_elasticity_mpa", value)}
              />
              <Field
                label="Flexión admisible (MPa)"
                value={form.timber.allowable_bending_stress_mpa}
                onChange={(value) => handleChange("timber", "allowable_bending_stress_mpa", value)}
              />
              <Field
                label="Cortante admisible (MPa)"
                value={form.timber.allowable_shear_stress_mpa}
                onChange={(value) => handleChange("timber", "allowable_shear_stress_mpa", value)}
              />
            </FormGroup>

            <FormGroup title="Cargas">
              <Field
                label="Carga permanente (kN/m2)"
                value={form.loads.dead_load_kN_per_m2}
                onChange={(value) => handleChange("loads", "dead_load_kN_per_m2", value)}
              />
              <Field
                label="Sobrecarga (kN/m2)"
                value={form.loads.imposed_load_kN_per_m2}
                onChange={(value) => handleChange("loads", "imposed_load_kN_per_m2", value)}
              />
              <Field
                label="Carga adicional (kN/m2)"
                value={form.loads.additional_dead_load_kN_per_m2}
                onChange={(value) => handleChange("loads", "additional_dead_load_kN_per_m2", value)}
              />
            </FormGroup>

            <FormGroup title="Criterio">
              <Field
                label="Base de cálculo"
                value={form.criteria.design_standard}
                onChange={(value) => handleChange("criteria", "design_standard", value)}
              />
              <Field
                label="Límite de flecha L/x"
                value={form.criteria.max_deflection_ratio}
                onChange={(value) => handleChange("criteria", "max_deflection_ratio", value)}
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
          </form>
        </section>

        <section className="panel panel-results">
          <div className="panel-heading">
            <h2>Resultados</h2>
            <p>Se actualizan con la respuesta del backend.</p>
          </div>

          {result ? (
            <>
              <div className="summary-band">
                <div>
                  <span className="metric-label">Estado</span>
                  <strong>{result.summary.passed ? "Cumple" : "No cumple"}</strong>
                </div>
                <div>
                  <span className="metric-label">Controla</span>
                  <strong>{result.summary.governing_check}</strong>
                </div>
                <div>
                  <span className="metric-label">Norma</span>
                  <strong>{result.inputs.criteria.design_standard}</strong>
                </div>
              </div>

              <div className="metrics-grid">
                <ResultCard label="Carga lineal" value={result.results.line_load_kN_per_m} unit="kN/m" />
                <ResultCard label="Momento máximo" value={result.results.max_moment_kNm} unit="kNm" />
                <ResultCard label="Cortante máximo" value={result.results.max_shear_kN} unit="kN" />
                <ResultCard label="Flecha" value={result.results.deflection_mm} unit="mm" />
              </div>

              <div className="checks-list">
                {result.checks.map((check) => (
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
                {result.warnings.length > 0 ? (
                  result.warnings.map((warning) => (
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
        </section>
      </main>
    </div>
  );
}

function FormGroup({ title, children }) {
  return (
    <section className="form-group">
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

function ResultCard({ label, value, unit }) {
  return (
    <article className="result-card">
      <span className="metric-label">{label}</span>
      <strong>{formatNumber(value)}</strong>
      <span>{unit}</span>
    </article>
  );
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-ES", {
    maximumFractionDigits: 3,
  }).format(value);
}

export default App;
