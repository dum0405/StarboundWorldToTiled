# StarboundWorldToTiled

# How to Use

# 1. After installing OpenStarbound, run the following commands in-game to extract tile data:
---------------------------------------------------------------------------------------------------------------------------------------------------------------

/run local t={} local function tableFromAssets(list,keyName) local d={{id=0,name="empty"}} for i=1,#list do local a=root.assetJson(list[i]) table.insert(d,{id=a[keyName],name=a.name or a.materialName or a.modName}) end table.sort(d,function(a,b)return a.id<b.id end) local r={} for _,v in ipairs(d) do r[tostring(v.id)]=v.name end return r end t.material=tableFromAssets(root.assetsByExtension("material"),"materialId") t.mod=tableFromAssets(root.assetsByExtension("matmod"),"modId") t.liquid=tableFromAssets(root.assetsByExtension("liquid"),"liquidId") local o=root.assetsByExtension("object") local w={} for i=1,#o do local p=o[i] local a=root.assetJson(p) local n=a.objectName or root.assetPathBaseName(p) local e={} local h=false if type(a.inputNodes)=="table" then for idx,node in pairs(a.inputNodes) do e["i_"..tostring(idx-1)]={node[1],node[2]} h=true end end if type(a.outputNodes)=="table" then for idx,node in pairs(a.outputNodes) do e["o_"..tostring(idx-1)]={node[1],node[2]} h=true end end if h then w[n]=e end end t.wire=w root.setConfiguration("worldToTiled",t)

/run root.setConfiguration("worldToTiled", {})

---------------------------------------------------------------------------------------------------------------------------------------------------------------

## License for included libraries

- py-starbound: MIT License (https://github.com/blixt/py-starbound)
- NumPy: BSD 3-Clause License (https://numpy.org)