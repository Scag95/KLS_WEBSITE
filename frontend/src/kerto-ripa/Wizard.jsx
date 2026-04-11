import React, { useState } from "react";
import Step1SectionType from "./Step1SectionType";
import "./KertoRipa.css";

export default function KertoRipaWizard() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    sectionType: "ribbed_top",
    geometry: null,
    loads: null,
    supports: null
  });

  const handleSectionTypeChange = (typeId) => {
    setFormData((prev) => ({ ...prev, sectionType: typeId }));
  };

  return (
    <div className="kerto-ripa-wizard">
      {step === 1 && (
        <Step1SectionType
          value={formData.sectionType}
          onChange={handleSectionTypeChange}
        />
      )}
      
      {/* Contenedor temporal de botones de depuración / navegación */}
      <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
         <button 
           disabled={step === 1}
           style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', border: '1px solid #ccc', background: 'white' }}
         >
            Atrás
         </button>
         <button 
           style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', background: '#8a6a4b', color: 'white', border: 'none' }}
         >
            Siguiente Paso
         </button>
      </div>
    </div>
  );
}
