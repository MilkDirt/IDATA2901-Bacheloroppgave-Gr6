# -*- coding: utf-8 -*-
import Rhino
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed


class PlasserByggDialog(ef.Form):

    def __init__(self):
        super(PlasserByggDialog, self).__init__()
        self.Title     = "Plasser Bygg"
        self.Padding   = ed.Padding(10)
        self.Resizable = False
        self.Owner     = Rhino.UI.RhinoEtoApp.MainWindow  # always on top of Rhino
        self._terrain_id   = None
        self._building_ids = None
        self._build_ui()

    def _build_ui(self):
        layout = ef.TableLayout()
        layout.Spacing = ed.Size(4, 6)

        # Status badges
        self._t_lbl = self._lbl("Terreng:  -")
        self._b_lbl = self._lbl("Bygg:     -")
        box = ef.GroupBox(); box.Text = "Valgt"; box.Width = 260
        inn = ef.TableLayout(); inn.Padding = ed.Padding(6); inn.Spacing = ed.Size(0, 2)
        inn.Rows.Add(ef.TableRow(ef.TableCell(self._t_lbl)))
        inn.Rows.Add(ef.TableRow(ef.TableCell(self._b_lbl)))
        box.Content = inn
        layout.Rows.Add(ef.TableRow(ef.TableCell(box)))

        layout.Rows.Add(ef.TableRow(ef.TableCell(self._btn("1. Velg terreng", self.on_velg_terreng))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._btn("2. Velg bygg", self.on_velg_bygg))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._gap(2))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._btn("Flytt bygg", self.on_flytt, ed.Colors.DarkBlue))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._btn("Plasser pa terreng", self.on_plasser, ed.Colors.DarkGreen))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._gap(2))))

        self.status_label = ef.Label()
        self.status_label.Text = "Velg terreng og bygg."
        self.status_label.TextColor = ed.Colors.Gray
        self.status_label.Width = 260
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status_label)))

        rb = ef.Button(); rb.Text = "Nullstill"; rb.Width = 100; rb.Click += self.on_reset
        cb = ef.Button(); cb.Text = "Lukk";      cb.Width = 100; cb.Click += lambda s, e: self.Close()
        br = ef.TableLayout(); br.Spacing = ed.Size(6, 0)
        br.Rows.Add(ef.TableRow(ef.TableCell(rb, False), ef.TableCell(cb, False), ef.TableCell(ef.Label())))
        layout.Rows.Add(ef.TableRow(ef.TableCell(br)))
        self.Content = layout

    def _lbl(self, t):
        l = ef.Label(); l.Text = t; l.TextColor = ed.Colors.Gray; l.Width = 240; return l

    def _btn(self, t, h, c=None):
        b = ef.Button(); b.Text = t; b.Width = 260
        if c: b.TextColor = c
        b.Click += h; return b

    def _gap(self, h=4):
        l = ef.Label(); l.Height = h; return l

    def _set_status(self, text, color=None):
        self.status_label.Text = text
        self.status_label.TextColor = color or ed.Colors.Gray

    def _refresh(self):
        doc = Rhino.RhinoDoc.ActiveDoc
        if self._terrain_id and doc.Objects.Find(self._terrain_id):
            self._t_lbl.Text = "Terreng:  OK"; self._t_lbl.TextColor = ed.Colors.Green
        else:
            self._t_lbl.Text = "Terreng:  -"; self._t_lbl.TextColor = ed.Colors.Gray
        if self._building_ids:
            self._b_lbl.Text = "Bygg:     OK ({})".format(len(self._building_ids))
            self._b_lbl.TextColor = ed.Colors.Green
        else:
            self._b_lbl.Text = "Bygg:     -"; self._b_lbl.TextColor = ed.Colors.Gray

    def on_velg_terreng(self, sender, e):
        self._set_status("Klikk pa terreng...", ed.Colors.Orange)
        tid = rs.GetObject("Velg terreng-mesh", rs.filter.mesh)
        if not tid or not rs.coercemesh(tid):
            self._set_status("Ingen terreng valgt.", ed.Colors.Red); return
        self._terrain_id = tid
        self._refresh()
        self._set_status("Terreng OK.", ed.Colors.Green)

    def on_velg_bygg(self, sender, e):
        if not self._terrain_id:
            self._set_status("Velg terreng forst!", ed.Colors.Red); return
        doc = Rhino.RhinoDoc.ActiveDoc
        rs.HideObject(self._terrain_id); doc.Views.Redraw()
        ids = rs.GetObjects("Velg bygg, trykk Enter", preselect=False)
        rs.ShowObject(self._terrain_id); doc.Views.Redraw()
        if not ids:
            self._set_status("Ingen bygg valgt.", ed.Colors.Red); return
        self._building_ids = list(ids)
        self._refresh()
        self._set_status("{} obj husket.".format(len(ids)), ed.Colors.Green)

    def on_reset(self, sender, e):
        self._terrain_id = None; self._building_ids = None
        self._refresh(); self._set_status("Nullstilt.", ed.Colors.Gray)

    def on_flytt(self, sender, e):
        if not self._building_ids:
            self._set_status("Velg bygg forst!", ed.Colors.Red); return
        rs.UnselectAllObjects()
        rs.SelectObjects(self._building_ids)
        self._set_status("Markert. Bruk Move / Gumball.", ed.Colors.Green)

    def on_plasser(self, sender, e):
        if not self._terrain_id or not self._building_ids:
            self._set_status("Velg terreng og bygg forst!", ed.Colors.Red); return
        doc = Rhino.RhinoDoc.ActiveDoc
        terrain_mesh = rs.coercemesh(self._terrain_id)
        if not terrain_mesh:
            self._set_status("Terreng ikke funnet!", ed.Colors.Red); return

        self._set_status("Jobber...", ed.Colors.Orange)

        xs0, xs1, ys0, ys1, zmin = [], [], [], [], float('inf')
        for bid in self._building_ids:
            obj = doc.Objects.Find(bid)
            if obj is None: continue
            bb = obj.Geometry.GetBoundingBox(True)
            xs0.append(bb.Min.X); xs1.append(bb.Max.X)
            ys0.append(bb.Min.Y); ys1.append(bb.Max.Y)
            if bb.Min.Z < zmin: zmin = bb.Min.Z
        if not xs0:
            self._set_status("Feil: ingen geometri.", ed.Colors.Red); return

        x0, x1, y0, y1 = min(xs0), max(xs1), min(ys0), max(ys1)

        zv = []
        for i in range(9):
            for j in range(9):
                x = x0 + (x1-x0)*i/8.0; y = y0 + (y1-y0)*j/8.0
                ray = rg.Ray3d(rg.Point3d(x, y, 99999), rg.Vector3d(0,0,-1))
                t = rg.Intersect.Intersection.MeshRay(terrain_mesh, ray)
                if t >= 0: zv.append(99999 - t)
        if not zv:
            self._set_status("Ingen terreng-treff!", ed.Colors.Red); return

        avg = sum(zv)/len(zv)
        fz  = avg - (avg - min(zv)) * 0.3

        blend = 8.0
        cx0=x0-blend; cx1=x1+blend; cy0=y0-blend; cy1=y1+blend
        verts = terrain_mesh.Vertices
        for vi in range(verts.Count):
            v=verts[vi]; vx,vy,vz = v.X,v.Y,v.Z
            if vx<cx0 or vx>cx1 or vy<cy0 or vy>cy1: continue
            if x0<=vx<=x1 and y0<=vy<=y1:
                verts[vi] = rg.Point3f(vx, vy, float(fz))
            else:
                dx=max(x0-vx,0.0,vx-x1); dy=max(y0-vy,0.0,vy-y1)
                d=(dx*dx+dy*dy)**0.5
                if d < blend:
                    t=d/blend; bv=1.0-(1.0-t)**2
                    verts[vi] = rg.Point3f(vx, vy, float(fz+(vz-fz)*bv))

        terrain_mesh.Normals.ComputeNormals()
        terrain_mesh.UnifyNormals()
        if terrain_mesh.VertexColors.Count > 0:
            import System.Drawing as sd
            all_z=[terrain_mesh.Vertices[vi].Z for vi in range(terrain_mesh.Vertices.Count)]
            z_lo=min(all_z); z_rng=max(max(all_z)-z_lo, 0.1)
            for vi in range(terrain_mesh.Vertices.Count):
                t=(terrain_mesh.Vertices[vi].Z-z_lo)/z_rng
                if t<0.5: tt=t/0.5; r,g,b=int(tt*210),int(150+tt*85),int(60-tt*60)
                else: tt=(t-0.5)/0.5; r,g,b=int(210+tt*45),int(235-tt*200),int(tt*220)
                terrain_mesh.VertexColors[vi]=sd.Color.FromArgb(max(0,min(255,r)),max(0,min(255,g)),max(0,min(255,b)))

        doc.Objects.Replace(self._terrain_id, terrain_mesh)

        xform = rg.Transform.Translation(rg.Vector3d(0, 0, fz - zmin))
        for bid in self._building_ids:
            obj = doc.Objects.Find(bid)
            if obj is not None: doc.Objects.Transform(bid, xform, True)

        doc.Views.Redraw()
        self._set_status("Ferdig! Z = {:.1f}m".format(fz), ed.Colors.Green)


if __name__ == "__main__":
    dialog = PlasserByggDialog()
    dialog.Show()