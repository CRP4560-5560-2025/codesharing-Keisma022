Census_Map_Toolbox.pyt

This ArcGIS Pro project includes a custom Python Toolbox that joins Census Tract boundaries with Census Data stored in Excel. It will display the data on a map and generate a graph of the selected variable.
This tool is designed to work with:
  Census_Tract_Excel.xlsx
  Census_Tract.geojson
What does this tool do?
1. Reads an Excel File & Converts it to an ArcGIS Table
2. Reads a GeoJSON File & converts it into a feature Class
3. Joins the tables based on:
  -GeoJSON Field: NAME
  -Excel Field: Geography 
4. Adds the joined layer to the active map in ArcGIS Pro.
5. Creates a graph of the selected attribute column from an Excel File using matplotlib.
6. Saves the Graph as a PNG at a user-chosen location
