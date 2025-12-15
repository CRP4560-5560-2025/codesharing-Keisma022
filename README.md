CRP 4560/5560 Code Sharing Assignment
Author: Kolton Eisma
Date Created: December 11, 2025
------------------------------------------------------------------------------
Purpose
------------------------------------------------------------------------------
This ArcGIS Pro Python Toolbox automates a workflow to:
Convert a Story County, IA Census Tracts GeoJSON/Esri JSON file into a feature class
Join a join-ready Census CSV table to the tract feature class
Optionally add the joined feature class to the current map with a display style
Export a matplotlib bar chart (PNG) of the selected numeric variable by tract

--------------------------------------------------------------------------------
Data Accessed
--------------------------------------------------------------------------------
**Census Geography**: Story County, IA Census Tracts (downloaded as GeoJSON / MapLayer JSON from data.census.gov)
**Census Table**: ACS 5-year subject table (example used: households receiving SNAP/food stamps)

-------------------------------------------------------------------------------
How to Run
-------------------------------------------------------------------------------
1. Open the ArcGIS Pro project and add the toolbox: CensusTractToolbox.pyt
2. Run the tool: Join Census CSV to GeoJSON Tracts + Map + Plot
3. Provide the inputs:
    Input Census CSV (join-ready): CSV with Geography + one numeric value field
    Input GeoJSON / MapLayer JSON: Story County tract boundaries file
4. Select fields from dropdown menus:
    Feature Class Join Field (typically NAME or NAMELSAD)
    CSV Join Field (typically Geography)
    CSV Value Field (numeric variable to map/plot)
5. Choose a display option (or “Do not add to map”)
6. Run the tool. Outputs are written to the toolbox outputs/ folder:
    outputs.gdb (joined feature class)
    A PNG chart of the selected variable by tract
--------------------------------------------------------------------------------
Notes / Expected Output Location
--------------------------------------------------------------------------------
Outputs are saved to a folder named outputs located in the same directory as the toolbox file to improve portability.
