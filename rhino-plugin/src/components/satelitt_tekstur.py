# -*- coding: utf-8 -*-
"""
Satellitt Tekstur — applies ESRI World Imagery to a terrain mesh.
Fetches image for the exact same UTM bbox the terrain was built from.
UV coordinates map mesh XY directly to image pixel fractions.

FIX: The terrain mesh is centered at origin by terreng_generator.py,
     so UV must be computed relative to the mesh's own bounding box,
     not assuming the mesh starts at (0, 0).
"""
import Rhino
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed
import System.IO as sio
import System.Drawing as sd
import math
import os

try:
    import urllib.request as _ul
except ImportError:
    import urllib2 as _ul


def _latlon_to_utm(lat, lon):
    if lat >= 56.0 and lat < 64.0 and lon >= 3.0 and lon < 12.0:
        zone = 32
    elif lon >= 21.0 and lat >= 68.0:
        zone = 35
    elif lat >= 65.0:
        zone = 33
    else:
        zone = 33
    epsg = 25800 + zone
    a = 6378137.0; f = 1.0/298.257223563; b = a*(1-f); e2 = 1-(b/a)**2
    lat_r = math.radians(lat); lon_r = math.radians(lon)
    lon0  = math.radians((zone-1)*6 - 180 + 3)
    N  = a/math.sqrt(1-e2*math.sin(lat_r)**2)
    T  = math.tan(lat_r)**2; C = e2/(1-e2)*math.cos(lat_r)**2
    A_ = math.cos(lat_r)*(lon_r-lon0)
    M  = a*((1-e2/4-3*e2**2/64-5*e2**3/256)*lat_r
            -(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*lat_r)
            +(15*e2**2/256+45*e2**3/1024)*math.sin(4*lat_r)
            -(35*e2**3/3072)*math.sin(6*lat_r))
    k0 = 0.9996
    e = k0*N*(A_+(1-T+C)*A_**3/6+(5-18*T+T**2+72*C-58*(e2/(1-e2)))*A_**5/120)+500000.0
    n = k0*(M+N*math.tan(lat_r)*(A_**2/2+(5-T+9*C+4*C**2)*A_**4/24
            +(61-58*T+T**2+600*C-330*(e2/(1-e2)))*A_**6/720))
    return e, n, epsg, zone


def _utm_to_latlon(ost, nord, epsg):
    zone = epsg - 25800
    k0 = 0.9996; a = 6378137.0; e2 = 0.00669438
    x = ost - 500000.0; y = nord
    M = y/k0
    mu = M/(a*(1-e2/4-3*e2**2/64-5*e2**3/256))
    e1 = (1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
    fp = (mu + (3*e1/2)*math.sin(2*mu)
             + (21*e1**2/16)*math.sin(4*mu)
             + (151*e1**3/96)*math.sin(6*mu))
    e_p2=e2/(1-e2); C1=e_p2*math.cos(fp)**2; T1=math.tan(fp)**2
    R1=a*(1-e2)/(1-e2*math.sin(fp)**2)**1.5
    N1=a/math.sqrt(1-e2*math.sin(fp)**2)
    D=x/(N1*k0)
    lat=fp-(N1*math.tan(fp)/R1)*(D**2/2-(5+3*T1+10*C1-4*C1**2-9*e_p2)*D**4/24)
    lon_r=(D-(1+2*T1+C1)*D**3/6)/math.cos(fp)
    return math.degrees(lat), math.degrees(lon_r)+(zone-1)*6-180+3


def _fetch_esri(ost, nord, requested_size, epsg):
    """
    Fetch ESRI for the full Kartverket fetch area (max(size,1500)m).
    Returns (image_bytes, fetch_size_m) so UV can be scaled correctly.
    """
    fetch_m = max(float(requested_size), 1500.0)

    lat_sw, lon_sw = _utm_to_latlon(ost - fetch_m/2,  nord - fetch_m/2, epsg)
    lat_ne, lon_ne = _utm_to_latlon(ost + fetch_m/2,  nord + fetch_m/2, epsg)

    url = (
        "https://server.arcgisonline.com/arcgis/rest/services/"
        "World_Imagery/MapServer/export?"
        "bbox={lon_sw},{lat_sw},{lon_ne},{lat_ne}"
        "&bboxSR=4326&imageSR=4326"
        "&size=2048,2048&format=jpg&f=image"
    ).format(lat_sw=lat_sw, lon_sw=lon_sw, lat_ne=lat_ne, lon_ne=lon_ne)

    print("ESRI fetch: {:.0f}m bbox (centered on UTM {:.0f}, {:.0f})".format(fetch_m, ost, nord))
    print("ESRI bbox: lon {:.5f}..{:.5f}  lat {:.5f}..{:.5f}".format(
        lon_sw, lon_ne, lat_sw, lat_ne))

    req  = _ul.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = _ul.urlopen(req, timeout=30).read()
    if data[:2] != b'\xff\xd8':
        raise Exception("Fikk ikke JPEG: " + repr(data[:80]))
    return data, fetch_m


class SatellittTeksturDialog(ef.Dialog):

    def __init__(self, lat=62.4722, lon=6.1495, size=1000, nord=None, ost=None):
        super(SatellittTeksturDialog, self).__init__()
        self.Title     = "Satellitt Tekstur"
        self.Padding   = ed.Padding(12)
        self.Resizable = False
        self._lat  = float(lat)
        self._lon  = float(lon)
        self._size = float(size)
        self._ost, self._nord, self._epsg, self._zone = _latlon_to_utm(lat, lon)
        self._build_ui()

    def _build_ui(self):
        info = ef.Label()
        info.Text = "lat={:.4f}, lon={:.4f}, {}m  (sone {})".format(
            self._lat, self._lon, int(self._size), self._zone)
        info.TextColor = ed.Colors.DarkGray

        self.status = ef.Label()
        self.status.Text      = "Klar — velg terreng-mesh og klikk Hent."
        self.status.TextColor = ed.Colors.Gray
        self.status.Width     = 340

        hent_btn = ef.Button()
        hent_btn.Text   = "Hent Flyfoto (ESRI)"
        hent_btn.Width  = 340
        hent_btn.Click += self.on_hent

        avbryt_btn = ef.Button()
        avbryt_btn.Text   = "Avbryt"
        avbryt_btn.Click += lambda s, e: self.Close()

        btn_row = ef.TableLayout()
        btn_row.Spacing = ed.Size(5, 0)
        btn_row.Rows.Add(ef.TableRow(
            ef.TableCell(avbryt_btn), ef.TableCell(hent_btn)))

        layout = ef.TableLayout()
        layout.Spacing = ed.Size(5, 8)
        layout.Rows.Add(ef.TableRow(ef.TableCell(info)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(btn_row)))
        self.Content = layout

    def _set_status(self, text, color):
        self.status.Text      = text
        self.status.TextColor = color

    def _apply_uv(self, mesh, fetch_size):
        """
        Map mesh vertices to UV coordinates in the ESRI image.

        The terrain mesh is CENTERED at the origin (terreng_generator translates
        it by -bbox.Center before adding to Rhino). So the mesh spans roughly
        [-fetch_size/2 .. +fetch_size/2] in both X and Y.

        UV mapping:
          U = (vertex.X + fetch_size/2) / fetch_size   →  0.0 (west) to 1.0 (east)
          V = (vertex.Y + fetch_size/2) / fetch_size   →  0.0 (south) to 1.0 (north)

        This correctly aligns the ESRI image (which also covers the same centered
        fetch_size × fetch_size area) with the mesh geometry.
        """
        half = fetch_size / 2.0
        tc = mesh.TextureCoordinates
        tc.Clear()
        for vi in range(mesh.Vertices.Count):
            v = mesh.Vertices[vi]
            u  = (v.X + half) / fetch_size
            vv = (v.Y + half) / fetch_size
            tc.Add(u, vv)

    def _apply_material(self, doc, obj_id, mesh, tex_path):
        mat = Rhino.DocObjects.Material()
        mat.Name = "Flyfoto_ESRI"
        mat.SetBitmapTexture(tex_path)
        mat.CommitChanges()
        idx   = doc.Materials.Add(mat)
        obj   = doc.Objects.Find(obj_id)
        attrs = obj.Attributes
        attrs.MaterialIndex  = idx
        attrs.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
        mesh.VertexColors.Clear()
        doc.Objects.Replace(obj_id, mesh)
        doc.Objects.ModifyAttributes(obj_id, attrs, True)

    def on_hent(self, sender, e):
        doc = Rhino.RhinoDoc.ActiveDoc

        self._set_status("Velg terreng-mesh i Rhino...", ed.Colors.Orange)
        obj_id = rs.GetObject("Velg terreng-mesh", rs.filter.mesh)
        if not obj_id:
            self._set_status("Ingen mesh valgt.", ed.Colors.Red)
            return
        mesh = rs.coercemesh(obj_id)
        if not mesh:
            self._set_status("Ugyldig mesh.", ed.Colors.Red)
            return

        self._set_status("Laster ned fra ESRI...", ed.Colors.Orange)
        try:
            img_data, fetch_size = _fetch_esri(
                self._ost, self._nord, self._size, self._epsg)
            print("Downloaded {} KB, fetch_size={}m".format(
                len(img_data)//1024, fetch_size))
        except Exception as ex:
            self._set_status("Nedlasting feilet: " + str(ex), ed.Colors.Red)
            return

        cache_dir = os.path.join(os.path.expanduser("~"), "rhino_terrain_cache")
        try:
            os.makedirs(cache_dir)
        except Exception:
            pass
        tmp = os.path.join(cache_dir,
            "flyfoto_{:.0f}_{:.0f}_{:.0f}.jpg".format(
                self._ost, self._nord, self._size))
        try:
            with open(tmp, 'wb') as f:
                f.write(img_data)
        except Exception as ex:
            self._set_status("Kunne ikke lagre: " + str(ex), ed.Colors.Red)
            return

        self._set_status("Påfører tekstur...", ed.Colors.Orange)
        try:
            self._apply_uv(mesh, fetch_size)
            self._apply_material(doc, obj_id, mesh, tmp)
            doc.Views.Redraw()
            self._set_status(
                "Ferdig! Bytt til Rendered view for å se flyfotoet.", ed.Colors.Green)
        except Exception as ex:
            self._set_status("Tekstur-feil: " + str(ex), ed.Colors.Red)


if __name__ == "__main__":
    dlg = SatellittTeksturDialog(lat=62.4722, lon=6.1495, size=1000)
    dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)