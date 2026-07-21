# 使用示例

## 基础示例

### 矢量分析

```
用户：对 C:/data/roads.shp 做 500 米缓冲区分析
AI 调用：analysis_Buffer(in_features="C:/data/roads.shp", out_feature_class="C:/results/roads_buf.shp", buffer_distance_or_field="500 meters")
```

```
用户：把 roads.shp 和 rivers.shp 做相交分析
AI 调用：analysis_Intersect(in_features=["C:/data/roads.shp", "C:/data/rivers.shp"], out_feature_class="C:/results/intersection.shp")
```

```
用户：从 buildings.shp 中删除 rivers_buffer.shp 覆盖的部分
AI 调用：analysis_Erase(in_features="C:/data/buildings.shp", erase_features="C:/results/rivers_buffer.shp", out_feature_class="C:/results/building_clean.shp")
```

### 栅格分析

```
用户：计算 DEM 的坡度和坡向
AI 调用：
  ddd_Slope(in_raster="C:/data/dem.tif", out_raster="C:/results/slope.tif")
  ddd_Aspect(in_raster="C:/data/dem.tif", out_raster="C:/results/aspect.tif")
```

```
用户：对 DEM 做重分类，把坡度小于5度的设为1，大于等于5度的设为0
AI 调用：sa_Reclassify(in_raster="C:/results/slope.tif", reclass_field="Value", remap="0 5 1;5 90 0", out_raster="C:/results/slope_reclass.tif")
```

```
用户：提取 DEM 的等高线，间距 20 米
AI 调用：ddd_Contour(in_raster="C:/data/dem.tif", out_polyline_features="C:/results/contours.shp", contour_interval=20)
```

### 空间统计

```
用户：分析 crimes.shp 的 Incident_C 字段空间自相关
AI 调用：stats_SpatialAutocorrelation(Input_Feature_Class="C:/data/crimes.shp", Input_Field="Incident_C", Conceptualization_of_Spatial_Relationships="FIXED_DISTANCE_BAND")
```

```
用户：对 crimes.shp 做热点分析
AI 调用：stats_HotSpots(Input_Feature_Class="C:/data/crimes.shp", Input_Field="Incident_C", Output_Feature_Class="C:/results/hotspot.shp")
```

### 地统计分析

```
用户：对 air_quality.shp 的 PM25 字段做 Kriging 插值
AI 调用：ga_Kriging(in_features="C:/data/air_quality.shp", z_field="PM25", out_surface_raster="C:/results/kriging_pm25.tif")
```

```
用户：对同样的数据做 IDW 插值，对比效果
AI 调用：ga_Idw(in_features="C:/data/air_quality.shp", z_field="PM25", out_surface_raster="C:/results/idw_pm25.tif", power=2)
```

### 数据管理

```
用户：把 roads.shp 投影到 WGS84 Web Mercator
AI 调用：management_Project(in_dataset="C:/data/roads.shp", out_dataset="C:/results/roads_3857.shp", out_coor_system=3857)
```

```
用户：给 buildings.shp 添加一个 area 字段并计算面积
AI 调用：
  management_AddField(in_table="C:/data/buildings.shp", field_name="area", field_type="DOUBLE")
  management_CalculateField(in_table="C:/data/buildings.shp", field="area", expression="!shape.area!", expression_type="PYTHON3")
```

## 复合分析示例

### 选址分析
```
用户：找一个适合建医院的区域，离主干道500m内，离居民区1000m内，坡度小于5度
AI 自动执行：
  1. analysis_Buffer(roads.shp, buffer_500m.shp, "500 meters")
  2. analysis_Buffer(residential.shp, buffer_1000m.shp, "1000 meters")
  3. ddd_Slope(dem.tif, slope.tif)
  4. sa_Reclassify(slope.tif, slope_reclass.tif, "0 5 1;5 90 0")
  5. analysis_Intersect([buffer_500m.shp, buffer_1000m.shp, slope_reclass.tif], candidates.shp)
```

### 三维可视域分析
```
用户：找到 100 个候选观测点中视野最好的那个
AI 自动执行：
  1. 生成 100 个规则网格点
  2. ddd_Viewshed2(dem.tif, observers.shp, viewshed.tif)
  3. 统计每个观测点的可视面积
  4. 排序返回 TOP 3 最佳位置
```

## 错误处理示例

```
用户：对 nonexistent.shp 做缓冲区
AI 调用：analysis_Buffer → 返回 ERROR 000732
AI 回复：数据集 nonexistent.shp 不存在。当前数据目录中有 roads.shp, buildings.shp, rivers.shp，请问你想用哪个？
```
