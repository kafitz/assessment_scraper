clean_mls_data.sqlite
UPDATE "clean_2005_sales"
SET "land_value_2007" = REPLACE("land_value_2007", ",", ""),
"land_value_2011" = REPLACE("land_value_2011", ",", ""),
"cadastre_area_0" = REPLACE("cadastre_area_0", ",", ""),
"cadastre_area_1" = REPLACE("cadastre_area_1", ",", ""),
"cadastre_area_2" = REPLACE("cadastre_area_2", ",", ""),
"cadastre_area_3" = REPLACE("cadastre_area_3", ",", ""),
"cadastre_area_4" = REPLACE("cadastre_area_4", ",", ""),
"cadastre_area_5" = REPLACE("cadastre_area_5", ",", ""),
"cadastre_area_6" = REPLACE("cadastre_area_6", ",", ""),
"cadastre_area_7" = REPLACE("cadastre_area_7", ",", ""),
"cadastre_area_8" = REPLACE("cadastre_area_8", ",", ""),
"cadastre_area_9" = REPLACE("cadastre_area_9", ",", ""),
"total_property_value_2007" = REPLACE("total_property_value_2007", ",", ""),
"total_property_value_2011" = REPLACE("total_property_value_2011", ",", ""),
"building_value_2007" = REPLACE("building_value_2007", ",", ""),
"building_value_2011" = REPLACE("building_value_2011", ",", "")
"price_sold_1" = REPLACE("price_sold_1", ",", "")
"price_sold_2" = REPLACE("price_sold_2", ",", "")
"price_sold_3" = REPLACE("price_sold_3", ",", "")

2005_distmatrix.sqlite
UPDATE "2005_distmatrix"
SET "land_value_2007" = REPLACE("land_value_2007", ",", ""),
"land_value_2011" = REPLACE("land_value_2011", ",", ""),
"total_property_value_2007" = REPLACE("total_property_value_2007", ",", ""),
"total_property_value_2011" = REPLACE("total_property_value_2011", ",", ""),
"building_value_2007" = REPLACE("building_value_2007", ",", ""),
"building_value_2011" = REPLACE("building_value_2011", ",", ""),
"price_sold_1" = REPLACE("price_sold_1", ",", ""),
"price_sold_2" = REPLACE("price_sold_2", ",", ""),
"price_sold_3" = REPLACE("price_sold_3", ",", "")

UPDATE "2005_distmatrix"
SET "id" = REPLACE("id", '"', ''),
"input_search" = REPLACE("input_search", '"', ''),
"geocoded_arrondissement" = REPLACE("geocoded_arrondissement", '"', ''),
"id_uef" = REPLACE("id_uef", '"', ''),
"address" = REPLACE("address", '"', ''),
"neighborhood" = REPLACE("neighborhood", '"', ''),
"year_built" = REPLACE("year_built", '"', ''),
"property_code" = REPLACE("property_code", '"', ''),
"start_address" = REPLACE("start_address", '"', ''),
"end_address" = REPLACE("end_address", '"', ''),
"lot_area" = REPLACE("lot_area", '"', ''),
"role_year" = REPLACE("role_year", '"', ''),
"building_value_2007" = REPLACE("building_value_2007", '"', ''),
"land_value_2007" = REPLACE("land_value_2007", '"', ''),
"total_property_value_2007" = REPLACE("total_property_value_2007", '"', ''),
"building_value_2011" = REPLACE("building_value_2007", '"', ''),
"land_value_2011" = REPLACE("land_value_2007", '"', ''),
"total_property_value_2011" = REPLACE("total_property_value_2007", '"', ''),
"date_sold_1" = REPLACE("date_sold_1", '"', ''),
"price_sold_1" = REPLACE("price_sold_1", '"', ''),
"date_sold_2" = REPLACE("date_sold_2", '"', ''),
"price_sold_2" = REPLACE("price_sold_2", '"', ''),
"date_sold_3" = REPLACE("date_sold_3", '"', ''),
"price_sold_3" = REPLACE("price_sold_3", '"', ''),
"latitude" = REPLACE("latitude", '"', ''),
"longitude" = REPLACE("longitude", '"', ''),
"targetid" = REPLACE("targetid", '"', ''),
"distance" = REPLACE("distance", '"', '')