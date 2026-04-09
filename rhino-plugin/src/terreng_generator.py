# -*- coding: utf-8 -*-
import Rhino
import Rhino.Geometry as rg
import Rhino.UI
import Eto.Forms as ef
import Eto.Drawing as ed
import System.IO as sio
import System.Drawing as sd


class TerrengDialog(ef.Dialog):

    def __init__(self):
        self.Title = "Terreng Generator"
        self.Padding = ed.Padding(10)
        self.Resizable = False

        nord_label = ef.Label()
        nord_label.Text = "Nord UTM (eks: 6790000):"
        self.nord_input = ef.TextBox()
        self.nord_input.Text = "6790000"
        self.nord_input.Width = 300

        ost_label = ef.Label()
        ost_label.Text = "Øst UTM (eks: 394000):"
        self.ost_input = ef.TextBox()
        self.ost_input.Text = "394000"
        self.ost_input.Width = 300

        # Size input
        size_label = ef.Label()
        size_label.Text = "Størrelse i meter (eks: 500):"
        self.size_input = ef.TextBox()
        self.size_input.Text = "500"
        self.size_input.Width = 300

        self.status_label = ef.Label()
        self.status_label.Text = "Skriv inn UTM koordinater og klikk Hent."
        self.status_label.TextColor = ed.Colors.Gray

        hent_btn = ef.Button()
        hent_btn.Text = "Hent Terreng"
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
        layout.Rows.Add(ef.TableRow(ef.TableCell(nord_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.nord_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(ost_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.ost_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(size_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.size_input)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(self.status_label)))
        layout.Rows.Add(ef.TableRow(ef.TableCell(btn_row)))

        self.Content = layout

    def on_avbryt(self, sender, e):
        self.Close()

    def on_hent(self, sender, e):
        self.status_label.Text = "Henter terrengdata..."
        self.status_label.TextColor = ed.Colors.Orange

        #  Parse coordinates
        try:
            nord = float(self.nord_input.Text.strip())
            ost = float(self.ost_input.Text.strip())
            size = float(self.size_input.Text.strip())
            print("Coordinates:", nord, ost, "Size:", size)
        except:
            self.status_label.Text = "Feil: Ugyldig koordinater!"
            self.status_label.TextColor = ed.Colors.Red
            return

        #  Build URL
        bbox = "{0},{1},{2},{3},urn:ogc:def:crs:EPSG::25833".format(
            ost, nord, ost + size, nord + size
        )
        url = (
            "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm-nhm-25833?"
            "service=WCS&version=1.1.0&request=GetCoverage"
            "&identifier=nhm_dtm_topo_25833"
            "&boundingbox=" + bbox +
            "&format=image/png&store=false"
        )
        print("URL:", url)

        #  Download data
        try:
            try:
                import urllib.request as urllib_req
            except ImportError:
                import urllib2 as urllib_req

            self.status_label.Text = "Laster ned fra Kartverket..."
            response = urllib_req.urlopen(url, timeout=30)
            raw_data = response.read()
            print("Downloaded bytes:", len(raw_data))

        except Exception as ex:
            self.status_label.Text = "Feil: Nedlasting feilet!"
            self.status_label.TextColor = ed.Colors.Red
            print("Download error:", str(ex))
            return

        #  Find PNG in response
        png_sig = b'\x89PNG\r\n\x1a\n'
        png_start = raw_data.find(png_sig)

        if png_start == -1:
            self.status_label.Text = "Feil: Ingen PNG data!"
            self.status_label.TextColor = ed.Colors.Red
            print("Server response:", raw_data[:500])
            return

        png_data = raw_data[png_start:]
        print("PNG size:", len(png_data))

        #  Read PNG directly from memory
        try:
            import System
            png_bytes = System.Array[System.Byte](bytearray(png_data))
            memory_stream = sio.MemoryStream(png_bytes)
            bmp = sd.Bitmap(memory_stream)
            print("Bitmap size:", bmp.Width, "x", bmp.Height)
        except Exception as ex:
            self.status_label.Text = "Feil: Kunne ikke lese PNG!"
            self.status_label.TextColor = ed.Colors.Red
            print("Bitmap error:", str(ex))
            return

        #  Build mesh
        try:
            width = bmp.Width
            height = bmp.Height
            step = 3  # Skip pixels for performance
            min_z = 999999
            max_z = -999999

            doc = Rhino.RhinoDoc.ActiveDoc
            mesh = rg.Mesh()

            #  collect all Z values to find min
            all_z = []
            for y in range(0, height, step):
                for x in range(0, width, step):
                    pixel = bmp.GetPixel(x, y)
                    all_z.append(float(pixel.R))

            min_z = min(all_z)
            max_z = max(all_z)
            print("Height range:", min_z, "to", max_z)

            #  build mesh vertices
            for y in range(0, height, step):
                for x in range(0, width, step):
                    pixel = bmp.GetPixel(x, y)
                    # Subtract min_z so terrain starts at Z=0
                    z = (float(pixel.R) - min_z) * 1.0

                    # Scale to real world size
                    x_pos = (float(x) / width) * size
                    y_pos = (float(y) / height) * size

                    mesh.Vertices.Add(rg.Point3d(x_pos, y_pos, z))

            # Build mesh faces
            cols = len(range(0, width, step))
            rows = len(range(0, height, step))

            for i in range(rows - 1):
                for j in range(cols - 1):
                    mesh.Faces.AddFace(
                        i * cols + j,
                        i * cols + (j + 1),
                        (i + 1) * cols + (j + 1),
                        (i + 1) * cols + j
                    )

            # Fix normals so terrain faces up not down
            mesh.Normals.ComputeNormals()
            mesh.UnifyNormals()

            # --- Height-based vertex colors ---
            # Green (low) -> Yellow (mid) -> Red/White (high peaks)
            mesh.VertexColors.CreateMonotoneMesh(sd.Color.White)
            total_z_range = max_z - min_z
            if total_z_range < 0.1:
                total_z_range = 1.0  # avoid division by zero on flat terrain

            vert_idx = 0
            for y in range(0, height, step):
                for x in range(0, width, step):
                    pixel = bmp.GetPixel(x, y)
                    z_raw = float(pixel.R)
                    # Normalize 0.0 (lowest) to 1.0 (highest)
                    t = (z_raw - min_z) / total_z_range

                    if t < 0.5:
                        # Green -> Yellow
                        tt = t / 0.5
                        r = int(tt * 210)
                        g = int(150 + tt * 85)
                        b = int(60 - tt * 60)
                    else:
                        # Yellow -> Red/White (peaks)
                        tt = (t - 0.5) / 0.5
                        r = int(210 + tt * 45)
                        g = int(235 - tt * 200)
                        b = int(tt * 220)

                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))

                    mesh.VertexColors[vert_idx] = sd.Color.FromArgb(r, g, b)
                    vert_idx += 1

            # Center mesh at origin X and Y but keep Z at 0
            bbox_mesh = mesh.GetBoundingBox(True)
            move = rg.Vector3d(
                -bbox_mesh.Center.X,
                -bbox_mesh.Center.Y,
                0  # Keep Z at ground level
            )
            mesh.Translate(move)

        except Exception as ex:
            self.status_label.Text = "Feil: Mesh generering feilet!"
            self.status_label.TextColor = ed.Colors.Red
            print("Mesh error:", str(ex))
            return

        # Add to Rhino
        if abs(max_z - min_z) < 0.1:
            self.status_label.Text = "Advarsel: Flatt terreng - sjekk koordinater!"
            self.status_label.TextColor = ed.Colors.Orange
        else:
            doc.Objects.AddMesh(mesh)
            doc.Views.Redraw()
            self.status_label.Text = "Terreng generert! Høydeforskjell: " + str(round(max_z - min_z, 1)) + "m"
            self.status_label.TextColor = ed.Colors.Green


dialog = TerrengDialog()
dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)