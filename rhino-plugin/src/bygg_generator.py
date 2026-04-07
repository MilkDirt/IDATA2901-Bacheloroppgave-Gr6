# -*- coding: utf-8 -*-
import Rhino
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed
import math
import json


class ByggGeneratorDialog(ef.Dialog):

    def __init__(self):
        self.Title = "Bygg Generator"
        self.Padding = ed.Padding(10)
        self.Resizable = False

        desc_label = ef.Label()
        desc_label.Text = "Beskriv bygget:"

        self.desc_input = ef.TextBox()
        self.desc_input.Text = "moderne kontorbygg"
        self.desc_input.Width = 300

        floor_label = ef.Label()
        floor_label.Text = "Etasjehøyder (f.eks 0,7):"

        self.floor_input = ef.TextBox()
        self.floor_input.Text = "0,7"
        self.floor_input.Width = 300

        self.status_label = ef.Label()
        self.status_label.Text = "Velg bounding box, klikk Generer."
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

    def on_cancel(self, sender, e):
        self.Close()

    def on_generate(self, sender, e):
        self.status_label.Text = "Henter AI parametere..."
        self.status_label.TextColor = ed.Colors.Orange

        doc = Rhino.RhinoDoc.ActiveDoc
        selected = rs.GetObject("Velg bounding box", rs.filter.polysurface)

        if not selected:
            self.status_label.Text = "Ingen boks valgt!"
            self.status_label.TextColor = ed.Colors.Red
            return

        brep = rs.coercebrep(selected)
        if not brep:
            self.status_label.Text = "Ugyldig geometri!"
            self.status_label.TextColor = ed.Colors.Red
            return

        point_list = [v.Location for v in brep.Vertices]

        try:
            z_levels = sorted(set(
                float(h.strip()) for h in self.floor_input.Text.split(",")
            ))
        except:
            z_levels = [0.0, 7.0]

        description = self.desc_input.Text
        win_ratio = 0.4
        wall_t = 0.2

        try:
            import urllib.request as urllib_req
            total_height = z_levels[-1] - z_levels[0]
            url = "http://localhost:8000/generate-building"
            data = json.dumps({
                "description": description,
                "floors": len(z_levels) - 1,
                "height": total_height,
                "footprint_width": 10.0,
                "footprint_depth": 10.0
            }).encode("utf-8")
            req = urllib_req.Request(
                url, data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib_req.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                win_ratio = result["window_ratio"]
                wall_t = result["wall_thickness"]
        except Exception as ex:
            self.status_label.Text = "API feil - bruker standard verdier"
            self.status_label.TextColor = ed.Colors.Orange

        ground_pts = [p for p in point_list if round(p.Z, 2) == z_levels[0]]
        cx = sum(p.X for p in ground_pts) / len(ground_pts)
        cy = sum(p.Y for p in ground_pts) / len(ground_pts)
        sorted_pts = sorted(ground_pts, key=lambda p: math.atan2(p.Y - cy, p.X - cx))

        corner_pts = [rg.Point3d(p.X, p.Y, z_levels[0]) for p in sorted_pts]
        corner_pts.append(corner_pts[0])
        footprint = rg.PolylineCurve([rg.Point3d(p) for p in corner_pts])

        for i in range(len(z_levels) - 1):
            z_bottom = z_levels[i]
            z_top = z_levels[i + 1]
            floor_height = z_top - z_bottom

            polyline = footprint.ToPolyline()
            segments = polyline.GetSegments()

            for seg in segments:
                pt_a = rg.Point3d(seg.From.X, seg.From.Y, z_bottom)
                pt_b = rg.Point3d(seg.To.X, seg.To.Y, z_bottom)
                pt_c = rg.Point3d(seg.To.X, seg.To.Y, z_top)
                pt_d = rg.Point3d(seg.From.X, seg.From.Y, z_top)

                wall_srf = rg.NurbsSurface.CreateFromCorners(pt_a, pt_b, pt_c, pt_d)
                if wall_srf:
                    doc.Objects.AddSurface(wall_srf)

                seg_len = seg.Length
                if seg_len > 0:
                    panel_width = 3.0
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

        top_pts = [rg.Point3d(p.X, p.Y, z_levels[-1]) for p in sorted_pts]
        top_pts.append(top_pts[0])
        roof_curve = rg.PolylineCurve([rg.Point3d(p) for p in top_pts])
        roof_srfs = rg.Brep.CreatePlanarBreps(roof_curve, 0.01)
        if roof_srfs:
            for r in roof_srfs:
                doc.Objects.AddBrep(r)

        doc.Views.Redraw()
        self.status_label.Text = "Bygg generert!"
        self.status_label.TextColor = ed.Colors.Green


dialog = ByggGeneratorDialog()
dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)