# StarboundWorldToTiled

# How to Use

# 1. After installing OpenStarbound, run the following commands in-game to extract data:
---------------------------------------------------------------------------------------------------------------------------------------------------------------

- materialIdToName.json

/eval local matList = root.assetsByExtension("material"); local data = { { id = 0, name = "empty" } }; for i = 1, #matList do local asset = root.assetJson(matList[i]); table.insert(data, { id = asset.materialId, name = asset.materialName }); end; table.sort(data, function(a, b) return a.id < b.id end); local result = {}; for i, item in ipairs(data) do local idStr = tostring(item.id); local nameStr = item.name; table.insert(result, string.format('"%s": "%s"', idStr, nameStr)); end; local jsonOutput = "{\n" .. table.concat(result, ",\n") .. "\n}"; return jsonOutput

- modIdToName.json

/eval local matModList = root.assetsByExtension("matmod"); local data = { { id = 0, name = "empty" } }; for i = 1, #matModList do local asset = root.assetJson(matModList[i]); table.insert(data, { id = asset.modId, name = asset.modName }); end; table.sort(data, function(a, b) return a.id < b.id end); local result = {}; for i, item in ipairs(data) do local idStr = tostring(item.id); local nameStr = item.name; table.insert(result, string.format('"%s": "%s"', idStr, nameStr)); end; local jsonOutput = "{\n" .. table.concat(result, ",\n") .. "\n}"; return jsonOutput

- liquidIdToName.json

/eval local liquidList = root.assetsByExtension("liquid"); local data = { { id = 0, name = "empty" } }; for i = 1, #liquidList do local asset = root.assetJson(liquidList[i]); table.insert(data, { id = asset.liquidId, name = asset.name }); end; table.sort(data, function(a, b) return a.id < b.id end); local result = {}; for i, item in ipairs(data) do local idStr = tostring(item.id); local nameStr = item.name; table.insert(result, string.format('"%s": "%s"', idStr, nameStr)); end; local jsonOutput = "{\n" .. table.concat(result, ",\n") .. "\n}"; return jsonOutput

- objNodes.json

/eval local objList = root.assetsByExtension("object"); local result = {}; for i = 1, #objList do local path = objList[i]; local asset = root.assetJson(path); local objectName = asset.objectName or root.assetPathBaseName(path); local entry = {}; local hasData = false; if type(asset.inputNodes) == "table" then for idx, node in pairs(asset.inputNodes) do local key = "i_" .. tostring(idx - 1); entry[key] = { node[1], node[2] }; hasData = true; end; end; if type(asset.outputNodes) == "table" then for idx, node in pairs(asset.outputNodes) do local key = "o_" .. tostring(idx - 1); entry[key] = { node[1], node[2] }; hasData = true; end; end; if hasData then result[objectName] = entry; end; end; return sb.printJson(result, 1)

---------------------------------------------------------------------------------------------------------------------------------------------------------------


# 2. Copy the resulting JSON text from the log file and paste it into the corresponding .json file listed above.


# 3. Finally, open worldToTiledMap.py and update the following variables at the top of the file: 'worldToTiled.py'

'world_name'

'tileset_paths'


# 4. Then you're ready to run the script!


# 5. When you run the script, a JSON file compatible with the 'Tiled' program will be generated using the specified world_name as the file name. Additionally, a generated tileset may also be created if needed.

ex) world_name = "tiled\\packed\\dungeons\\converted\\-925019806_455368771_-28419092_7_2\\-925019806_455368771_-28419092_7_2.world"

Generated Tileset creation completed: tiled\packed\tilesets\generated\-925019806_455368771_-28419092_7_2.json

Converted Tiled Map creation completed: tiled\packed\dungeons\converted\-925019806_455368771_-28419092_7_2\-925019806_455368771_-28419092_7_2.json


