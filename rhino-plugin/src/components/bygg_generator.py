# -*- coding: utf-8 -*-
"""
Generates walls, windows and a flat roof from a selected bounding box in Rhino.
Calls a local FastAPI backend for AI-decided window ratio and wall thickness.
"""
import Rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed
import math
import json


class ByggGeneratorDialog(ef.Dialog):
    """Main dialog for the building generator plugin."""

    def __init__(self):
        super(ByggGeneratorDialog, self).__init__()
        self.Title = "Bygg Generator"
        self.Padding = ed.Padding(10)
        self.Resizable = False
        self._build_ui()

    def _build_ui(self):
        desc_label = ef.Label()
        desc_label.Text = "Beskriv bygget:"
        self.desc_input = ef.TextBox()
        self.desc_input.Text = "moderne kontorbygg"
        self.desc_input.Width = 300

        floor_label = ef.Label()
        floor_label.Text = "Etasjer (eks: 2 eller 0;7;14):"
        self.floor_input = ef.TextBox()
        self.floor_input.Text = "1"
        self.floor_input.Width = 300

        self.status_label = ef.Label()
        self.status_label.Text = "Velg skjelett i Rhino, klikk Generer."
        self.status_label.TextColor = ed.Colors.Gray

        generate_btn = ef.Button()
        generate_btn.Text = "Generer Bygg"
        generate_btn.Click += self.on_generate

        cancel_btn = ef.Button()
        cancel_btn.Text = "Avbryt"
        cancel_btn.Click += self.on_cancel

        btn_row = ef.TableLayout()
        btn_row.Spacing = ed.Size(5, 0)
        btn_row.Rows.Add(ef.TableRow(
            ef.TableCell(cancel_btn),
            ef.TableCell(generate_btn)
        ))

        layout = ef.TableLayout()
        layout.Spacing = ed.Size(5, 8)
        layout.Rows.Add(ef.TableRow(ef.TableCell(desc_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.desc_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(floor_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.floor_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(btn_row)))
        self.Content = layout

    def _set_status(self, text, color):
        self.status_label.Text = text
        self.status_label.TextColor = color

    def _parse_floor_levels(self, floor_text, z_min, z_max, total_height):
        # If the input contains semicolons it's treated as explicit Z heights (e.g. "0;7;14").
        # Otherwise it's a floor count and we divide the total height evenly.
        if ";" in floor_text:
            try:
                return sorted(set(float(h.strip()) for h in floor_text.split(";")))
            except:
                return [z_min, z_max]
        else:
            try:
                num_floors = max(1, int(floor_text))
                floor_h = total_height / num_floors
                return [z_min + i * floor_h for i in range(num_floors + 1)]
            except:
                return [z_min, z_max]

    def _fetch_ai_parameters(self, description, num_floors, total_height, box_width, box_depth):
        # Sends building description + dimensions to the local FastAPI server.
        # If the server isn't running we just use sensible defaults so the UI doesn't break.
        try:
            import urllib.request as urllib_req
            url = "http://localhost:8000/generate-building"
            data = json.dumps({
                "description": description,
                "floors": num_floors,
                "height": total_height,
                "footprint_width": box_width,
                "footprint_depth": box_depth
            }).encode("utf-8")
            req = urllib_req.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib_req.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["window_ratio"], result["wall_thickness"]
        except:
            self._set_status("API feil - bruker standard verdier", ed.Colors.Orange)
            return 0.4, 0.2

    def _get_sorted_ground_corners(self, brep, z_min, z_level):
        # Filter vertices to only those sitting at Z = z_min (ground level).
        # Sort by angle around the centroid so adjacent corners are always next to each other —
        # without this, wall segments can be drawn in the wrong order and cross each other.
        point_list = [v.Location for v in brep.Vertices]
        ground_pts = [p for p in point_list if abs(p.Z - z_min) < 0.1]

        if not ground_pts:
            return None

        cx = sum(p.X for p in ground_pts) / len(ground_pts)
        cy = sum(p.Y for p in ground_pts) / len(ground_pts)
        sorted_pts = sorted(ground_pts, key=lambda p: math.atan2(p.Y - cy, p.X - cx))

        corner_pts = [rg.Point3d(p.X, p.Y, z_level) for p in sorted_pts]
        corner_pts.append(corner_pts[0])
        return corner_pts

    def _generate_floor(self, doc, segments, z_bottom, z_top, panel_width, win_ratio):
        for seg in segments:
            pt_a = rg.Point3d(seg.From.X, seg.From.Y, z_bottom)
            pt_b = rg.Point3d(seg.To.X, seg.To.Y, z_bottom)
            pt_c = rg.Point3d(seg.To.X, seg.To.Y, z_top)
            pt_d = rg.Point3d(seg.From.X, seg.From.Y, z_top)

            wall_srf = rg.NurbsSurface.CreateFromCorners(pt_a, pt_b, pt_c, pt_d)
            if wall_srf:
                doc.Objects.AddSurface(wall_srf)

            self._generate_windows(doc, pt_a, pt_b, seg.Length,
                                   z_top - z_bottom, panel_width, win_ratio, z_bottom)

    def _generate_windows(self, doc, pt_a, pt_b, seg_len, floor_height,
                          panel_width, win_ratio, z_bottom):
        # Divides the wall length into equal panels, then places a window in the middle of each.
        # win_ratio controls both the width and height of each window as a fraction of the panel.
        if seg_len <= 0:
            return

        num_panels = max(1, int(seg_len / panel_width))
        dx = (pt_b.X - pt_a.X) / seg_len
        dy = (pt_b.Y - pt_a.Y) / seg_len

        for p in range(num_panels):
            panel_start = seg_len * p / num_panels
            panel_end = seg_len * (p + 1) / num_panels
            panel_mid = (panel_start + panel_end) / 2
            panel_w = (panel_end - panel_start) * win_ratio * 0.8
            win_h = floor_height * win_ratio * 0.8
            mid_x = pt_a.X + dx * panel_mid
            mid_y = pt_a.Y + dy * panel_mid
            win_z_bottom = z_bottom + floor_height * 0.2
            win_z_top = win_z_bottom + win_h

            w_pt_a = rg.Point3d(mid_x - dx * panel_w/2, mid_y - dy * panel_w/2, win_z_bottom)
            w_pt_b = rg.Point3d(mid_x + dx * panel_w/2, mid_y + dy * panel_w/2, win_z_bottom)
            w_pt_c = rg.Point3d(mid_x + dx * panel_w/2, mid_y + dy * panel_w/2, win_z_top)
            w_pt_d = rg.Point3d(mid_x - dx * panel_w/2, mid_y - dy * panel_w/2, win_z_top)

            win_srf = rg.NurbsSurface.CreateFromCorners(w_pt_a, w_pt_b, w_pt_c, w_pt_d)
            if win_srf:
                doc.Objects.AddSurface(win_srf)

    def _generate_roof(self, doc, corner_pts, z_top):
        top_pts = [rg.Point3d(p.X, p.Y, z_top) for p in corner_pts[:-1]]
        top_pts.append(top_pts[0])
        roof_curve = rg.PolylineCurve([rg.Point3d(p) for p in top_pts])
        roof_srfs = rg.Brep.CreatePlanarBreps(roof_curve, 0.01)
        if roof_srfs:
            for r in roof_srfs:
                doc.Objects.AddBrep(r)

    def on_cancel(self, sender, e):
        self.Close()

    def on_generate(self, sender, e):
        self._set_status("Henter AI parametere...", ed.Colors.Orange)
        doc = Rhino.RhinoDoc.ActiveDoc

        # Check if the user already has something selected in Rhino before opening this dialog.
        # If not, prompt them to select now.
        selected_ids = rs.SelectedObjects()
        if not selected_ids:
            # Nothing preselected — ask user to select
            selected_ids = rs.GetObjects(
                "Velg skjelett objekter og trykk Enter",
                preselect=True)
        if not selected_ids:
            self._set_status("Ingen objekter valgt!", ed.Colors.Red)
            return

        # Walk all selected objects and union their bounding boxes into one combined box
        combined_bbox = rg.BoundingBox.Empty
        for obj_id in selected_ids:
            obj = doc.Objects.Find(obj_id)
            if obj is not None:
                combined_bbox = rg.BoundingBox.Union(
                    combined_bbox, obj.Geometry.GetBoundingBox(True))

        if not combined_bbox.IsValid:
            self._set_status("Feil: Kunne ikke beregne bounding box!", ed.Colors.Red)
            return

        z_min = round(combined_bbox.Min.Z, 3)
        z_max = round(combined_bbox.Max.Z, 3)
        total_height = z_max - z_min
        box_width = combined_bbox.Max.X - combined_bbox.Min.X
        box_depth = combined_bbox.Max.Y - combined_bbox.Min.Y

        z_levels = self._parse_floor_levels(
            self.floor_input.Text.strip(), z_min, z_max, total_height
        )
        num_floors = len(z_levels) - 1

        win_ratio, wall_t = self._fetch_ai_parameters(
            self.desc_input.Text, num_floors, total_height, box_width, box_depth
        )

        # Build a closed rectangular footprint from the bounding box min/max corners
        mn = combined_bbox.Min
        mx = combined_bbox.Max
        corner_pts = [
            rg.Point3d(mn.X, mn.Y, z_levels[0]),
            rg.Point3d(mx.X, mn.Y, z_levels[0]),
            rg.Point3d(mx.X, mx.Y, z_levels[0]),
            rg.Point3d(mn.X, mx.Y, z_levels[0]),
            rg.Point3d(mn.X, mn.Y, z_levels[0]),  # closed
        ]

        footprint = rg.PolylineCurve([rg.Point3d(p) for p in corner_pts])
        panel_width = max(3.0, min(box_width, box_depth) / 6)

        for i in range(len(z_levels) - 1):
            segments = footprint.ToPolyline().GetSegments()
            self._generate_floor(doc, segments, z_levels[i], z_levels[i + 1],
                                  panel_width, win_ratio)

        self._generate_roof(doc, corner_pts, z_levels[-1])

        doc.Views.Redraw()
        self._set_status(
            "Bygg generert! ({} etasje(r))".format(num_floors),
            ed.Colors.Green
        )


if __name__ == "__main__":
    dialog = ByggGeneratorDialog()
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)