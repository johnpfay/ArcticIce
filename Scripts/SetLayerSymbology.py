import arcpy.mapping as ma 
mxd = ma.MapDocument("CURRENT")
df = ma.ListDataFrames(mxd)[0]
lyrs = ma.ListLayers(mxd,"IceUV*")
for i in range(len(lyrs)): ma.UpdateLayer(df,lyrs[i],lyrs[-1])

