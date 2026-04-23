# -*- coding: utf-8 -*-
"""
Plugin Panel — Main launcher for the Bygg & Terreng plugin.
Provides a single persistent floating panel with buttons for all four tools.
Run this script once at the start of a Rhino session — the panel stays open.

Workflow:
  1. Hent Terreng    — fetch elevation from Kartverket and build 3D mesh
  2. Hent Satellitt  — drape aerial imagery over the terrain
  3. Generer Bygg    — generate building from a bounding box skeleton
  4. Plasser Bygg    — flatten terrain and snap building to correct height
"""
import Rhino
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed
import os
import sys

# Clear any cached versions of tool modules so we always get the latest on import
for _mod in ['terreng_generator', 'satelitt_tekstur', 'bygg_generator', 'plasser_bygg']:
    if _mod in sys.modules:
        del sys.modules[_mod]

# Point to src/components/ where the tool modules live
_src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'components')
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from terreng_generator import generate_terrain
from satelitt_tekstur import SatellittTeksturDialog
from bygg_generator import ByggGeneratorDialog
from plasser_bygg import PlasserByggDialog


class PluginPanel(ef.Form):
    """
    Persistent floating panel that launches each tool dialog on demand.
    Uses ef.Form so it stays open and non-blocking while the user works in Rhino.
    Coordinates entered once at the top are shared across all tools.
    """

    def __init__(self):
        super(PluginPanel, self).__init__()
        self.Title = "Bygg & Terreng Plugin"
        self.Padding = ed.Padding(16)
        self.Resizable = False
        self.Width = 340
        self.Height = 640
        self._build_ui()

    def _build_ui(self):
        """Build the full panel layout."""
        layout = ef.TableLayout()
        layout.Spacing = ed.Size(0, 6)

        subtitle = ef.Label()
        subtitle.Text = "Fyll inn koordinater og følg stegene i rekkefølge."
        subtitle.TextColor = ed.Colors.DarkGray
        subtitle.Width = 290
        layout.Rows.Add(ef.TableRow(ef.TableCell(subtitle)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(6))))

        # Shared coordinate inputs
        coord_box = ef.GroupBox()
        coord_box.Text = "GPS Koordinater (lat/lon fra Google Maps)"
        coord_box.Width = 290
        coord_layout = ef.TableLayout()
        coord_layout.Padding = ed.Padding(8)
        coord_layout.Spacing = ed.Size(6, 4)

        self.lat_input  = self._input("")
        self.lon_input  = self._input("")
        self.size_input = self._input("")

        coord_layout.Rows.Add(ef.TableRow(self._cell(self._label("Breddegrad (lat):")), self._cell(self.lat_input)))
        coord_layout.Rows.Add(ef.TableRow(self._cell(self._label("Lengdegrad (lon):")), self._cell(self.lon_input)))
        coord_layout.Rows.Add(ef.TableRow(self._cell(self._label("Størrelse (m):")),    self._cell(self.size_input)))
        coord_box.Content = coord_layout

        layout.Rows.Add(ef.TableRow(ef.TableCell(coord_box)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))

        # Step 1 — Terreng (no sub-dialog, runs directly)
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._heading("Steg 1 - Terreng"))))
        self.t_status = self._status("Klar til å hente terreng.")
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.t_status)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._button("Hent Terreng fra Kartverket", self.on_terreng))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))

        # Step 2 — Satellitt
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._heading("Steg 2 - Satellitt"))))
        self.s_status = self._status("Hent terreng først.")
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.s_status)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._button("Legg på satellittbilde", self.on_satelitt))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))

        # Step 3 — Bygg
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._heading("Steg 3 - Bygg"))))
        self.b_status = self._status("Velg en bounding box i Rhino.")
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.b_status)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._button("Generer Bygg fra skjelett", self.on_bygg))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))

        # Step 4 — Plasser
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._heading("Steg 4 - Plassering"))))
        self.p_status = self._status("Generer bygg og terreng først.")
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.p_status)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._button("Plasser Bygg på Terreng", self.on_plasser))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))

        self.Content = layout

        # Set defaults after Content assigned (Eto quirk)
        self.lat_input.Text  = "62.47433077311483"
        self.lon_input.Text  = "6.164769452950289"
        self.size_input.Text = "1000"

    # -----------------------------------------------------------------------
    # UI helpers
    # -----------------------------------------------------------------------

    def _heading(self, text):
        lbl = ef.Label()
        lbl.Text = text
        lbl.Font = ed.Font(lbl.Font.Family, lbl.Font.Size, ed.FontStyle.Bold)
        return lbl

    def _label(self, text):
        lbl = ef.Label()
        lbl.Text = text
        lbl.Width = 110
        return lbl

    def _input(self, default=""):
        box = ef.TextBox()
        box.Text = default
        box.Width = 150
        return box

    def _status(self, text="Klar."):
        lbl = ef.Label()
        lbl.Text = text
        lbl.TextColor = ed.Colors.Gray
        lbl.Width = 290
        return lbl

    def _button(self, text, handler):
        btn = ef.Button()
        btn.Text = text
        btn.Width = 290
        btn.Click += handler
        return btn

    def _spacer(self, height=8):
        lbl = ef.Label()
        lbl.Height = height
        return lbl

    def _cell(self, control):
        return ef.TableCell(control)

    def _set_status(self, label, text, color):
        label.Text = text
        label.TextColor = color

    def _get_coords(self):
        """Read shared coordinate inputs. Returns (lat, lon, size) or None if invalid."""
        try:
            return (
                float(self.lat_input.Text.strip().replace(",", ".")),
                float(self.lon_input.Text.strip().replace(",", ".")),
                float(self.size_input.Text.strip())
            )
        except:
            return None

    # -----------------------------------------------------------------------
    # Button handlers
    # -----------------------------------------------------------------------

    def on_terreng(self, sender, e):
        """
        Generate terrain directly from panel coordinates — no sub-dialog.
        Calls generate_terrain() from terreng_generator.py inline.
        """
        coords = self._get_coords()
        if not coords:
            self._set_status(self.t_status, "Feil: Ugyldig koordinater!", ed.Colors.Red)
            return

        lat, lon, size = coords
        self._set_status(self.t_status, "Laster ned fra Kartverket...", ed.Colors.Orange)

        try:
            success, message = generate_terrain(lat, lon, size)
            color = ed.Colors.Green if success else ed.Colors.Orange
            self._set_status(self.t_status, ("OK: " if success else "") + message, color)
            if success:
                self._set_status(self.s_status, "Klar - velg terreng-mesh for satellitt.", ed.Colors.Gray)
        except Exception as ex:
            self._set_status(self.t_status, "Feil: " + str(ex), ed.Colors.Red)

    def on_satelitt(self, sender, e):
        """Open Satellitt Tekstur with coordinates from the shared inputs."""
        coords = self._get_coords()
        if not coords:
            self._set_status(self.s_status, "Feil: Sjekk koordinater!", ed.Colors.Red)
            return
        lat, lon, size = coords
        self._set_status(self.s_status, "Åpner...", ed.Colors.Orange)
        try:
            dlg = SatellittTeksturDialog(lat=lat, lon=lon, size=size)
            dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
            self._set_status(self.s_status, "Ferdig.", ed.Colors.Green)
        except Exception as ex:
            self._set_status(self.s_status, "Feil: " + str(ex), ed.Colors.Red)

    def on_bygg(self, sender, e):
        """Open Bygg Generator dialog."""
        self._set_status(self.b_status, "Åpner...", ed.Colors.Orange)
        try:
            dlg = ByggGeneratorDialog()
            dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
            self._set_status(self.b_status, "Ferdig.", ed.Colors.Green)
        except Exception as ex:
            self._set_status(self.b_status, "Feil: " + str(ex), ed.Colors.Red)

    def on_plasser(self, sender, e):
        """Open Plasser Bygg dialog."""
        self._set_status(self.p_status, "Åpner...", ed.Colors.Orange)
        try:
            dlg = PlasserByggDialog()
            dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
            self._set_status(self.p_status, "Ferdig.", ed.Colors.Green)
        except Exception as ex:
            self._set_status(self.p_status, "Feil: " + str(ex), ed.Colors.Red)


# Launch the panel — stays open for the full Rhino session
panel = PluginPanel()
panel.Show()