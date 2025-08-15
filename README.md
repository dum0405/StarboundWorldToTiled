# Starbound World Conversion Guide

## 1. Install OpenStarbound
Make sure **OpenStarbound** is installed. After launching the game, run the following commands to extract the tile and wire configurations data.

---------------------------------------------------------------------------------------------------------------------------------------------------------------

- Once you’ve extracted the tile data, you don’t need to run the commands again unless new tiles or objects are added through mods.
/run local t={} local function tableFromAssets(list,keyName) local d={{id=0,name="empty"}} for i=1,#list do local a=root.assetJson(list[i]) table.insert(d,{id=a[keyName],name=a.name or a.materialName or a.modName}) end table.sort(d,function(a,b)return a.id<b.id end) local r={} for _,v in ipairs(d) do r[tostring(v.id)]=v.name end return r end t.material=tableFromAssets(root.assetsByExtension("material"),"materialId") t.mod=tableFromAssets(root.assetsByExtension("matmod"),"modId") t.liquid=tableFromAssets(root.assetsByExtension("liquid"),"liquidId") local o=root.assetsByExtension("object") local w={} for i=1,#o do local p=o[i] local a=root.assetJson(p) local n=a.objectName or root.assetPathBaseName(p) local e={} local h=false if type(a.inputNodes)=="table" then for idx,node in pairs(a.inputNodes) do e["i_"..tostring(idx-1)]={node[1],node[2]} h=true end end if type(a.outputNodes)=="table" then for idx,node in pairs(a.outputNodes) do e["o_"..tostring(idx-1)]={node[1],node[2]} h=true end end if h then w[n]=e end end t.wire=w root.setConfiguration("worldToTiled",t)

- Since the config file will accumulate a large amount of data, run the following command when you no longer need the conversion feature.
/run root.setConfiguration("worldToTiled", {})

---------------------------------------------------------------------------------------------------------------------------------------------------------------

## 2. Run the Python Script **`worldToTiled.py`**
Load the following from your Starbound installation path:

- `storage\starbound.config`
- The **.world** or **.shipworld** file you want to convert
- The required tilesets

Then, set the save locations for:

- Generated tileset
- Tiled Dungeon files

> **Note:**  
> Ensure all paths follow Starbound’s **mod directory structure** to avoid errors.


## License for included libraries

- py-starbound: MIT License (https://github.com/blixt/py-starbound)
- NumPy: BSD 3-Clause License (https://numpy.org)