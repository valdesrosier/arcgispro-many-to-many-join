# Many-to-Many Join ArcPy Tool

## Overview

This repository provides a custom ArcPy geoprocessing tool for ArcGIS Pro that performs a many-to-many join between two feature layers or tables. The tool preserves all fields and geometry, and is implemented as a Python toolbox (`.pyt`) using pure ArcPy logic.

## Features

- Many-to-many join between feature layers or tables
- Preserves all fields and geometry in the output
- Robust handling of field types and nullability
- No external dependencies (pure ArcPy)
- Output feature class is automatically added to the map

## Installation

1. Clone or download this repository.
2. Place `manytomanyjoin.pyt` in your ArcGIS Pro project folder.
3. Add the toolbox to your ArcGIS Pro project.

## Usage

1. Open ArcGIS Pro and add the toolbox (`manytomanyjoin.pyt`) to your project.
2. Run the "Many to Many Join" tool.
3. Select:
   - Target Feature Layer
   - Join Layer/Table
   - Output Feature Class (path in your default geodatabase)
   - Target Field (field to join on in the target layer)
   - Join Field (field to join on in the join layer/table)
4. Execute the tool. The output feature class will be created and added to your map.

## Parameters

- **Target Feature Layer**: The main feature layer to join.
- **Join Layer/Table**: The secondary layer or table to join.
- **Output Feature Class**: Path for the resulting feature class.
- **Target Field**: Field in the target layer to join on.
- **Join Field**: Field in the join layer/table to join on.

## Notes

- The tool uses ArcPy’s built-in cursors and feature class management.
- Handles missing or non-nullable fields robustly.
- No pandas or external Python packages required.
