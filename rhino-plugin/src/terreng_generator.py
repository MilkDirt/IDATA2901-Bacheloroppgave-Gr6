# -*- coding: utf-8 -*-
"""
terreng_generator.py
====================
Generates 3D terrain mesh in Rhino from Norwegian elevation data (Kartverket).

INPUT:  GPS coordinates (latitude/longitude) — copy straight from Google Maps
        or norgeskart.no. No UTM knowledge needed.
OUTPUT: Rhino mesh with real elevation in meters, height-colored.

Can be run standalone (shows dialog) or called via generate_terrain(lat, lon, size).
"""

import Rhino
import Rhino.Geometry as rg
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed
import System.Drawing as sd
import os
import math
import struct

# ---------------------------------------------------------------------------
# Config — tweak these at the top
# ---------------------------------------------------------------------------

MESH_STEP     = 3    # Sample every Nth pixel. 1=full res (slow), 4=good balance, 8=fast preview
SMOOTH_ITER   = 2    # Box-smooth passes on Z grid (0=none, 1=light, 2=smooth)
SMOOTH_RADIUS = 2    # Kernel radius: 1=3x3, 2=5x5  (1 pass 3x3 = near-raw)
Z_SCALE       = 1.3  # Vertical exaggeration (1.0=real scale, 2.0=dramatic)
CACHE_DIR     = os.path.join(os.path.expanduser("~"), "rhino_terrain_cache")

# Natural elevation color stops: (t 0-1, R, G, B)
COLOR_STOPS = [
    (0.00,  20, 100,  20),   # deep green   - valley / sea level
    (0.20,  60, 160,  50),   # mid green    - lowland
    (0.40, 180, 200,  60),   # yellow-green - hills
    (0.60, 160, 110,  40),   # brown        - rocky
    (0.80, 140,  60,  30),   # dark red     - high peaks
    (1.00, 240, 240, 250),   # near-white   - snow
]

# ---------------------------------------------------------------------------
# UTM conversion (no external libraries)
# ---------------------------------------------------------------------------

def _latlon_to_utm(lat, lon):
    """
    Convert WGS84 lat/lon to UTM easting/northing + zone number.
    Applies Norway zone rules:
      Sør-Norge / Vestlandet / Møre og Romsdal -> zone 32
      Nordland / Troms                          -> zone 33
      Finnmark                                  -> zone 35
    Returns (easting, northing, zone_number, epsg_code).
    """
    if lat >= 72.0:
        zone = 33  # Svalbard
    elif lat >= 56.0 and lat < 64.0 and lon >= 3.0 and lon < 12.0:
        zone = 32  # Sør-Norge og Vestlandet inkl Møre og Romsdal
    elif lat >= 64.0 and lon < 18.0:
        zone = 32  # Trøndelag vest
    elif lon >= 21.0 and lat >= 68.0:
        zone = 35  # Finnmark
    elif lat >= 65.0:
        zone = 33  # Nordland / Troms
    else:
        zone = 33  # Default for resten av Norge

    epsg = 25800 + zone

    # WGS84 ellipsoid constants
    a  = 6378137.0
    f  = 1.0 / 298.257223563
    b  = a * (1 - f)
    e2 = 1 - (b / a) ** 2
    n  = f / (2 - f)

    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    lon0  = math.radians((zone - 1) * 6 - 180 + 3)

    N  = a / math.sqrt(1 - e2 * math.sin(lat_r) ** 2)
    T  = math.tan(lat_r) ** 2
    C  = e2 / (1 - e2) * math.cos(lat_r) ** 2
    A_ = math.cos(lat_r) * (lon_r - lon0)
    M  = a * (
        (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * lat_r
        - (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * math.sin(2*lat_r)
        + (15*e2**2/256 + 45*e2**3/1024) * math.sin(4*lat_r)
        - (35*e2**3/3072) * math.sin(6*lat_r)
    )

    k0 = 0.9996
    easting = k0 * N * (
        A_ + (1 - T + C) * A_**3 / 6
        + (5 - 18*T + T**2 + 72*C - 58*(e2/(1-e2))) * A_**5 / 120
    ) + 500000.0

    northing = k0 * (
        M + N * math.tan(lat_r) * (
            A_**2 / 2
            + (5 - T + 9*C + 4*C**2) * A_**4 / 24
            + (61 - 58*T + T**2 + 600*C - 330*(e2/(1-e2))) * A_**6 / 720
        )
    )
    if lat < 0:
        northing += 10000000.0

    return easting, northing, zone, epsg


# ---------------------------------------------------------------------------
# Kartverket WCS URL builder
# ---------------------------------------------------------------------------

def _build_wcs_url(ost, nord, size, epsg):
    """
    Build Kartverket WCS GetCoverage URL requesting GeoTIFF (Float32).
    Minimum bbox the server accepts is 1500m.
    """
    fetch = max(float(size), 1500.0)
    crs   = "urn:ogc:def:crs:EPSG::{0}".format(epsg)
    half = fetch / 2.0

    bbox = "{0},{1},{2},{3},{4}".format(
        ost - half,
        nord - half,
        ost + half,
        nord + half,
        crs
    )

    if epsg == 25832:
        identifier = "nhm_dtm_topo_25832"
        base = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25832"
    elif epsg == 25835:
        identifier = "nhm_dtm_topo_25835"
        base = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25835"
    else:
        identifier = "nhm_dtm_topo_25833"
        base = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833"

    url = (
        "{base}?service=WCS&version=1.1.0&request=GetCoverage"
        "&identifier={id}&boundingbox={bbox}"
        "&format=image/tiff&store=false"
    ).format(base=base, id=identifier, bbox=bbox)

    return url, fetch


# ---------------------------------------------------------------------------
# Download with disk cache
# ---------------------------------------------------------------------------

def _cache_path(ost, nord, size, epsg):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    fname = "dtm_{epsg}_{ost}_{nord}_{size}.tif".format(
        epsg=epsg, ost=int(ost), nord=int(nord), size=int(size))
    return os.path.join(CACHE_DIR, fname)


def _download_geotiff(url, cache_file):
    """
    Download GeoTIFF from Kartverket WCS.
    WCS 1.1 returns multipart MIME — extract TIFF bytes by searching for magic header.
    """
    try:
        import urllib.request as ul
    except ImportError:
        import urllib2 as ul

    response = ul.urlopen(url, timeout=60)
    raw = response.read()

    # TIFF magic: little-endian "II*\x00" or big-endian "MM\x00*"
    idx = raw.find(b'II\x2A\x00')
    if idx == -1:
        idx = raw.find(b'MM\x00\x2A')
    if idx == -1:
        try:
            msg = raw.decode('utf-8', errors='replace')[:800]
        except Exception:
            msg = repr(raw[:200])
        raise Exception("Ingen TIFF i svaret fra Kartverket.\nServer melding:\n" + msg)

    tiff_data = raw[idx:]
    with open(cache_file, 'wb') as f:
        f.write(tiff_data)
    return tiff_data


# ---------------------------------------------------------------------------
# Raw GeoTIFF Float32 parser (no gdal/rasterio)
# ---------------------------------------------------------------------------

def _read_geotiff_floats(tiff_data):
    """
    Parse a Float32 single-band GeoTIFF from raw bytes using only struct.
    GeoTIFF = standard TIFF + geo metadata tags. Pixel data is plain TIFF.

    Supports:
      - Little-endian and big-endian
      - Stripped TIFF layout (what Kartverket sends)
      - Float32 (SampleFormat=3, BitsPerSample=32)
      - Int16 / UInt16 fallback for older DTM10 data

    Returns (pixels_flat_list, width, height).
    """
    if len(tiff_data) < 8:
        raise Exception("TIFF for kort")

    bo = '<' if tiff_data[:2] == b'II' else '>'
    if tiff_data[:2] not in (b'II', b'MM'):
        raise Exception("Ikke gyldig TIFF-header")

    magic = struct.unpack_from(bo + 'H', tiff_data, 2)[0]
    if magic != 42:
        raise Exception("Feil TIFF magic: " + str(magic))

    ifd_offset = struct.unpack_from(bo + 'I', tiff_data, 4)[0]

    TYPE_SIZE = {1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8}
    TYPE_FMT  = {1:'B',2:'s',3:'H',4:'I',5:'II',6:'b',7:'B',
                 8:'h',9:'i',10:'ii',11:'f',12:'d'}

    tags = {}
    num_entries   = struct.unpack_from(bo + 'H', tiff_data, ifd_offset)[0]
    entry_offset  = ifd_offset + 2

    for _ in range(num_entries):
        tag_id  = struct.unpack_from(bo + 'H', tiff_data, entry_offset)[0]
        dtype   = struct.unpack_from(bo + 'H', tiff_data, entry_offset + 2)[0]
        count   = struct.unpack_from(bo + 'I', tiff_data, entry_offset + 4)[0]
        val_off = entry_offset + 8

        tsize = TYPE_SIZE.get(dtype, 1)
        total = tsize * count
        raw_v = (tiff_data[val_off: val_off + 4] if total <= 4
                 else tiff_data[struct.unpack_from(bo+'I', tiff_data, val_off)[0]:
                                struct.unpack_from(bo+'I', tiff_data, val_off)[0]+total])

        fmt = TYPE_FMT.get(dtype)
        if fmt and fmt != 's':
            try:
                val = (struct.unpack_from(bo+fmt, raw_v)[0] if count == 1
                       else list(struct.unpack_from(bo+fmt*count, raw_v)))
            except Exception:
                val = None
        else:
            val = raw_v

        tags[tag_id] = val
        entry_offset += 12

    width          = tags.get(256)
    height         = tags.get(257)
    bits           = tags.get(258)
    sample_fmt     = tags.get(339)
    strip_offsets  = tags.get(273)   # Stripped layout
    strip_counts   = tags.get(279)
    tile_offsets   = tags.get(324)   # Tiled layout
    tile_counts    = tags.get(325)
    tile_width     = tags.get(322)
    tile_height    = tags.get(323)

    if isinstance(bits, list):       bits       = bits[0]
    if isinstance(sample_fmt, list): sample_fmt = sample_fmt[0]
    if isinstance(tile_width, list): tile_width = tile_width[0]
    if isinstance(tile_height,list): tile_height= tile_height[0]

    if width is None or height is None:
        raise Exception("Klarte ikke lese TIFF-dimensjoner (tag 256/257 mangler)")

    # Decide pixel format
    if bits == 32 and sample_fmt == 3:
        px_fmt, px_size = bo+'f', 4
    elif bits == 32:
        px_fmt, px_size = bo+('i' if sample_fmt==2 else 'I'), 4
    elif bits == 16 and sample_fmt == 2:
        px_fmt, px_size = bo+'h', 2
    elif bits == 16:
        px_fmt, px_size = bo+'H', 2
    elif bits == 8:
        px_fmt, px_size = bo+'B', 1
    else:
        raise Exception("Ustøttet format: {b}-bit sf={sf}".format(b=bits, sf=sample_fmt))

    pixels = [0.0] * (width * height)

    # --- TILED layout ---
    if tile_offsets is not None and tile_width is not None:
        if not isinstance(tile_offsets, list): tile_offsets = [tile_offsets]
        if not isinstance(tile_counts,  list): tile_counts  = [tile_counts]
        tiles_across = (width  + tile_width  - 1) // tile_width
        tiles_down   = (height + tile_height - 1) // tile_height
        tile_idx = 0
        for ty in range(tiles_down):
            for tx in range(tiles_across):
                if tile_idx >= len(tile_offsets):
                    break
                off = tile_offsets[tile_idx]
                cnt = tile_counts[tile_idx]
                tile_data = tiff_data[off: off + cnt]
                n = cnt // px_size
                vals = list(struct.unpack_from(bo + px_fmt[-1] * n, tile_data))
                # Copy tile pixels into full image grid
                for row in range(tile_height):
                    img_row = ty * tile_height + row
                    if img_row >= height:
                        break
                    for col in range(tile_width):
                        img_col = tx * tile_width + col
                        if img_col >= width:
                            break
                        src = row * tile_width + col
                        dst = img_row * width + img_col
                        if src < len(vals) and dst < len(pixels):
                            pixels[dst] = float(vals[src])
                tile_idx += 1

    # --- STRIPPED layout ---
    elif strip_offsets is not None:
        if not isinstance(strip_offsets, list): strip_offsets = [strip_offsets]
        if not isinstance(strip_counts,  list): strip_counts  = [strip_counts]
        flat = []
        for off, cnt in zip(strip_offsets, strip_counts):
            strip = tiff_data[off: off + cnt]
            n     = cnt // px_size
            flat.extend(struct.unpack_from(bo + px_fmt[-1] * n, strip))
        pixels = [float(v) for v in flat]

    else:
        raise Exception("TIFF har verken strips eller tiles — ukjent layout")

    if len(pixels) < width * height:
        raise Exception("For fa pixlar: forventet {e}, fikk {g}".format(
            e=width*height, g=len(pixels)))

    return pixels, width, height


# ---------------------------------------------------------------------------
# Grid smoothing
# ---------------------------------------------------------------------------

def _box_smooth(grid, cols, rows, radius, passes):
    """Box-average on flat 2D grid. Runs on Z values before mesh is built."""
    for _ in range(passes):
        ng = list(grid)
        for r in range(rows):
            for c in range(cols):
                total, count = 0.0, 0
                for rr in range(max(0,r-radius), min(rows-1,r+radius)+1):
                    for cc in range(max(0,c-radius), min(cols-1,c+radius)+1):
                        total += grid[rr*cols+cc]
                        count += 1
                ng[r*cols+c] = total/count
        grid = ng
    return grid


# ---------------------------------------------------------------------------
# Mesh building
# ---------------------------------------------------------------------------

def _build_mesh(pixels, img_w, img_h, fetch_size, requested_size):
    """
    Build Rhino mesh from flat pixel list.
    Crops the image to exactly requested_size meters so a 500m request
    gives a real 500x500m patch at full resolution (not squished 1500m).
    Returns (mesh, min_elev_m, max_elev_m).
    """
    step = MESH_STEP

    # Kartverket returns ~1px per meter so crop pixel count = requested meters
    crop_ratio = min(1.0, float(requested_size) / float(fetch_size))
    crop_w = max(2, int(img_w * crop_ratio))
    crop_h = max(2, int(img_h * crop_ratio))

    cols = len(range(0, crop_w, step))
    rows = len(range(0, crop_h, step))

    # --- CENTERED CROP (FIX) ---
    center_x = img_w // 2
    center_y = img_h // 2

    half_w = crop_w // 2
    half_h = crop_h // 2

    start_x = max(0, center_x - half_w)
    start_y = max(0, center_y - half_h)

    sampled = [
        pixels[(start_y + r) * img_w + (start_x + c)]
        for r in range(0, crop_h, step)
        for c in range(0, crop_w, step)
    ]

    NODATA_LOW, NODATA_HIGH = -1000.0, 10000.0
    valid = [v for v in sampled if NODATA_LOW < v < NODATA_HIGH]
    if not valid:
        raise Exception(
            "Ingen gyldige hoydepixler. "
            "Sjekk at koordinatene er pa norsk fastland.")

    valid_s = sorted(valid)
    n       = len(valid_s)
    median  = valid_s[n // 2]
    p2      = valid_s[max(0, int(n * 0.02))]
    p98     = valid_s[min(n-1, int(n * 0.98))]

    cleaned = []
    for v in sampled:
        if v <= NODATA_LOW or v >= NODATA_HIGH:
            cleaned.append(median)
        else:
            cleaned.append(max(p2, min(p98, v)))

    if SMOOTH_ITER > 0:
        cleaned = _box_smooth(cleaned, cols, rows, SMOOTH_RADIUS, SMOOTH_ITER)

    min_z    = min(cleaned)
    max_z    = max(cleaned)
    mesh = rg.Mesh()
    for idx, z_val in enumerate(cleaned):
        ri = idx // cols
        ci = idx % cols
        # Flip Y: TIFF row 0 = north (high UTM Y), so invert row direction
        mesh.Vertices.Add(rg.Point3d(
            (float(ci * step) / crop_w) * requested_size,
            (1.0 - float(ri * step) / crop_h) * requested_size,
            (z_val - min_z) * Z_SCALE,
        ))

    for i in range(rows - 1):
        for j in range(cols - 1):
            mesh.Faces.AddFace(
                i*cols+j, i*cols+(j+1),
                (i+1)*cols+(j+1), (i+1)*cols+j)

    mesh.Normals.ComputeNormals()
    mesh.UnifyNormals()
    return mesh, min_z, max_z


# ---------------------------------------------------------------------------
# Vertex coloring
# ---------------------------------------------------------------------------

def _lerp_color(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(COLOR_STOPS)-1):
        t0,r0,g0,b0 = COLOR_STOPS[i]
        t1,r1,g1,b1 = COLOR_STOPS[i+1]
        if t <= t1:
            f = (t-t0)/(t1-t0) if t1 != t0 else 1.0
            return int(r0+f*(r1-r0)), int(g0+f*(g1-g0)), int(b0+f*(b1-b0))
    return COLOR_STOPS[-1][1], COLOR_STOPS[-1][2], COLOR_STOPS[-1][3]


def _apply_colors(mesh, min_z, max_z):
    mesh.VertexColors.CreateMonotoneMesh(sd.Color.White)
    z_range = max((max_z - min_z) * Z_SCALE, 0.1)
    for vi in range(mesh.Vertices.Count):
        t = max(0.0, min(1.0, mesh.Vertices[vi].Z / z_range))
        r, g, b = _lerp_color(t)
        mesh.VertexColors[vi] = sd.Color.FromArgb(
            max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def generate_terrain(lat, lon, size):
    """
    Download and generate terrain mesh from GPS coordinates.
    lat, lon : WGS84 decimal degrees  (e.g. 62.4722, 6.1495 for Ålesund)
    size     : area side length in meters  (e.g. 1000)
    Returns  : (success: bool, message: str)
    """
    try:
        ost, nord, zone, epsg = _latlon_to_utm(lat, lon)
        print("UTM sone {z} (EPSG:{e}): Ost={o:.0f}, Nord={n:.0f}".format(
            z=zone, e=epsg, o=ost, n=nord))
    except Exception as ex:
        return False, "Koordinat-feil: " + str(ex)

    try:
        url, fetch_size = _build_wcs_url(ost, nord, size, epsg)
        cache_file = _cache_path(ost, nord, size, epsg)
        print("URL: " + url)
    except Exception as ex:
        return False, "URL-feil: " + str(ex)

    try:
        if os.path.exists(cache_file):
            print("Bruker cache: " + cache_file)
            with open(cache_file, 'rb') as f:
                tiff_data = f.read()
        else:
            print("Laster ned fra Kartverket...")
            tiff_data = _download_geotiff(url, cache_file)
            print("Lastet ned {kb} KB".format(kb=len(tiff_data)//1024))
    except Exception as ex:
        return False, "Nedlasting feilet: " + str(ex)

    try:
        pixels, img_w, img_h = _read_geotiff_floats(tiff_data)
        print("TIFF: {w}x{h} px".format(w=img_w, h=img_h))
    except Exception as ex:
        if os.path.exists(cache_file):
            os.remove(cache_file)
        return False, "TIFF-parsing feilet: " + str(ex)

    try:
        mesh, min_z, max_z = _build_mesh(pixels, img_w, img_h, fetch_size, size)
        if (max_z - min_z) < 0.5:
            return False, (
                "Advarsel: Nesten flatt terreng ({:.1f}m). "
                "Er koordinatene i hav?".format(max_z - min_z))
    except Exception as ex:
        return False, "Mesh-feil: " + str(ex)

    try:
        _apply_colors(mesh, min_z, max_z)
        bbox = mesh.GetBoundingBox(True)
        mesh.Translate(rg.Vector3d(-bbox.Center.X, -bbox.Center.Y, 0))
        doc = Rhino.RhinoDoc.ActiveDoc
        doc.Objects.AddMesh(mesh)
        doc.Views.Redraw()
        return True, (
            "OK!  Hoydeforskjell: {h:.1f}m  |  "
            "Min: {mn:.0f}m  Max: {mx:.0f}m  |  "
            "{s}x{s}m  |  UTM sone {z}".format(
                h=max_z-min_z, mn=min_z, mx=max_z, s=int(size), z=zone))
    except Exception as ex:
        return False, "Rhino-feil: " + str(ex)


# ---------------------------------------------------------------------------
# Standalone dialog
# ---------------------------------------------------------------------------

class TerrengGeneratorDialog(ef.Dialog):

    def __init__(self):
        super(TerrengGeneratorDialog, self).__init__()
        self.Title     = "Terreng Generator"
        self.Padding   = ed.Padding(14)
        self.Resizable = False
        self.Width     = 360
        self.Height    = 310
        self._build_ui()

    def _build_ui(self):
        hint = ef.Label()
        hint.Text = (
            "Koordinater fra Google Maps eller norgeskart.no\n"
            "Eksempel Ålesund: 62.4722  /  6.1495")
        hint.TextColor = ed.Colors.DarkGray

        self.lat_inp  = self._tb("62.4722")
        self.lon_inp  = self._tb("6.1495")
        self.size_inp = self._tb("1000")

        self.status = ef.Label()
        self.status.Text      = "Fyll inn koordinater og klikk Hent."
        self.status.TextColor = ed.Colors.Gray
        self.status.Width     = 330

        hent_btn = ef.Button()
        hent_btn.Text   = "Hent Terreng"
        hent_btn.Width  = 140
        hent_btn.Click += self._on_hent

        lukk_btn = ef.Button()
        lukk_btn.Text   = "Lukk"
        lukk_btn.Width  = 80
        lukk_btn.Click += lambda s, e: self.Close()

        cache_btn = ef.Button()
        cache_btn.Text   = "Slett cache"
        cache_btn.Width  = 100
        cache_btn.Click += self._on_clear_cache

        btn_row = ef.TableLayout()
        btn_row.Spacing = ed.Size(6, 0)
        btn_row.Rows.Add(ef.TableRow(
            ef.TableCell(lukk_btn),
            ef.TableCell(cache_btn),
            ef.TableCell(hent_btn),
        ))

        layout = ef.TableLayout()
        layout.Spacing = ed.Size(5, 7)
        layout.Rows.Add(ef.TableRow(ef.TableCell(hint)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))
        self._row(layout, "Breddegrad (lat):",  self.lat_inp)
        self._row(layout, "Lengdegrad (lon):",  self.lon_inp)
        self._row(layout, "Storrelse (meter):", self.size_inp)
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self._spacer(4))))
        layout.Rows.Add(ef.TableRow(ef.TableCell(btn_row)))
        self.Content = layout

        # Set defaults AFTER Content is assigned — Eto renders them reliably this way
        self.lat_inp.Text  = "62.47433077311483"
        self.lon_inp.Text  = "6.164769452950289"
        self.size_inp.Text = "1000"

    def _tb(self, default):
        t = ef.TextBox()
        t.Text  = default
        t.Width = 200
        return t

    def _spacer(self, h=8):
        l = ef.Label()
        l.Height = h
        return l

    def _row(self, layout, label_text, control):
        l = ef.Label()
        l.Text  = label_text
        l.Width = 120
        layout.Rows.Add(ef.TableRow(ef.TableCell(l), ef.TableCell(control)))

    def _set_status(self, text, color):
        self.status.Text      = text
        self.status.TextColor = color

    def _on_clear_cache(self, sender, e):
        if os.path.exists(CACHE_DIR):
            removed = sum(
                1 for f in os.listdir(CACHE_DIR)
                if f.endswith('.tif') and not os.remove(os.path.join(CACHE_DIR, f)))
            self._set_status("Slettet {n} cache-fil(er).".format(n=removed), ed.Colors.Orange)
        else:
            self._set_status("Ingen cache.", ed.Colors.Gray)

    def _on_hent(self, sender, e):
        try:
            lat  = float(self.lat_inp.Text.strip().replace(',', '.'))
            lon  = float(self.lon_inp.Text.strip().replace(',', '.'))
            size = float(self.size_inp.Text.strip())
        except Exception:
            self._set_status("Feil: Skriv inn gyldige tall.", ed.Colors.Red)
            return

        if not (57.0 <= lat <= 72.0):
            self._set_status(
                "Lat {:.4f} er utenfor Norge (57-72). Bruker du desimalgrader?".format(lat),
                ed.Colors.Orange)
            return
        if not (4.0 <= lon <= 32.0):
            self._set_status(
                "Lon {:.4f} er utenfor Norge (4-32).".format(lon),
                ed.Colors.Orange)
            return
        if not (200 <= size <= 5000):
            self._set_status("Storrelse ma vare 200-5000 meter.", ed.Colors.Orange)
            return

        self._set_status("Laster ned fra Kartverket...", ed.Colors.Orange)
        success, msg = generate_terrain(lat, lon, size)
        self._set_status(msg, ed.Colors.Green if success else ed.Colors.Red)


if __name__ == "__main__":
    dlg = TerrengGeneratorDialog()
    dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)