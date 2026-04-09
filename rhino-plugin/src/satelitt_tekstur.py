# -*- coding: utf-8 -*-
"""
Satellitt Tekstur — Rhino plugin for applying real satellite imagery to a terrain mesh.
Fetches free aerial tiles from ESRI World Imagery using the same UTM coordinates
as the terrain, stitches them into a single texture, and applies it via UV mapping.
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


# ---------------------------------------------------------------------------
# Coordinate conversion utilities
# ---------------------------------------------------------------------------

def utm_to_latlon(easting, northing, zone=33):
    """
    Convert UTM zone 33N (EPSG:25833) coordinates to WGS84 lat/lon degrees.
    Uses the standard Transverse Mercator inverse projection formula.
    """
    k0 = 0.9996
    a = 6378137.0
    e = 0.081819191
    e2 = e * e
    e_p2 = e2 / (1 - e2)

    x = easting - 500000.0
    y = northing

    M = y / k0
    mu = M / (a * (1 - e2/4 - 3*e2*e2/64 - 5*e2*e2*e2/256))

    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    J1 = 3*e1/2 - 27*e1**3/32
    J2 = 21*e1**2/16 - 55*e1**4/32
    J3 = 151*e1**3/96
    J4 = 1097*e1**4/512

    fp = mu + J1*math.sin(2*mu) + J2*math.sin(4*mu) + J3*math.sin(6*mu) + J4*math.sin(8*mu)

    C1 = e_p2 * math.cos(fp)**2
    T1 = math.tan(fp)**2
    R1 = a * (1 - e2) / (1 - e2*math.sin(fp)**2)**1.5
    N1 = a / math.sqrt(1 - e2*math.sin(fp)**2)
    D = x / (N1 * k0)

    lat = fp - (N1*math.tan(fp)/R1) * (
        D**2/2 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e_p2)*D**4/24 +
        (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*e_p2 - 3*C1**2)*D**6/720
    )
    lon = (D - (1 + 2*T1 + C1)*D**3/6 +
           (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*e_p2 + 24*T1**2)*D**5/120) / math.cos(fp)

    return math.degrees(lat), math.degrees(lon) + (zone - 1) * 6 - 180 + 3


def latlon_to_tile(lat, lon, zoom):
    """Convert WGS84 lat/lon to XYZ slippy map tile coordinates at a given zoom level."""
    lat_r = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_r) + 1.0/math.cos(lat_r)) / math.pi) / 2.0 * n)
    return x, y


# ---------------------------------------------------------------------------
# Tile fetching and stitching
# ---------------------------------------------------------------------------

def fetch_tile(tx, ty, zoom):
    """
    Download a single 256x256 PNG tile from ESRI World Imagery.
    ESRI tiles are free and require no authentication.
    """
    try:
        import urllib.request as urllib_req
    except ImportError:
        import urllib2 as urllib_req

    url = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{}/{}/{}".format(zoom, ty, tx)
    )
    print("Fetching tile:", url)
    req = urllib_req.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib_req.urlopen(req, timeout=15).read()


def stitch_tiles(tiles_data, tile_grid, tile_size=256):
    """
    Combine a grid of downloaded tiles into a single stitched bitmap.
    tile_grid is a 2D list of (tx, ty, zoom) tuples defining the layout.
    """
    cols = len(tile_grid[0])
    rows = len(tile_grid)
    result = sd.Bitmap(cols * tile_size, rows * tile_size)
    g = sd.Graphics.FromImage(result)

    for row_idx, row in enumerate(tile_grid):
        for col_idx, (tx, ty, zoom) in enumerate(row):
            tile_bytes = tiles_data.get((tx, ty, zoom))
            if tile_bytes:
                import System
                arr = System.Array[System.Byte](bytearray(tile_bytes))
                tile_bmp = sd.Bitmap(sio.MemoryStream(arr))
                g.DrawImage(tile_bmp, col_idx * tile_size, row_idx * tile_size)

    g.Dispose()
    return result


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class SatellittTeksturDialog(ef.Dialog):
    """Main dialog for applying satellite imagery to a terrain mesh."""

    def __init__(self):
        self.Title = "Satellitt Tekstur"
        self.Padding = ed.Padding(10)
        self.Resizable = False
        self._build_ui()

    def _build_ui(self):
        """Build and arrange all UI elements in the dialog."""
        info_label = ef.Label()
        info_label.Text = "Samme UTM koordinater som terrenget:"

        nord_label = ef.Label()
        nord_label.Text = "Nord UTM:"
        self.nord_input = ef.TextBox()
        self.nord_input.Text = "6790000"
        self.nord_input.Width = 300

        ost_label = ef.Label()
        ost_label.Text = "Øst UTM:"
        self.ost_input = ef.TextBox()
        self.ost_input.Text = "394000"
        self.ost_input.Width = 300

        size_label = ef.Label()
        size_label.Text = "Størrelse i meter:"
        self.size_input = ef.TextBox()
        self.size_input.Text = "500"
        self.size_input.Width = 300

        self.status_label = ef.Label()
        self.status_label.Text = "Klar."
        self.status_label.TextColor = ed.Colors.Gray

        hent_btn = ef.Button()
        hent_btn.Text = "Hent Satellitt Tekstur"
        hent_btn.Click += self.on_hent

        avbryt_btn = ef.Button()
        avbryt_btn.Text = "Avbryt"
        avbryt_btn.Click += self.on_avbryt

        btn_row = ef.TableLayout()
        btn_row.Spacing = ed.Size(5, 0)
        btn_row.Rows.Add(ef.TableRow(
            ef.TableCell(avbryt_btn),
            ef.TableCell(hent_btn)
        ))

        layout = ef.TableLayout()
        layout.Spacing = ed.Size(5, 8)
        layout.Rows.Add(ef.TableRow(ef.TableCell(info_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(nord_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.nord_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(ost_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.ost_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(size_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.size_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(btn_row)))
        self.Content = layout

    def _set_status(self, text, color):
        """Update the status label with a message and color."""
        self.status_label.Text = text
        self.status_label.TextColor = color

    def _get_zoom_level(self, size):
        """
        Select an appropriate tile zoom level based on the terrain area size.
        Smaller areas use higher zoom for more detail.
        """
        if size <= 500:
            return 16
        elif size <= 2000:
            return 15
        return 14

    def _get_tile_grid(self, ost, nord, size, zoom):
        """
        Calculate which tiles cover the terrain bbox and return a 2D grid of tile coords.
        Converts UTM corners to lat/lon, then to tile coordinates.
        """
        lat_sw, lon_sw = utm_to_latlon(ost, nord, zone=33)
        lat_ne, lon_ne = utm_to_latlon(ost + size, nord + size, zone=33)

        tx_sw, ty_ne = latlon_to_tile(lat_sw, lon_sw, zoom)
        tx_ne, ty_sw = latlon_to_tile(lat_ne, lon_ne, zoom)

        tx_min, tx_max = min(tx_sw, tx_ne), max(tx_sw, tx_ne)
        ty_min, ty_max = min(ty_sw, ty_ne), max(ty_sw, ty_ne)

        print("Tile range X:{}-{} Y:{}-{} Zoom:{}".format(tx_min, tx_max, ty_min, ty_max, zoom))

        return [
            [(tx, ty, zoom) for tx in range(tx_min, tx_max + 1)]
            for ty in range(ty_min, ty_max + 1)
        ]

    def _apply_uv_coordinates(self, terrain_mesh):
        """
        Map each mesh vertex to a UV coordinate in [0,1] range based on its XY position.
        This aligns the stitched satellite image correctly onto the terrain surface.
        """
        bbox = terrain_mesh.GetBoundingBox(True)
        x_range = max(bbox.Max.X - bbox.Min.X, 0.001)
        y_range = max(bbox.Max.Y - bbox.Min.Y, 0.001)

        tc = terrain_mesh.TextureCoordinates
        tc.Clear()
        for vi in range(terrain_mesh.Vertices.Count):
            v = terrain_mesh.Vertices[vi]
            tc.Add(
                (v.X - bbox.Min.X) / x_range,
                (v.Y - bbox.Min.Y) / y_range
            )

    def _apply_material(self, doc, terrain_id, terrain_mesh, texture_path):
        """
        Create a Rhino material with the satellite texture and apply it to the terrain object.
        Clears any existing vertex colors so the texture renders correctly.
        """
        mat = Rhino.DocObjects.Material()
        mat.Name = "Satelitt_ESRI"
        mat.SetBitmapTexture(texture_path)
        mat.CommitChanges()
        mat_index = doc.Materials.Add(mat)

        obj = doc.Objects.Find(terrain_id)
        obj_attrs = obj.Attributes
        obj_attrs.MaterialIndex = mat_index
        obj_attrs.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject

        terrain_mesh.VertexColors.Clear()
        doc.Objects.Replace(terrain_id, terrain_mesh)
        doc.Objects.ModifyAttributes(terrain_id, obj_attrs, True)

    def on_avbryt(self, sender, e):
        self.Close()

    def on_hent(self, sender, e):
        """Main handler — fetches satellite tiles, stitches image, applies as mesh texture."""
        doc = Rhino.RhinoDoc.ActiveDoc

        try:
            nord = float(self.nord_input.Text.strip())
            ost = float(self.ost_input.Text.strip())
            size = float(self.size_input.Text.strip())
        except:
            self._set_status("Feil: Ugyldig koordinater!", ed.Colors.Red)
            return

        self._set_status("Velg terreng-mesh...", ed.Colors.Orange)
        terrain_id = rs.GetObject("Velg terreng-mesh", rs.filter.mesh)
        if not terrain_id:
            self._set_status("Ingen terreng valgt!", ed.Colors.Red)
            return

        terrain_mesh = rs.coercemesh(terrain_id)
        if not terrain_mesh:
            self._set_status("Ugyldig mesh!", ed.Colors.Red)
            return

        self._set_status("Beregner tile-dekning...", ed.Colors.Orange)
        try:
            zoom = self._get_zoom_level(size)
            tile_grid = self._get_tile_grid(ost, nord, size, zoom)
        except Exception as ex:
            self._set_status("Feil: Koordinatkonvertering feilet!", ed.Colors.Red)
            print("Coord error:", str(ex))
            return

        self._set_status("Henter satellittbilder...", ed.Colors.Orange)
        tiles_data = {}
        try:
            for row in tile_grid:
                for (tx, ty, zoom) in row:
                    tiles_data[(tx, ty, zoom)] = fetch_tile(tx, ty, zoom)
        except Exception as ex:
            self._set_status("Feil: Tile nedlasting feilet! " + str(ex), ed.Colors.Red)
            return

        self._set_status("Setter sammen bilde...", ed.Colors.Orange)
        try:
            stitched = stitch_tiles(tiles_data, tile_grid)
            print("Stitched size:", stitched.Width, "x", stitched.Height)
        except Exception as ex:
            self._set_status("Feil: Bildesammensetning feilet!", ed.Colors.Red)
            print("Stitch error:", str(ex))
            return

        try:
            temp_path = sio.Path.Combine(
                sio.Path.GetTempPath(),
                "rhino_satelitt_{0}_{1}.jpg".format(int(nord), int(ost))
            )
            stitched.Save(temp_path, sd.Imaging.ImageFormat.Jpeg)
            print("Texture saved to:", temp_path)
        except Exception as ex:
            self._set_status("Feil: Lagring feilet!", ed.Colors.Red)
            return

        self._set_status("Påfører tekstur...", ed.Colors.Orange)
        try:
            self._apply_uv_coordinates(terrain_mesh)
            self._apply_material(doc, terrain_id, terrain_mesh, temp_path)
            doc.Views.Redraw()
            self._set_status("Satellitt påført! Bytt til Rendered view.", ed.Colors.Green)
        except Exception as ex:
            self._set_status("Feil: Tekstur påføring feilet! " + str(ex), ed.Colors.Red)
            print("Material error:", str(ex))


dialog = SatellittTeksturDialog()
dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)