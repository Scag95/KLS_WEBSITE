import React from "react";
import "./KertoRipa.css";

const SECTION_OPTIONS = [
  {
    id: "ribbed_top",
    title: "Ribbed Slab (Top)",
    description: "Losa superior de madera (Kerto-Q) soportada por nervios verticales (Kerto-S). Ideal para cubiertas ligeras.",
    svg: (
      <svg viewBox="0 0 100 80" className="section-icon">
        <rect x="10" y="20" width="80" height="10" rx="2" className="kerto-q" />
        <rect x="25" y="30" width="15" height="35" rx="1" className="kerto-s" />
        <rect x="60" y="30" width="15" height="35" rx="1" className="kerto-s" />
      </svg>
    )
  },
  {
    id: "ribbed_bottom",
    title: "Ribbed Slab (Bottom)",
    description: "Nervios verticales apoyados sobre una losa inferior. Útil como encofrado perdido o plataformas invertidas.",
    svg: (
      <svg viewBox="0 0 100 80" className="section-icon">
        <rect x="25" y="15" width="15" height="35" rx="1" className="kerto-s" />
        <rect x="60" y="15" width="15" height="35" rx="1" className="kerto-s" />
        <rect x="10" y="50" width="80" height="10" rx="2" className="kerto-q" />
      </svg>
    )
  },
  {
    id: "box",
    title: "Box Slab",
    description: "Losa superior e inferior formando sección en cajón cerrado. Máxima inercia y resistencia al fuego.",
    svg: (
      <svg viewBox="0 0 100 80" className="section-icon">
        <rect x="10" y="15" width="80" height="10" rx="2" className="kerto-q" />
        <rect x="25" y="25" width="15" height="30" rx="1" className="kerto-s" />
        <rect x="60" y="25" width="15" height="30" rx="1" className="kerto-s" />
        <rect x="10" y="55" width="80" height="10" rx="2" className="kerto-q" />
      </svg>
    )
  },
  {
    id: "open_box",
    title: "Open Box Slab",
    description: "Similar al cajón pero con losa inferior discontinua. Facilita el paso de conductos y tuberías.",
    svg: (
      <svg viewBox="0 0 100 80" className="section-icon">
        <rect x="10" y="15" width="80" height="10" rx="2" className="kerto-q" />
        <rect x="25" y="25" width="15" height="30" rx="1" className="kerto-s" />
        <rect x="60" y="25" width="15" height="30" rx="1" className="kerto-s" />
        <rect x="15" y="55" width="35" height="8" rx="1" className="kerto-s" />
        <rect x="50" y="55" width="35" height="8" rx="1" className="kerto-s" />
      </svg>
    )
  }
];

export default function Step1SectionType({ value, onChange }) {
  return (
    <div className="wizard-step step-section-type">
      <div className="step-header">
        <h2>Paso 1: Tipo de Sección</h2>
        <p>
          Selecciona la tipología de ensamblaje Kerto-Ripa. Esta decisión
          determinará los campos geométricos disponibles en los siguientes pasos
          y el modo de fallo principal del panel.
        </p>
      </div>

      <div className="section-cards-grid">
        {SECTION_OPTIONS.map((sec) => (
          <div
            key={sec.id}
            className={`section-card ${value === sec.id ? "selected" : ""}`}
            onClick={() => onChange(sec.id)}
          >
            <div className="card-illustration">
              {sec.svg}
            </div>
            <div className="card-content">
              <h3>{sec.title}</h3>
              <p>{sec.description}</p>
            </div>
            <div className="selection-ring"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
