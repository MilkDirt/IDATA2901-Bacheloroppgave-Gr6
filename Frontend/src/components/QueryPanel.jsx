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
        <h2>Ny Byggesøknad</h2>
        <button onClick={() => setShow(false)}>✕</button>
      </div>

      <div className="panel-content">

        <input
          name="adresse"
          placeholder="Adresse"
          value={formData.adresse}
          onChange={handleChange}
        />

        <input
          name="gnr"
          placeholder="Gnr"
          value={formData.gnr}
          onChange={handleChange}
        />

        <input
          name="bnr"
          placeholder="Bnr"
          value={formData.bnr}
          onChange={handleChange}
        />

        <input
          name="kommune"
          placeholder="Kommune"
          value={formData.kommune}
          onChange={handleChange}
        />

        <select
          name="tiltakstype"
          value={formData.tiltakstype}
          onChange={handleChange}
        >
          <option value="">Velg tiltakstype</option>
          <option value="tilbygg">Tilbygg</option>
          <option value="nybygg">Nybygg</option>
          <option value="bruksendring">Bruksendring</option>
        </select>

        <input
          name="bra"
          placeholder="BRA (m²)"
          value={formData.bra}
          onChange={handleChange}
        />

        <input
          name="bya"
          placeholder="BYA (m²)"
          value={formData.bya}
          onChange={handleChange}
        />

        <input
          name="hoyde"
          placeholder="Høyde (meter)"
          value={formData.hoyde}
          onChange={handleChange}
        />

        <label className="checkbox">
          <input
            type="checkbox"
            name="nabovarsel"
            checked={formData.nabovarsel}
            onChange={handleChange}
          />
          Nabovarsel sendt
        </label>

        <button className="generate-btn" onClick={generateApplication}>
          Generer søknad
        </button>

      </div>
    </div>
  );
}