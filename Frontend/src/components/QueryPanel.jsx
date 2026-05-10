import React, { useState } from "react";
import "../Styles/QueryPanel.css";

const SCHEMAS = {
    behovsvurdering: "Behovsvurdering",
    kostnadsoverslag: "Kostnadsoverslag",
};

export default function QueryPanel({
                                       show,
                                       setShow,
                                       formData,
                                       setFormData,
                                       kostnadsoverlagData,
                                       setKostnadsoverlagData,
                                       generateApplication,
                                       generateKostnadsoverlag,
                                   }) {
    const [activeSchema, setActiveSchema] = useState("behovsvurdering");

    const handleChange = (setter) => (e) => {
        const { name, value, type, checked } = e.target;
        setter(prev => ({
            ...prev,
            [name]: type === "checkbox" ? checked : value
        }));
    };

    const handleGenerate = () => {
        if (activeSchema === "behovsvurdering") generateApplication();
        else generateKostnadsoverlag();
    };

    const handleReset = () => {
        if (activeSchema === "behovsvurdering") {
            setFormData({});
        } else {
            setKostnadsoverlagData({});
        }
    };

    return (
        <div className={`slide-panel ${show ? "open" : ""}`}>
            <div className="panel-header">
                <select
                    className="schema-select"
                    value={activeSchema}
                    onChange={(e) => setActiveSchema(e.target.value)}
                >
                    {Object.entries(SCHEMAS).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                    ))}
                </select>
                <button onClick={() => setShow(false)}>✕</button>
            </div>

            <div className="panel-content">

                {/* ── BEHOVSVURDERING ───────────────────────────────── */}
                {activeSchema === "behovsvurdering" && (<>

                    <div className="field-group">
                        <label>1. Type anlegg</label>
                        <select name="typeAnlegg" value={formData.typeAnlegg || ""} onChange={handleChange(setFormData)}>
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
                                onChange={handleChange(setFormData)}
                            />
                        )}
                    </div>

                    <div className="field-group">
                        <label>2. Behov – innhold og dimensjonering</label>
                        <textarea
                            name="behovBeskrivelse"
                            placeholder="Beskriv behovet, f.eks. antall brukere, type bruk, kapasitet..."
                            value={formData.behovBeskrivelse || ""}
                            onChange={handleChange(setFormData)}
                            rows={3}
                        />
                        <input
                            name="antallBrukere"
                            placeholder="Estimert antall brukere"
                            type="number"
                            value={formData.antallBrukere || ""}
                            onChange={handleChange(setFormData)}
                        />
                    </div>

                    <div className="field-group">
                        <label>3. Vurdering i kommunens planer</label>
                        <textarea
                            name="kommunalePlanerBeskrivelse"
                            placeholder="Beskriv hvordan anlegget er vurdert i kommunens planer..."
                            value={formData.kommunalePlanerBeskrivelse || ""}
                            onChange={handleChange(setFormData)}
                            rows={3}
                        />
                    </div>

                    <div className="field-group">
                        <label>4. Plassering relativt til andre anlegg</label>
                        <textarea
                            name="avstandAndreAnlegg"
                            placeholder="Beskriv avstand til lignende anlegg i nærheten..."
                            value={formData.avstandAndreAnlegg || ""}
                            onChange={handleChange(setFormData)}
                            rows={2}
                        />
                        <input
                            name="avstandKm"
                            placeholder="Avstand til nærmeste lignende anlegg (km)"
                            type="number"
                            step="0.1"
                            value={formData.avstandKm || ""}
                            onChange={handleChange(setFormData)}
                        />
                    </div>

                    <div className="field-group">
                        <label>5. Innbyggertall og befolkningsdata</label>
                        <input name="kommune" placeholder="Kommune" value={formData.kommune || ""} onChange={handleChange(setFormData)} />
                        <input name="innbyggertall" placeholder="Innbyggertall i kommunen" type="number" value={formData.innbyggertall || ""} onChange={handleChange(setFormData)} />
                        <input name="befolkningINeromraade" placeholder="Befolkning i nærmiljøet/nedslagsfeltet" type="number" value={formData.befolkningINeromraade || ""} onChange={handleChange(setFormData)} />
                    </div>

                    <div className="field-group">
                        <label>6. Beskrivelse av brukerne</label>
                        <textarea
                            name="brukerBeskrivelse"
                            placeholder="Hvem er brukerne? Aldersgrupper, kjønn, funksjonsnivå, skoler, lag..."
                            value={formData.brukerBeskrivelse || ""}
                            onChange={handleChange(setFormData)}
                            rows={3}
                        />
                    </div>

                    <div className="field-group">
                        <label>7. Idrettslag og medlemstall</label>
                        <input name="idrettslag" placeholder="Navn på idrettslag/-lag som skal bruke anlegget" value={formData.idrettslag || ""} onChange={handleChange(setFormData)} />
                        <input name="antallMedlemmer" placeholder="Totalt antall medlemmer" type="number" value={formData.antallMedlemmer || ""} onChange={handleChange(setFormData)} />
                    </div>

                    <div className="field-group">
                        <label>8. Driftsansvarlig</label>
                        <input name="driftsansvarlig" placeholder="Hvem skal drifte anlegget?" value={formData.driftsansvarlig || ""} onChange={handleChange(setFormData)} />
                        <select name="driftsmodell" value={formData.driftsmodell || ""} onChange={handleChange(setFormData)}>
                            <option value="">Velg driftsmodell</option>
                            <option value="kommunal">Kommunal drift</option>
                            <option value="idrettslag">Idrettslag</option>
                            <option value="stiftelse">Stiftelse/AS</option>
                            <option value="interkommunal">Interkommunalt samarbeid</option>
                            <option value="annet">Annet</option>
                        </select>
                    </div>

                </>)}

                {/* ── KOSTNADSOVERSLAG ──────────────────────────────── */}
                {activeSchema === "kostnadsoverslag" && (<>

                    <div className="field-group">
                        <label>Prosjekt og anlegg</label>
                        <input name="prosjektNavn" placeholder="Prosjektnavn" value={kostnadsoverlagData.prosjektNavn || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="kommune" placeholder="Kommune" value={kostnadsoverlagData.kommune || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <select name="typeAnlegg" value={kostnadsoverlagData.typeAnlegg || ""} onChange={handleChange(setKostnadsoverlagData)}>
                            <option value="">Velg type anlegg</option>
                            <option value="fotballbane">Fotballbane</option>
                            <option value="flerbrukshall">Flerbrukshall</option>
                            <option value="svommehall">Svømmehall</option>
                            <option value="friidrettsbane">Friidrettsbane</option>
                            <option value="ishall">Ishall</option>
                            <option value="tennisbane">Tennisbane</option>
                            <option value="annet">Annet</option>
                        </select>
                        <input name="anleggStorrelse" placeholder="Størrelse på anlegget (m²)" type="number" value={kostnadsoverlagData.anleggStorrelse || ""} onChange={handleChange(setKostnadsoverlagData)} />
                    </div>

                    <div className="field-group">
                        <label>Tilskuddsberettigede kostnader</label>
                        <input name="grunnarb" placeholder="Grunnarbeid og sprengning (kr)" type="number" value={kostnadsoverlagData.grunnarb || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="dreneringKr" placeholder="Drenering og avløp (kr)" type="number" value={kostnadsoverlagData.dreneringKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="aktivitetsflateKr" placeholder="Aktivitetsflate/dekke (kr)" type="number" value={kostnadsoverlagData.aktivitetsflateKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="gjerdeUtstyrKr" placeholder="Gjerde, mål og utstyr (kr)" type="number" value={kostnadsoverlagData.gjerdeUtstyrKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="garderodeKr" placeholder="Garderobe og sanitær (kr)" type="number" value={kostnadsoverlagData.garderodeKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="lysanleggKr" placeholder="Lysanlegg (kr)" type="number" value={kostnadsoverlagData.lysanleggKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="andreKostnaderTilskudd" placeholder="Andre tilskuddsberettigede kostnader (kr)" type="number" value={kostnadsoverlagData.andreKostnaderTilskudd || ""} onChange={handleChange(setKostnadsoverlagData)} />
                    </div>

                    <div className="field-group">
                        <label>Ikke tilskuddsberettigede kostnader</label>
                        <input name="tribuneKr" placeholder="Tribuneanlegg (kr)" type="number" value={kostnadsoverlagData.tribuneKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="parkeringKr" placeholder="Parkering og veier (kr)" type="number" value={kostnadsoverlagData.parkeringKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="avgifterKr" placeholder="Avgifter og gebyrer (kr)" type="number" value={kostnadsoverlagData.avgifterKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="andreKostnaderIkke" placeholder="Andre ikke tilskuddsberettigede kostnader (kr)" type="number" value={kostnadsoverlagData.andreKostnaderIkke || ""} onChange={handleChange(setKostnadsoverlagData)} />
                    </div>

                    <div className="field-group">
                        <label>Dugnad</label>
                        <input name="dugnadTimer" placeholder="Estimert antall dugnadstimer" type="number" value={kostnadsoverlagData.dugnadTimer || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="dugnadTimepris" placeholder="Timepris for dugnad (kr)" type="number" value={kostnadsoverlagData.dugnadTimepris || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <textarea name="dugnadBeskrivelse" placeholder="Beskriv dugnadsarbeidet..." value={kostnadsoverlagData.dugnadBeskrivelse || ""} onChange={handleChange(setKostnadsoverlagData)} rows={2} />
                    </div>

                    <div className="field-group">
                        <label>Finansiering</label>
                        <input name="spillemidlerKr" placeholder="Søkt spillemidler (kr)" type="number" value={kostnadsoverlagData.spillemidlerKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="kommunaltTilskuddKr" placeholder="Kommunalt tilskudd (kr)" type="number" value={kostnadsoverlagData.kommunaltTilskuddKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="egneMiddlerKr" placeholder="Egne midler/egenkapital (kr)" type="number" value={kostnadsoverlagData.egneMiddlerKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="andreTilskuddKr" placeholder="Andre tilskudd (kr)" type="number" value={kostnadsoverlagData.andreTilskuddKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                        <input name="lanKr" placeholder="Lån (kr)" type="number" value={kostnadsoverlagData.lanKr || ""} onChange={handleChange(setKostnadsoverlagData)} />
                    </div>

                </>)}

            </div>

            <div className="panel-footer">
                <button className="generate-btn" onClick={handleGenerate}>
                    Generer {SCHEMAS[activeSchema].toLowerCase()}
                </button>
                <button className="reset-btn" onClick={handleReset}>
                    Tøm skjema
                </button>
            </div>
        </div>
    );
}