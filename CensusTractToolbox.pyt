#==================================================================================================
#  CensusTractToolbox.pyt
#  CRP 4560/5560 Code Sharing Assignment
#  Author: Kolton Eisma
#  Email: Keisma@iastate.edu
#  Tool: CSV + GeoJSON (Story County tracts) -> Feature Class -> Join -> Display option -> Matplotlib PNG
#==================================================================================================

import os
from pathlib import Path
import arcpy
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt


class Toolbox(object):
    def __init__(self):
        self.label = "Census Tract Code Sharing Toolbox"
        self.alias = "censustracttools"
        self.tools = [CensusTractJoinAndPlot]


class CensusTractJoinAndPlot(object):

    def __init__(self):
        self.label = "Join Census CSV to GeoJSON Tracts + Map + Plot"
        self.description = (
            "Converts a Census GeoJSON to a feature class, joins a Census CSV table, "
            "optionally adds the output to the current map with a display option, "
            "and exports a matplotlib PNG graph of the mapped attribute."
        
        )
        self.canRunInBackground = False

    #==============================================================================================
    # Parameters
    #==============================================================================================
    def getParameterInfo(self):
        p = []

        # (a) user selects CSV + GeoJSON
        csv_path = arcpy.Parameter(
            displayName="Input Census CSV",
            name="csv_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )
        csv_path.filter.list = ["csv"]
        p.append(csv_path)

        geojson_path = arcpy.Parameter(
            displayName="Input GeoJSON / MapLayer JSON",
            name="geojson_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
        )

        geojson_path.filter.list = ["json", "geojson"]
        p.append(geojson_path)

        out_gdb_name = arcpy.Parameter(
            displayName="Output Geodatabase Name",
            name="out_gdb_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        out_gdb_name.value = "outputs.gdb"
        p.append(out_gdb_name)

        out_fc_name = arcpy.Parameter(
            displayName="Output Feature Class Name",
            name="out_fc_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        out_fc_name.value = "StoryCounty_Tracts_Joined"
        p.append(out_fc_name)

        # (d) use join field names
        fc_join_field = arcpy.Parameter(
            displayName="Feature Class Join Field (from GeoJSON feature class)",
            name="fc_join_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        p.append(fc_join_field)

        csv_join_field = arcpy.Parameter(
            displayName="CSV Join Field (from CSV table)",
            name="csv_join_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        p.append(csv_join_field)

        # field to map + plot
        value_field = arcpy.Parameter(
            displayName="CSV Value Field to Map & Plot (numeric field name)",
            name="value_field",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        p.append(value_field)

        # (e) dropdown display options
        display_option = arcpy.Parameter(
            displayName="Display Option (dropdown)",
            name="display_option",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        display_option.filter.type = "ValueList"
        display_option.filter.list = [
            "Do not add to map",
            "Add to current map (single symbol)",
            "Add to current map (graduated colors on value field)",
        ]
        display_option.value = "Add to current map (graduated colors on value field)"
        p.append(display_option)

        # (g) user chooses where to save PNG
        out_png = arcpy.Parameter(
            displayName="Output Graph PNG",
            name="out_png",
            datatype="DEFile",
            parameterType="Required",
            direction="Output",
        )
        out_png.filter.list = ["png"]
        p.append(out_png)
        return p
    #==============================================================================================
    # Dynamic UI: auto-fill + dropdown menus
    #==============================================================================================
    def updateParameters(self, parameters):
        """
        Auto-fill defaults + build dropdown lists.
        Outputs are written to <toolbox_dir>/outputs.
        """
        csv_param = parameters[0]          # Input Census CSV
        geojson_param = parameters[1]      # Input GeoJSON / MapLayer JSON
        fc_join_param = parameters[4]      # Feature Class Join Field
        csv_join_param = parameters[5]     # CSV Join Field
        value_field_param = parameters[6]  # CSV Value Field
        out_png_param = parameters[8]      # Output Graph PNG

        #==========================================================================================
        # A) CSV: dropdowns
        #==========================================================================================
        if csv_param.valueAsText:
            try:
                fields = arcpy.ListFields(csv_param.valueAsText)
                field_names = [f.name for f in fields]

                # ---- CSV Join Field: only allow Geography
                join_candidates = [n for n in ["Geography", "GEOID", "GEOIDFQ"] if n in field_names]

                csv_join_param.filter.type = "ValueList"
                csv_join_param.filter.list = join_candidates

                # Auto-select Geography
                if join_candidates and not csv_join_param.valueAsText:
                    csv_join_param.value = join_candidates[0]

                #  CSV Value Field: numeric fields ONLY, excluding join fields ----
                numeric_fields = [
                    f.name for f in fields
                    if f.type in ("Integer", "Double", "Single", "SmallInteger")
                    and f.name not in join_candidates
                ]

                value_field_param.filter.type = "ValueList"
                value_field_param.filter.list = numeric_fields

                # Auto-select first numeric value
                if numeric_fields and not value_field_param.valueAsText:
                    value_field_param.value = numeric_fields[0]

            except Exception:
                pass


        #==========================================================================================
        # B) GeoJSON: convert to in_memory FC to populate FC join dropdown
        #==========================================================================================
        if geojson_param.valueAsText:
            gj_path = geojson_param.valueAsText
            temp_fc = r"in_memory\_geojson_preview"
            try:
                if arcpy.Exists(temp_fc):
                    arcpy.management.Delete(temp_fc)

                arcpy.conversion.JSONToFeatures(gj_path, temp_fc)

                fc_fields = [f.name for f in arcpy.ListFields(temp_fc)]
                fc_join_param.filter.type = "ValueList"
                fc_join_param.filter.list = fc_fields

                # Default FC join field preference order
                preferred_fc = ["NAMELSAD", "NAME", "BASENAME", "GEOIDFQ", "GEOID"]
                if not fc_join_param.valueAsText:
                    for cand in preferred_fc:
                        if cand in fc_fields:
                            fc_join_param.value = cand
                            break
            except Exception:
                pass
        #==========================================================================================
        # C) Auto-fill Output PNG path
        #==========================================================================================
        try:
            if (not out_png_param.valueAsText):
                toolbox_dir = Path(__file__).resolve().parent
                outputs_dir = toolbox_dir / "outputs"
                outputs_dir.mkdir(parents=True, exist_ok=True)

                safe_field = "plot"
                if value_field_param.valueAsText:
                    safe_field = (
                        value_field_param.valueAsText
                        .replace(" ", "_")
                        .replace("!", "")
                        .replace("/", "_")
                        .replace("\\", "_")
                        .replace(":", "_")
                    )

                out_png_param.value = str(outputs_dir / f"{safe_field}_by_tract.png")
        except Exception:
            pass

    def updateMessages(self, parameters):
        """
        Friendly validation messages before running.
        """
        fc_join_param = parameters[4]
        csv_join_param = parameters[5]
        value_field_param = parameters[6]
        out_png_param = parameters[8]

        # Only flag if user is trying to run without them
        if not fc_join_param.valueAsText:
            fc_join_param.setErrorMessage("Select a feature class join field (dropdown populates after selecting GeoJSON).")

        if not csv_join_param.valueAsText:
            csv_join_param.setErrorMessage("Select a CSV join field (dropdown populates after selecting CSV).")

        if not value_field_param.valueAsText:
            value_field_param.setErrorMessage("Select a numeric CSV field to map and plot.")

        if not out_png_param.valueAsText:
            out_png_param.setErrorMessage("Output PNG will auto-fill after selecting inputs (or set a path manually).")

    #==============================================================================================
    #  Execution
    #==============================================================================================
    def execute(self, parameters, messages):
        csv_path = Path(parameters[0].valueAsText)
        geojson_path = Path(parameters[1].valueAsText)
        out_gdb_name = parameters[2].valueAsText or "outputs.gdb"
        out_fc_name = parameters[3].valueAsText or "StoryCounty_Tracts_Joined"
        fc_join_field = parameters[4].valueAsText
        csv_join_field = parameters[5].valueAsText
        value_field = parameters[6].valueAsText
        display_option = parameters[7].valueAsText
        out_png = Path(parameters[8].valueAsText)
        if csv_join_field == value_field:
                    raise arcpy.ExecuteError("CSV Join Field and CSV Value Field cannot be the same.")

        arcpy.env.overwriteOutput = True
        toolbox_dir = Path(__file__).resolve().parent
        out_folder = toolbox_dir / "outputs"
        out_folder.mkdir(parents=True, exist_ok=True)

        # Create / locate output GDB
        if not out_gdb_name.lower().endswith(".gdb"):
            out_gdb_name = out_gdb_name + ".gdb"

        out_gdb = out_folder / out_gdb_name
        if not out_gdb.exists():
            arcpy.AddMessage(f"Creating output geodatabase: {out_gdb}")
            arcpy.management.CreateFileGDB(str(out_folder), out_gdb_name)

        # (c) Convert GeoJSON -> Feature Class
        temp_fc = out_gdb / "StoryCounty_Tracts_Raw"
        arcpy.AddMessage("Converting GeoJSON/JSON to feature class...")
        # ArcGIS Pro tool supports GeoJSON + Esri JSON:
        arcpy.conversion.JSONToFeatures(str(geojson_path), str(temp_fc))

        if not fc_join_field or fc_join_field.strip() == "":
            fc_join_field = self._pick_fc_join_field(str(temp_fc))
            arcpy.AddMessage(f"Auto-selected feature class join field: {fc_join_field}")

        # Bring CSV in as a table view
        arcpy.AddMessage("Making table view from CSV...")
        csv_view = "csv_view"
        arcpy.management.MakeTableView(str(csv_path), csv_view)

        # Validate fields exist
        self._require_field(str(temp_fc), fc_join_field, "Feature Class Join Field")
        self._require_field(csv_view, csv_join_field, "CSV Join Field")
        self._require_field(csv_view, value_field, "CSV Value Field")

        # Join (writes fields from CSV onto feature class)
        arcpy.AddMessage("Joining CSV fields into feature class...")

        # JoinField modifies the FC by copying fields from the table based on the key
        arcpy.management.JoinField(
            in_data=str(temp_fc),
            in_field=fc_join_field,
            join_table=csv_view,
            join_field=csv_join_field,
            fields=[value_field],
        )

        # Copy to final named feature class
        out_fc = out_gdb / out_fc_name
        arcpy.AddMessage(f"Saving final joined feature class: {out_fc}")
        arcpy.management.CopyFeatures(str(temp_fc), str(out_fc))

        # Optional map display
        if display_option != "Do not add to map":
            self._add_to_current_map(str(out_fc), value_field, display_option)

        # (f) matplotlib graph of the same mapped attribute
        arcpy.AddMessage("Creating matplotlib plot...")
        self._plot_field_by_tract(
            fc_path=str(out_fc),
            tract_label_field=fc_join_field,
            value_field=value_field,
            out_png=str(out_png),
        )

        arcpy.AddMessage("Done.")

    #==============================================================================================
    # Helpers
    #==============================================================================================
    def _require_field(self, dataset, field_name, label):
        fields = [f.name for f in arcpy.ListFields(dataset)]
        if field_name not in fields:
            raise arcpy.ExecuteError(
                f"{label} '{field_name}' not found. Available fields: {fields}"
            )

    def _pick_fc_join_field(self, fc_path: str) -> str:
        candidates = ["NAMELSAD", "NAME", "BASENAME", "GEOIDFQ", "GEOID"]
        fields = [f.name for f in arcpy.ListFields(fc_path)]
        for c in candidates:
            if c in fields:
                return c
        raise arcpy.ExecuteError(f"No suitable join field found in feature class. Fields: {fields}")

    def _add_to_current_map(self, fc_path, value_field, display_option):
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            m = aprx.activeMap
            if m is None:
                arcpy.AddWarning("No active map found. Skipping map display.")
                return

            lyr = m.addDataFromPath(fc_path)
            arcpy.AddMessage("Added output feature class to the current map.")

            if "graduated colors" in display_option.lower():
                sym = lyr.symbology
                sym.updateRenderer("GraduatedColorsRenderer")
                sym.renderer.classificationField = value_field
                sym.renderer.breakCount = 5
                lyr.symbology = sym
                arcpy.AddMessage("Applied graduated colors symbology on the value field.")

        except Exception as ex:
            arcpy.AddWarning(f"Could not add/apply symbology in CURRENT project. {ex}")

    def _plot_field_by_tract(self, fc_path, tract_label_field, value_field, out_png):
        """
        Builds a simple bar chart: tract label vs value_field, saves to PNG.
        """
        labels = []
        values = []

        # Use SearchCursor to extract values
        with arcpy.da.SearchCursor(fc_path, [tract_label_field, value_field]) as cur:
            for tract, val in cur:
                # Skip nulls
                if val is None:
                    continue
                labels.append(str(tract))
                values.append(float(val))

        if not values:
            raise arcpy.ExecuteError("No numeric values found to plot (all null/empty?).")

        # Sort by tract label
        pairs = sorted(zip(labels, values), key=lambda x: x[0])
        labels, values = zip(*pairs)

        # Simple plot
        plt.figure(figsize=(12, 6))
        plt.bar(labels, values)
        plt.xticks(rotation=90)
        plt.ylabel(value_field)
        plt.title(f"{value_field} by Census Tract")
        plt.tight_layout()

        out_dir = Path(out_png).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        plt.savefig(out_png, dpi=300)
        plt.close()