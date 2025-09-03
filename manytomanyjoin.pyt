import arcpy
import os
import math

class ManyToManyJoinTool(object):
    def __init__(self):
        self.label = "Many to Many Join"
        self.description = "Joins two feature layers or tables on a many-to-many relationship, keeping all fields and data."
        self.canRunInBackground = False

    def getParameterInfo(self):
        params = [
            arcpy.Parameter(
                displayName="Target Feature Layer",
                name="target_layer",
                datatype=["GPFeatureLayer"],
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Join Layer/Table",
                name="join_layer",
                datatype=["GPFeatureLayer", "GPTableView"],
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Feature Class",
                name="output_dataset",
                datatype=["DEFeatureClass"],
                parameterType="Required",
                direction="Output"
            ),
            arcpy.Parameter(
                displayName="Target Field",
                name="target_field",
                datatype="Field",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Join Field",
                name="join_field",
                datatype="Field",
                parameterType="Required",
                direction="Input"
            )
        ]
        params[3].parameterDependencies = ["target_layer"]
        params[4].parameterDependencies = ["join_layer"]
        return params

    def updateParameters(self, parameters):
        if parameters[0].altered and not parameters[2].altered:
            target_path = parameters[0].valueAsText
            if target_path:
                if os.path.exists(target_path):
                    target_name = os.path.splitext(os.path.basename(target_path))[0]
                else:
                    target_name = target_path.split("\\")[-1].split("/")[-1]
                try:
                    aprx = arcpy.mp.ArcGISProject("CURRENT")
                    default_gdb = aprx.defaultGeodatabase
                except Exception:
                    default_gdb = arcpy.env.defaultGDB
                if default_gdb:
                    out_name = f"{target_name}_join"
                    parameters[2].value = os.path.join(default_gdb, out_name)
        return

    def execute(self, parameters, messages):
        target_layer = parameters[0].valueAsText
        join_layer = parameters[1].valueAsText
        output_dataset = parameters[2].valueAsText
        target_field = parameters[3].valueAsText
        join_field = parameters[4].valueAsText

        temp_target = os.path.join(arcpy.env.scratchGDB, "temp_target")
        temp_join = os.path.join(arcpy.env.scratchGDB, "temp_join")
        if arcpy.Exists(temp_target):
            arcpy.Delete_management(temp_target)
        if arcpy.Exists(temp_join):
            arcpy.Delete_management(temp_join)
        arcpy.CopyFeatures_management(target_layer, temp_target)  
        arcpy.CopyRows_management(join_layer, temp_join)

        target_desc = arcpy.Describe(temp_target)

        join_records = []
        join_fields = [f.name for f in arcpy.ListFields(temp_join) if f.type not in ('OID', 'Geometry', 'Raster', 'Blob')]
        join_fields_full = join_fields.copy()
        if join_field not in join_fields:
            join_fields.append(join_field)
        with arcpy.da.SearchCursor(temp_join, join_fields) as cursor:
            for row in cursor:
                join_records.append(dict(zip(join_fields, row)))
        join_map = {}
        for rec in join_records:
            key = str(rec[join_field])
            join_map.setdefault(key, []).append(rec)

        target_fields = [f.name for f in arcpy.ListFields(temp_target) if f.type not in ('OID', 'Geometry', 'Raster', 'Blob')]
        out_fields = target_fields + [f for f in join_fields_full if f != join_field] + ['SHAPE@']

        sr = target_desc.spatialReference
        arcpy.CreateFeatureclass_management(os.path.dirname(output_dataset), os.path.basename(output_dataset), target_desc.shapeType, spatial_reference=sr)
        for f in arcpy.ListFields(temp_target):
            if f.type not in ('OID', 'Geometry') and not f.name.upper().startswith('OID') and not f.name.upper().startswith('FID'):
                arcpy.AddField_management(output_dataset, f.name, f.type, f.precision, f.scale, f.length)
        for f in arcpy.ListFields(temp_join):
            if f.type not in ('OID', 'Geometry') and not f.name.upper().startswith('OID') and not f.name.upper().startswith('FID') and f.name != join_field:
                arcpy.AddField_management(output_dataset, f.name, f.type, f.precision, f.scale, f.length)

        field_info = {f.name: {'type': f.type, 'nullable': f.isNullable} for f in arcpy.ListFields(output_dataset)}
        with arcpy.da.SearchCursor(temp_target, target_fields + [target_field, 'SHAPE@']) as t_cursor, \
             arcpy.da.InsertCursor(output_dataset, out_fields) as i_cursor:
            for t_row in t_cursor:
                t_dict = dict(zip(target_fields + [target_field, 'SHAPE@'], t_row))
                t_key = str(t_dict[target_field])
                if t_key in join_map:
                    for j_dict in join_map[t_key]:
                        out_row = [t_dict[f] for f in target_fields]
                        out_row += [j_dict.get(f, None) for f in join_fields_full if f != join_field]
                        out_row.append(t_dict['SHAPE@'])
                        for idx, f in enumerate(out_fields):
                            v = out_row[idx]
                            info = field_info.get(f, {})
                            dtype = info.get('type', 'Unknown')
                            if dtype == 'String' and v is not None and not isinstance(v, str):
                                out_row[idx] = str(v)
                            if v is None and f != 'SHAPE@':
                                if dtype == 'String':
                                    out_row[idx] = '' if not info.get('nullable', True) else None
                                elif dtype in ('Integer', 'SmallInteger', 'Long', 'Short'):
                                    out_row[idx] = 0 if not info.get('nullable', True) else None
                                elif dtype in ('Double', 'Single', 'Float'):
                                    out_row[idx] = 0.0 if not info.get('nullable', True) else None
                                elif dtype == 'Date':
                                    out_row[idx] = None
                                else:
                                    out_row[idx] = None
                            elif dtype in ('Integer', 'SmallInteger', 'Long', 'Short') and v is not None:
                                try:
                                    out_row[idx] = int(v)
                                except (ValueError, TypeError):
                                    out_row[idx] = 0
                            elif dtype in ('Double', 'Single', 'Float') and v is not None:
                                try:
                                    out_row[idx] = float(v)
                                except (ValueError, TypeError):
                                    out_row[idx] = 0.0
                        skip_row = any(out_row[idx] is None and f != 'SHAPE@' and not field_info.get(f, {}).get('nullable', True) for idx, f in enumerate(out_fields))
                        if out_row[-1] is not None and not skip_row:
                            i_cursor.insertRow(out_row)
                        else:
                            messages.addWarningMessage(f"Skipped row due to missing required value: {out_row}")

        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            m = aprx.activeMap
            m.addDataFromPath(output_dataset)
            messages.addMessage(f"Output feature class added to map: {output_dataset}")
        except Exception as e:
            messages.addWarningMessage(f"Could not add output to map: {e}")

        messages.addMessage(f"Many-to-many join completed (arcpy-only). Output: {output_dataset}")

class Toolbox(object):
    def __init__(self):
        self.label = "Custom Tools"
        self.alias = "customtools"
        self.tools = [ManyToManyJoinTool]