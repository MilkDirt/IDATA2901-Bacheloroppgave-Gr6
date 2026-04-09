# -*- coding: utf-8 -*-
"""
Plasser Bygg på Terreng — Rhino plugin for placing a generated building on a terrain mesh.
Flattens the terrain under the building footprint and moves the building to match.
Uses a smooth blend zone around the footprint to avoid sharp terrain edges.
"""
import Rhino
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed


class PlasserByggDialog(ef.Dialog):
    """Main dialog for placing a building onto a terrain mesh."""

    def __init__(self):
        self.Title = "Plasser Bygg på Terreng"
        self.Padding = ed.Padding(10)
        self.Resizable = False
        self._build_ui()

    def _build_ui(self):
        """Build and arrange all UI elements in the dialog."""
        info_label = ef.Label()
        info_label.Text = "Velg terreng-mesh, deretter bygget."

        self.status_label = ef.Label()
        self.status_label.Text = "Klar."
        self.status_label.TextColor = ed.Colors.Gray

        plasser_btn = ef.Button()
        plasser_btn.Text = "Plasser Bygg på Terreng"
        plasser_btn.Click += self.on_plasser

        avbryt_btn = ef.Button()
        avbryt_btn.Text = "Avbryt"
        avbryt_btn.Click += self.on_avbryt

        btn_row = ef.TableLayout()
        btn_row.Spacing = ed.Size(5, 0)
        btn_row.Rows.Add(ef.TableRow(
            ef.TableCell(avbryt_btn),
            ef.TableCell(plasser_btn)
        ))

        layout = ef.TableLayout()
        layout.Spacing = ed.Size(5, 8)
        layout.Rows.Add(ef.TableRow(ef.TableCell(info_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(btn_row)))
        self.Content = layout

    def _set_status(self, text, color):
        """Update the status label with a message and color."""
        self.status_label.Text = text
        self.status_label.TextColor = color

    def _get_building_bounds(self, doc, building_ids):
        """
        Calculate the combined XY bounding box and minimum Z of all building objects.
        Returns (x_min, x_max, y_min, y_max, z_min) or None if no valid geometry found.
        """
        all_min_x, all_min_y, all_max_x, all_max_y = [], [], [], []
        building_z_min = float('inf')

        for bid in building_ids:
            obj = doc.Objects.Find(bid)
            if obj is None:
                continue
            bbox = obj.Geometry.GetBoundingBox(True)
            all_min_x.append(bbox.Min.X)
            all_min_y.append(bbox.Min.Y)
            all_max_x.append(bbox.Max.X)
            all_max_y.append(bbox.Max.Y)
            if bbox.Min.Z < building_z_min:
                building_z_min = bbox.Min.Z

        if not all_min_x:
            return None

        return (min(all_min_x), max(all_max_x),
                min(all_min_y), max(all_max_y),
                building_z_min)

    def _sample_terrain_heights(self, terrain_mesh, x_min, x_max, y_min, y_max, samples=10):
        """
        Cast rays downward from a grid of points within the given XY bounds
        and collect the terrain Z values at each hit point.
        Returns a list of Z values, or an empty list if no hits.
        """
        z_values = []
        for i in range(samples + 1):
            for j in range(samples + 1):
                sx = x_min + (x_max - x_min) * i / samples
                sy = y_min + (y_max - y_min) * j / samples
                ray = rg.Ray3d(rg.Point3d(sx, sy, 10000), rg.Vector3d(0, 0, -1))
                t = rg.Intersect.Intersection.MeshRay(terrain_mesh, ray)
                if t >= 0:
                    z_values.append(10000 + (-1) * t)
        return z_values

    def _calculate_flat_z(self, terrain_z_values):
        """
        Calculate the target Z level to flatten the terrain to under the building.
        Uses average height slightly shifted toward the minimum for a natural grounded look,
        so the building appears embedded in the terrain rather than sitting on a pedestal.
        """
        avg_z = sum(terrain_z_values) / len(terrain_z_values)
        min_z = min(terrain_z_values)
        return avg_z - (avg_z - min_z) * 0.3

    def _flatten_terrain(self, terrain_mesh, x_min, x_max, y_min, y_max,
                         flat_z, blend_distance=8.0):
        """
        Modify terrain mesh vertices to create a flat building pad.
        Vertices inside the footprint are snapped to flat_z.
        Vertices within blend_distance outside the footprint are smoothly interpolated
        back to their original height, avoiding sharp terrain edges.
        """
        vertices = terrain_mesh.Vertices

        for vi in range(vertices.Count):
            v = vertices[vi]
            vx, vy, vz = v.X, v.Y, v.Z

            if x_min <= vx <= x_max and y_min <= vy <= y_max:
                vertices[vi] = rg.Point3f(vx, vy, float(flat_z))
            else:
                dx = max(x_min - vx, 0, vx - x_max)
                dy = max(y_min - vy, 0, vy - y_max)
                dist = (dx ** 2 + dy ** 2) ** 0.5

                if dist < blend_distance:
                    t = dist / blend_distance
                    blend = 1.0 - (1.0 - t) ** 2
                    new_z = flat_z + (vz - flat_z) * blend
                    vertices[vi] = rg.Point3f(vx, vy, float(new_z))

        terrain_mesh.Normals.ComputeNormals()
        terrain_mesh.UnifyNormals()

    def _move_building_to_z(self, doc, building_ids, current_z_min, target_z):
        """Translate all building objects vertically so the base aligns with target_z."""
        xform = rg.Transform.Translation(rg.Vector3d(0, 0, target_z - current_z_min))
        for bid in building_ids:
            obj = doc.Objects.Find(bid)
            if obj is not None:
                doc.Objects.Transform(bid, xform, True)

    def on_avbryt(self, sender, e):
        self.Close()

    def on_plasser(self, sender, e):
        """Main handler — selects terrain and building, flattens terrain, places building."""
        doc = Rhino.RhinoDoc.ActiveDoc

        self._set_status("Velg terreng-mesh...", ed.Colors.Orange)
        terrain_id = rs.GetObject("Velg terreng-mesh", rs.filter.mesh)
        if not terrain_id:
            self._set_status("Ingen terreng valgt!", ed.Colors.Red)
            return

        terrain_mesh = rs.coercemesh(terrain_id)
        if not terrain_mesh:
            self._set_status("Ugyldig terreng-mesh!", ed.Colors.Red)
            return

        self._set_status("Velg bygget (alle flater)...", ed.Colors.Orange)
        building_ids = rs.GetObjects("Velg alle bygningsobjekter", preselect=False)
        if not building_ids:
            self._set_status("Ingen bygning valgt!", ed.Colors.Red)
            return

        bounds = self._get_building_bounds(doc, building_ids)
        if not bounds:
            self._set_status("Feil: Kunne ikke lese bygningsgeometri!", ed.Colors.Red)
            return

        x_min, x_max, y_min, y_max, building_z_min = bounds

        terrain_z_values = self._sample_terrain_heights(terrain_mesh, x_min, x_max, y_min, y_max)
        if not terrain_z_values:
            self._set_status(
                "Feil: Ingen treff på terreng! Flytt bygget over terrenget og prøv igjen.",
                ed.Colors.Red
            )
            return

        flat_z = self._calculate_flat_z(terrain_z_values)

        self._flatten_terrain(terrain_mesh, x_min, x_max, y_min, y_max, flat_z)
        doc.Objects.Replace(terrain_id, terrain_mesh)

        self._move_building_to_z(doc, building_ids, building_z_min, flat_z)

        doc.Views.Redraw()
        self._set_status(
            "Ferdig! Bygg plassert på Z={0}m, terreng tilpasset.".format(round(flat_z, 2)),
            ed.Colors.Green
        )


dialog = PlasserByggDialog()
dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)