import React from "react";
import "../Styles/QueryPanel.css";

export default function QueryPanel({
  show,
  setShow,
  formData,
  setFormData,
  generateApplication
}) {

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };

  return (
    <div className={`slide-panel ${show ? "open" : ""}`}>
      <div className="panel-header">
        <h2>Behovsvurdering</h2>
        <button className="close-btn" onClick={() => setShow(false)}>✕</button>
      </div>

      <div className="panel-content">

        {/* Type anlegg */}
        <div className="field-group">
          <label>1. Type anlegg</label>
          <select name="typeAnlegg" value={formData.typeAnlegg || ""} onChange={handleChange}>
            <option value="">Velg type anlegg</option>
            <option value="fotballbane">Fotballbane</option>
            <option value="flerbrukshall">Flerbrukshall</option>
            <option value="svommehall">Svømmehall</option>
            <option value="friidrettsbane">Friidrettsbane</option>
            <option value="ishall">Ishall</option>
            <option value="tennisbane">Tennisbane</option>
            <option value="annet">Annet</option>
          </select>
          {formData.typeAnlegg === "annet" && (
            <input
              name="typeAnleggAnnet"
              placeholder="Beskriv type anlegg"
              value={formData.typeAnleggAnnet || ""}
              onChange={handleChange}
            />
          )}
        </div>

        {/* Behove, innhold og dimensjonering */}
        <div className="field-group">
          <label>2. Behov – innhold og dimensjonering</label>
          <textarea
            name="behovBeskrivelse"
            placeholder="Beskriv behovet, f.eks. antall brukere, type bruk, kapasitet..."
            value={formData.behovBeskrivelse || ""}
            onChange={handleChange}
            rows={3}
          />
          <input
            name="antallBrukere"
            placeholder="Estimert antall brukere"
            type="number"
            value={formData.antallBrukere || ""}
            onChange={handleChange}
          />
        </div>

        {/* Kommunale planer */}
        <div className="field-group">
          <label>3. Vurdering i kommunens planer</label>
          <textarea
            name="kommunalePlanerBeskrivelse"
            placeholder="Beskriv hvordan anlegget er vurdert i kommunens planer (kommuneplan, idrettsplan, o.l.)..."
            value={formData.kommunalePlanerBeskrivelse || ""}
            onChange={handleChange}
            rows={3}
          />
        </div>

        {/* Avstand til andre anlegg */}
        <div className="field-group">
          <label>4. Plassering relativt til andre anlegg</label>
          <textarea
            name="avstandAndreAnlegg"
            placeholder="Beskriv avstand til lignende anlegg i nærheten..."
            value={formData.avstandAndreAnlegg || ""}
            onChange={handleChange}
            rows={2}
          />
          <input
            name="avstandKm"
            placeholder="Avstand til nærmeste lignende anlegg (km)"
            type="number"
            step="0.1"
            value={formData.avstandKm || ""}
            onChange={handleChange}
          />
        </div>

        {/* Innbyggertall befolkningsdata */}
        <div className="field-group">
          <label>5. Innbyggertall og befolkningsdata</label>
          <input
            name="kommune"
            placeholder="Kommune"
            value={formData.kommune || ""}
            onChange={handleChange}
          />
          <input
            name="innbyggertall"
            placeholder="Innbyggertall i kommunen"
            type="number"
            value={formData.innbyggertall || ""}
            onChange={handleChange}
          />
          <input
            name="befolkningINeromraade"
            placeholder="Befolkning i nærmiljøet/nedslagsfeltet"
            type="number"
            value={formData.befolkningINeromraade || ""}
            onChange={handleChange}
          />
        </div>

        {/* Beskrivelse av brukerne */}
        <div className="field-group">
          <label>6. Beskrivelse av brukerne</label>
          <textarea
            name="brukerBeskrivelse"
            placeholder="Hvem er brukerne? Aldersgrupper, kjønn, funksjonsnivå, skoler, lag, foreninger..."
            value={formData.brukerBeskrivelse || ""}
            onChange={handleChange}
            rows={3}
          />
        </div>

        {/* Antall medlemmer */}
        <div className="field-group">
          <label>7. Idrettslag og medlemstall</label>
          <input
            name="idrettslag"
            placeholder="Navn på idrettslag/-lag som skal bruke anlegget"
            value={formData.idrettslag || ""}
            onChange={handleChange}
          />
          <input
            name="antallMedlemmer"
            placeholder="Totalt antall medlemmer"
            type="number"
            value={formData.antallMedlemmer || ""}
            onChange={handleChange}
          />
        </div>

       {/* Drift */}
        <div className="field-group">
          <label>8. Driftsansvarlig</label>
          <input
            name="driftsansvarlig"
            placeholder="Hvem skal drifte anlegget? (organisasjon, kommune, lag...)"
            value={formData.driftsansvarlig || ""}
            onChange={handleChange}
          />
          <select name="driftsmodell" value={formData.driftsmodell || ""} onChange={handleChange}>
            <option value="">Velg driftsmodell</option>
            <option value="kommunal">Kommunal drift</option>
            <option value="idrettslag">Idrettslag</option>
            <option value="stiftelse">Stiftelse/AS</option>
            <option value="interkommunal">Interkommunalt samarbeid</option>
            <option value="annet">Annet</option>
          </select>
        </div>

        <button className="generate-btn" onClick={generateApplication}>
          Generer behovsvurdering
        </button>

      </div>
    </div>
  );
}