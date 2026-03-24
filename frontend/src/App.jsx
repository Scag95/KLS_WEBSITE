import { useState, useEffect } from "react";

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

function parseNumberFields(section) {
  return Object.fromEntries(
    Object.entries(section).map(([key, value]) => [key, key === "grade" || key === "design_standard" ? value : Number(value)]),
  );
}

function App() {
  const [activeTab, setActiveTab] = useState("geometry");
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestError, setRequestError] = useState("");

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
          className={`tab-button ${activeTab === "results" ? "active" : ""}`}
          onClick={() => setActiveTab("results")}
        >
          <span className="tab-icon">📊</span>
          Resultados
        </button>
      </div>

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

            {activeTab === "geometry" && (
              <>
                <FormGroup title="Geometría longitudinal">
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
            )}

            {activeTab === "loads" && (
              <>
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
              </>
            )}

            {activeTab === "results" && (
              <div className="results-preview">
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
                      <ResultCard label="Momento de inercia" value={result.results.section_inertia_mm4} unit="mm⁴" />
                      <ResultCard label="Módulo de sección" value={result.results.section_modulus_mm3} unit="mm³" />
                      <ResultCard label="Tensión de flexión" value={result.results.bending_stress_mpa} unit="MPa" />
                      <ResultCard label="Tensión de cortante" value={result.results.shear_stress_mpa} unit="MPa" />
                      <ResultCard label="Flecha admisible" value={result.results.allowable_deflection_mm} unit="mm" />
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
              </div>
            )}

            {activeTab === "section" && (
              <>
                <FormGroup title="Sección transversal">
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

        {(activeTab === "geometry" || activeTab === "results" || activeTab === "section") && (
          <section className="panel panel-diagrams">
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
            <DiagramsSection result={result} view={activeTab} form={form} />
          </section>
        )}
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

function DiagramsSection({ result, view = "results", form }) {
  // Usar parámetros del cálculo si existe, sino valores por defecto
  const defaultParams = {
    length: 4.0,
    elements: 100, // valor fijo interno
    load: -1.6,
    modulus: 11000,
  };

  const calculatedParams = result ? {
    length: result.inputs.geometry.span_m,
    elements: 100, // mantener fijo internamente
    load: -result.results.line_load_kN_per_m, // negativo para downward
    modulus: result.inputs.timber.modulus_of_elasticity_mpa,
  } : defaultParams;
  const sectionDimensions = result
    ? {
        widthMm: result.inputs.geometry.width_mm,
        depthMm: result.inputs.geometry.depth_mm,
      }
    : {
        widthMm: Number(form?.geometry.width_mm ?? 63),
        depthMm: Number(form?.geometry.depth_mm ?? 200),
      };
  const supports = (form?.supports ?? []).map((support) => ({
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
      project_name: result ? result.inputs.project_name : "Beam example",
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
      const response = await fetch(`${API_BASE_URL}/analyze/beam`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Error en la API de análisis de viga");
      }

      const data = await response.json();
      setDiagramData(data);
    } catch (err) {
      setError(err.message);
      // Fallback local
      setDiagramData(buildFallbackResponse(payload));
    } finally {
      setLoading(false);
    }
  };

  // Cargar diagramas cuando cambia el result
  useEffect(() => {
    loadDiagrams(calculatedParams);
  }, [result]);

  // Cargar diagramas iniciales
  useEffect(() => {
    if (!result) {
      loadDiagrams(defaultParams);
    }
  }, []);

  return (
    <section className="panel panel-diagrams">
      <div className="panel-heading">
        <h2>Diagramas estructurales</h2>
        <p>
          {result
            ? "Diagramas sincronizados con el cálculo del forjado"
            : "Diagramas con parámetros por defecto"
          }
          {error && " (calculando localmente)"}
          {loading && " - Actualizando..."}
        </p>
      </div>

      {result && view === "results" && (
        <div className="diagram-notice">
          <p>Los diagramas muestran la viga calculada:
            <strong>luz {result.inputs.geometry.span_m}m</strong>,
            <strong>carga {result.results.line_load_kN_per_m} kN/m</strong>,
            <strong>E {result.inputs.timber.modulus_of_elasticity_mpa} MPa</strong>.
          </p>
        </div>
      )}

      {diagramData && (
        <>
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

          {view === "results" && (
            <div className="metrics-grid metrics-grid-compact">
              <ResultCard label="Flecha máxima" value={diagramData.summary.max_deflection_mm} unit="mm" />
              <ResultCard label="Momento máximo" value={diagramData.summary.max_moment_kNm} unit="kNm" />
              <ResultCard label="Cortante máximo" value={diagramData.summary.max_shear_kN} unit="kN" />
              <ResultCard label="Nodos" value={diagramData.summary.total_nodes} unit="" />
              <ResultCard label="Elementos" value={diagramData.summary.total_elements} unit="" />
            </div>
          )}

          {view === "results" && (
            <article className="diagram-card beam-view-card">
              <div className="diagram-card-header">
                <h3>Viga y deformada</h3>
                <span>Vista general</span>
              </div>
              <BeamView nodes={diagramData.nodes} />
              <div className="diagram-card-footer">
                La línea clara representa el eje no deformado y la línea azul la deformada amplificada.
              </div>
            </article>
          )}

          {view === "section" && (
            <SectionCard widthMm={sectionDimensions.widthMm} depthMm={sectionDimensions.depthMm} />
          )}

          {view === "results" && (
            <div id="diagram-grid" className="diagram-grid">
              {diagramData.diagrams.map((diagram) => (
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
      <LineChart points={diagram.points} type={diagram.diagram_type} />
      <div className="diagram-card-footer">
        Valor máximo: {formatNumber(maxAbs)} {diagram.unit}
      </div>
    </article>
  );
}

function LineChart({ points, type }) {
  const width = 520;
  const height = 220;
  const padding = 26;

  const xValues = points.map(p => p.x_m);
  const yValues = points.map(p => p.value);
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...yValues, 0);
  const maxY = Math.max(...yValues, 0);
  const ySpan = maxY - minY || 1;
  const xSpan = maxX - minX || 1;
  const zeroY = padding + ((maxY - 0) / ySpan) * (height - padding * 2);

  const pointsStr = points.map(point => {
    const x = padding + ((point.x_m - minX) / xSpan) * (width - padding * 2);
    const y = padding + ((maxY - point.value) / ySpan) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className={`diagram-svg ${type}`}>
      <line
        x1={padding}
        x2={width - padding}
        y1={zeroY}
        y2={zeroY}
        className="axis-line"
      />
      <polyline
        points={pointsStr}
        className="diagram-line"
      />
      {points.map((point, index) => {
        const x = padding + ((point.x_m - minX) / xSpan) * (width - padding * 2);
        const y = padding + ((maxY - point.value) / ySpan) * (height - padding * 2);
        return (
          <circle
            key={index}
            cx={x}
            cy={y}
            r="4"
            className="diagram-point"
          />
        );
      })}
    </svg>
  );
}

function BeamView({ nodes }) {
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
    const y = baseY + node.vertical_displacement_mm * scaleY;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="beam-svg">
      <polyline points={baselinePoints} className="beam-baseline" />
      <polyline points={deformedPoints} className="beam-deformed" />
      {nodes.map((node, index) => {
        const x = padding + ((node.x_m - xMin) / xSpan) * (width - padding * 2);
        const y = baseY + node.vertical_displacement_mm * scaleY;
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
      {/* Supports */}
      <polygon points={`${padding - 16},${baseY + 30} ${padding + 16},${baseY + 30} ${padding},${baseY + 6}`} className="beam-support" />
      <polygon points={`${width - padding - 16},${baseY + 30} ${width - padding + 16},${baseY + 30} ${width - padding},${baseY + 6}`} className="beam-support" />
      {/* Roller circles */}
      <circle cx={width - padding - 8} cy={baseY + 38} r="4" className="beam-support" />
      <circle cx={width - padding + 8} cy={baseY + 38} r="4" className="beam-support" />
    </svg>
  );
}

function CrossSectionView({ widthMm, depthMm }) {
  const width = 420;
  const height = 320;
  const marginX = 88;
  const marginY = 40;
  const drawableWidth = width - marginX * 2;
  const drawableHeight = height - marginY * 2;
  const scale = Math.min(drawableWidth / widthMm, drawableHeight / depthMm);
  const sectionWidth = widthMm * scale;
  const sectionHeight = depthMm * scale;
  const rectX = (width - sectionWidth) / 2;
  const rectY = (height - sectionHeight) / 2;
  const topY = rectY;
  const bottomY = rectY + sectionHeight;
  const leftX = rectX;
  const rightX = rectX + sectionWidth;
  const midX = width / 2;
  const midY = height / 2;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="section-svg" aria-label="Vista de sección transversal">
      <defs>
        <linearGradient id="sectionFill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#ffd4a8" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#d87c45" stopOpacity="0.88" />
        </linearGradient>
      </defs>

      <rect
        x={rectX}
        y={rectY}
        width={sectionWidth}
        height={sectionHeight}
        rx="18"
        className="section-shape"
        fill="url(#sectionFill)"
      />

      <line x1={leftX} y1={topY - 18} x2={rightX} y2={topY - 18} className="dimension-line" />
      <line x1={leftX} y1={topY - 26} x2={leftX} y2={topY - 2} className="dimension-line" />
      <line x1={rightX} y1={topY - 26} x2={rightX} y2={topY - 2} className="dimension-line" />
      <text x={midX} y={topY - 24} className="dimension-text" textAnchor="middle">
        {formatNumber(widthMm)} mm
      </text>

      <line x1={rightX + 22} y1={topY} x2={rightX + 22} y2={bottomY} className="dimension-line" />
      <line x1={rightX + 12} y1={topY} x2={rightX + 32} y2={topY} className="dimension-line" />
      <line x1={rightX + 12} y1={bottomY} x2={rightX + 32} y2={bottomY} className="dimension-line" />
      <text x={rightX + 34} y={midY} className="dimension-text" dominantBaseline="middle">
        {formatNumber(depthMm)} mm
      </text>

      <line x1={leftX + 18} y1={midY} x2={rightX - 18} y2={midY} className="section-axis" />
      <line x1={midX} y1={topY + 18} x2={midX} y2={bottomY - 18} className="section-axis" />
      <circle cx={midX} cy={midY} r="4.5" className="section-center" />
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
    shearPoints.push({ x_m: x, value: x === length ? 0 : shear });
    momentPoints.push({ x_m: x, value: moment });
    deflectionPoints.push({ x_m: x, value: deflection });
  }

  return {
    summary: {
      total_nodes: nodeCount,
      total_elements: elements,
      max_deflection_mm: maxDeflection,
      max_deflection_position_m: length / 2,
      max_moment_kNm: maxMoment,
      max_shear_kN: maxShear,
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
