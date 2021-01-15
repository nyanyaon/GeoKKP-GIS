<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" labelsEnabled="0" styleCategories="AllStyleCategories" readOnly="0" maxScale="0" version="3.16.2-Hannover" simplifyMaxScale="1" simplifyLocal="1" simplifyDrawingHints="1" simplifyDrawingTol="1" minScale="100000000" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal accumulate="0" startField="" startExpression="" fixedDuration="0" enabled="0" durationField="" endExpression="" endField="" mode="0" durationUnit="min">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" type="singleSymbol">
    <symbols>
      <symbol alpha="1" force_rhr="0" type="fill" name="0" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SimpleFill">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="237,237,237,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.26"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer locked="0" pass="0" enabled="1" class="GeometryGenerator">
          <prop k="SymbolType" v="Line"/>
          <prop k="geometryModifier" v="-- This is a very complex style!!!&#xa;-- The labels are part of the style as&#xa;-- &quot;Font markers&quot;.&#xa;&#xa;segments_to_lines(force_rhr($geometry))"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol alpha="1" force_rhr="0" type="line" name="@0@1" clip_to_extent="1">
            <layer locked="0" pass="0" enabled="1" class="GeometryGenerator">
              <prop k="SymbolType" v="Line"/>
              <prop k="geometryModifier" v="segments_to_lines($geometry)"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
              <symbol alpha="1" force_rhr="0" type="line" name="@@0@1@0" clip_to_extent="1">
                <layer locked="0" pass="0" enabled="1" class="SimpleLine">
                  <prop k="align_dash_pattern" v="0"/>
                  <prop k="capstyle" v="square"/>
                  <prop k="customdash" v="5;2"/>
                  <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="customdash_unit" v="MM"/>
                  <prop k="dash_pattern_offset" v="0"/>
                  <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="dash_pattern_offset_unit" v="MM"/>
                  <prop k="draw_inside_polygon" v="0"/>
                  <prop k="joinstyle" v="bevel"/>
                  <prop k="line_color" v="35,35,35,255"/>
                  <prop k="line_style" v="solid"/>
                  <prop k="line_width" v="0.26"/>
                  <prop k="line_width_unit" v="MM"/>
                  <prop k="offset" v="-3"/>
                  <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_unit" v="MM"/>
                  <prop k="ring_filter" v="0"/>
                  <prop k="tweak_dash_pattern_on_corners" v="0"/>
                  <prop k="use_custom_dash" v="0"/>
                  <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <data_defined_properties>
                    <Option type="Map">
                      <Option value="" type="QString" name="name"/>
                      <Option name="properties"/>
                      <Option value="collection" type="QString" name="type"/>
                    </Option>
                  </data_defined_properties>
                </layer>
                <layer locked="0" pass="0" enabled="1" class="MarkerLine">
                  <prop k="average_angle_length" v="4"/>
                  <prop k="average_angle_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="average_angle_unit" v="MM"/>
                  <prop k="interval" v="3"/>
                  <prop k="interval_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="interval_unit" v="MM"/>
                  <prop k="offset" v="-6"/>
                  <prop k="offset_along_line" v="0"/>
                  <prop k="offset_along_line_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_along_line_unit" v="MM"/>
                  <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_unit" v="MM"/>
                  <prop k="placement" v="centralpoint"/>
                  <prop k="ring_filter" v="0"/>
                  <prop k="rotate" v="1"/>
                  <data_defined_properties>
                    <Option type="Map">
                      <Option value="" type="QString" name="name"/>
                      <Option name="properties"/>
                      <Option value="collection" type="QString" name="type"/>
                    </Option>
                  </data_defined_properties>
                  <symbol alpha="1" force_rhr="0" type="marker" name="@@@0@1@0@1" clip_to_extent="1">
                    <layer locked="0" pass="0" enabled="1" class="FontMarker">
                      <prop k="angle" v="0"/>
                      <prop k="chr" v="A"/>
                      <prop k="color" v="0,0,0,255"/>
                      <prop k="font" v="Arial"/>
                      <prop k="font_style" v="Regular"/>
                      <prop k="horizontal_anchor_point" v="1"/>
                      <prop k="joinstyle" v="bevel"/>
                      <prop k="offset" v="0,0"/>
                      <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="offset_unit" v="MM"/>
                      <prop k="outline_color" v="35,35,35,255"/>
                      <prop k="outline_width" v="0"/>
                      <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="outline_width_unit" v="MM"/>
                      <prop k="size" v="4"/>
                      <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="size_unit" v="MM"/>
                      <prop k="vertical_anchor_point" v="1"/>
                      <data_defined_properties>
                        <Option type="Map">
                          <Option value="" type="QString" name="name"/>
                          <Option type="Map" name="properties">
                            <Option type="Map" name="char">
                              <Option value="true" type="bool" name="active"/>
                              <Option value="if( layer_property(  @layer , 'distance_units')='meters',&#xa;round(length(geometry_n( $geometry, @geometry_part_num)),1)||'m',&#xa;'' -- If layer coordinate unit is NOT meters, don't show labels.&#xa;)" type="QString" name="expression"/>
                              <Option value="3" type="int" name="type"/>
                            </Option>
                          </Option>
                          <Option value="collection" type="QString" name="type"/>
                        </Option>
                      </data_defined_properties>
                    </layer>
                  </symbol>
                </layer>
                <layer locked="0" pass="0" enabled="1" class="MarkerLine">
                  <prop k="average_angle_length" v="4"/>
                  <prop k="average_angle_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="average_angle_unit" v="MM"/>
                  <prop k="interval" v="3"/>
                  <prop k="interval_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="interval_unit" v="MM"/>
                  <prop k="offset" v="-3"/>
                  <prop k="offset_along_line" v="0"/>
                  <prop k="offset_along_line_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_along_line_unit" v="MM"/>
                  <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_unit" v="MM"/>
                  <prop k="placement" v="firstvertex"/>
                  <prop k="ring_filter" v="0"/>
                  <prop k="rotate" v="1"/>
                  <data_defined_properties>
                    <Option type="Map">
                      <Option value="" type="QString" name="name"/>
                      <Option name="properties"/>
                      <Option value="collection" type="QString" name="type"/>
                    </Option>
                  </data_defined_properties>
                  <symbol alpha="1" force_rhr="0" type="marker" name="@@@0@1@0@2" clip_to_extent="1">
                    <layer locked="0" pass="0" enabled="1" class="EllipseMarker">
                      <prop k="angle" v="-90"/>
                      <prop k="color" v="0,0,0,255"/>
                      <prop k="horizontal_anchor_point" v="1"/>
                      <prop k="joinstyle" v="bevel"/>
                      <prop k="offset" v="0,0"/>
                      <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="offset_unit" v="MM"/>
                      <prop k="outline_color" v="35,35,35,255"/>
                      <prop k="outline_style" v="no"/>
                      <prop k="outline_width" v="0"/>
                      <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="outline_width_unit" v="MM"/>
                      <prop k="size" v="3.3"/>
                      <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="size_unit" v="MM"/>
                      <prop k="symbol_height" v="3.3"/>
                      <prop k="symbol_height_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="symbol_height_unit" v="MM"/>
                      <prop k="symbol_name" v="triangle"/>
                      <prop k="symbol_width" v="1.4"/>
                      <prop k="symbol_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="symbol_width_unit" v="MM"/>
                      <prop k="vertical_anchor_point" v="0"/>
                      <data_defined_properties>
                        <Option type="Map">
                          <Option value="" type="QString" name="name"/>
                          <Option name="properties"/>
                          <Option value="collection" type="QString" name="type"/>
                        </Option>
                      </data_defined_properties>
                    </layer>
                  </symbol>
                </layer>
                <layer locked="0" pass="0" enabled="1" class="MarkerLine">
                  <prop k="average_angle_length" v="4"/>
                  <prop k="average_angle_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="average_angle_unit" v="MM"/>
                  <prop k="interval" v="3"/>
                  <prop k="interval_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="interval_unit" v="MM"/>
                  <prop k="offset" v="-3"/>
                  <prop k="offset_along_line" v="0"/>
                  <prop k="offset_along_line_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_along_line_unit" v="MM"/>
                  <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_unit" v="MM"/>
                  <prop k="placement" v="lastvertex"/>
                  <prop k="ring_filter" v="0"/>
                  <prop k="rotate" v="1"/>
                  <data_defined_properties>
                    <Option type="Map">
                      <Option value="" type="QString" name="name"/>
                      <Option name="properties"/>
                      <Option value="collection" type="QString" name="type"/>
                    </Option>
                  </data_defined_properties>
                  <symbol alpha="1" force_rhr="0" type="marker" name="@@@0@1@0@3" clip_to_extent="1">
                    <layer locked="0" pass="0" enabled="1" class="EllipseMarker">
                      <prop k="angle" v="90"/>
                      <prop k="color" v="0,0,0,255"/>
                      <prop k="horizontal_anchor_point" v="1"/>
                      <prop k="joinstyle" v="bevel"/>
                      <prop k="offset" v="0,0"/>
                      <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="offset_unit" v="MM"/>
                      <prop k="outline_color" v="35,35,35,255"/>
                      <prop k="outline_style" v="no"/>
                      <prop k="outline_width" v="0"/>
                      <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="outline_width_unit" v="MM"/>
                      <prop k="size" v="3.3"/>
                      <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="size_unit" v="MM"/>
                      <prop k="symbol_height" v="3.3"/>
                      <prop k="symbol_height_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="symbol_height_unit" v="MM"/>
                      <prop k="symbol_name" v="triangle"/>
                      <prop k="symbol_width" v="1.4"/>
                      <prop k="symbol_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                      <prop k="symbol_width_unit" v="MM"/>
                      <prop k="vertical_anchor_point" v="0"/>
                      <data_defined_properties>
                        <Option type="Map">
                          <Option value="" type="QString" name="name"/>
                          <Option name="properties"/>
                          <Option value="collection" type="QString" name="type"/>
                        </Option>
                      </data_defined_properties>
                    </layer>
                  </symbol>
                </layer>
              </symbol>
            </layer>
            <layer locked="0" pass="0" enabled="1" class="HashLine">
              <prop k="average_angle_length" v="4"/>
              <prop k="average_angle_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="average_angle_unit" v="MM"/>
              <prop k="hash_angle" v="0"/>
              <prop k="hash_length" v="4"/>
              <prop k="hash_length_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="hash_length_unit" v="MM"/>
              <prop k="interval" v="3"/>
              <prop k="interval_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="interval_unit" v="MM"/>
              <prop k="offset" v="-2"/>
              <prop k="offset_along_line" v="0"/>
              <prop k="offset_along_line_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_along_line_unit" v="MM"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="placement" v="lastvertex"/>
              <prop k="ring_filter" v="0"/>
              <prop k="rotate" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
              <symbol alpha="1" force_rhr="0" type="line" name="@@0@1@1" clip_to_extent="1">
                <layer locked="0" pass="0" enabled="1" class="SimpleLine">
                  <prop k="align_dash_pattern" v="0"/>
                  <prop k="capstyle" v="square"/>
                  <prop k="customdash" v="5;2"/>
                  <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="customdash_unit" v="MM"/>
                  <prop k="dash_pattern_offset" v="0"/>
                  <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="dash_pattern_offset_unit" v="MM"/>
                  <prop k="draw_inside_polygon" v="0"/>
                  <prop k="joinstyle" v="bevel"/>
                  <prop k="line_color" v="35,35,35,255"/>
                  <prop k="line_style" v="solid"/>
                  <prop k="line_width" v="0.1"/>
                  <prop k="line_width_unit" v="MM"/>
                  <prop k="offset" v="0"/>
                  <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_unit" v="MM"/>
                  <prop k="ring_filter" v="0"/>
                  <prop k="tweak_dash_pattern_on_corners" v="0"/>
                  <prop k="use_custom_dash" v="0"/>
                  <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <data_defined_properties>
                    <Option type="Map">
                      <Option value="" type="QString" name="name"/>
                      <Option name="properties"/>
                      <Option value="collection" type="QString" name="type"/>
                    </Option>
                  </data_defined_properties>
                </layer>
              </symbol>
            </layer>
            <layer locked="0" pass="0" enabled="1" class="HashLine">
              <prop k="average_angle_length" v="4"/>
              <prop k="average_angle_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="average_angle_unit" v="MM"/>
              <prop k="hash_angle" v="0"/>
              <prop k="hash_length" v="4"/>
              <prop k="hash_length_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="hash_length_unit" v="MM"/>
              <prop k="interval" v="3"/>
              <prop k="interval_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="interval_unit" v="MM"/>
              <prop k="offset" v="-2"/>
              <prop k="offset_along_line" v="0"/>
              <prop k="offset_along_line_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_along_line_unit" v="MM"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="placement" v="firstvertex"/>
              <prop k="ring_filter" v="0"/>
              <prop k="rotate" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
              <symbol alpha="1" force_rhr="0" type="line" name="@@0@1@2" clip_to_extent="1">
                <layer locked="0" pass="0" enabled="1" class="SimpleLine">
                  <prop k="align_dash_pattern" v="0"/>
                  <prop k="capstyle" v="square"/>
                  <prop k="customdash" v="5;2"/>
                  <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="customdash_unit" v="MM"/>
                  <prop k="dash_pattern_offset" v="0"/>
                  <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="dash_pattern_offset_unit" v="MM"/>
                  <prop k="draw_inside_polygon" v="0"/>
                  <prop k="joinstyle" v="bevel"/>
                  <prop k="line_color" v="35,35,35,255"/>
                  <prop k="line_style" v="solid"/>
                  <prop k="line_width" v="0.1"/>
                  <prop k="line_width_unit" v="MM"/>
                  <prop k="offset" v="0"/>
                  <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <prop k="offset_unit" v="MM"/>
                  <prop k="ring_filter" v="0"/>
                  <prop k="tweak_dash_pattern_on_corners" v="0"/>
                  <prop k="use_custom_dash" v="0"/>
                  <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
                  <data_defined_properties>
                    <Option type="Map">
                      <Option value="" type="QString" name="name"/>
                      <Option name="properties"/>
                      <Option value="collection" type="QString" name="type"/>
                    </Option>
                  </data_defined_properties>
                </layer>
              </symbol>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory spacing="5" enabled="0" spacingUnitScale="3x:0,0,0,0,0,0" barWidth="5" height="15" backgroundAlpha="255" penColor="#000000" lineSizeScale="3x:0,0,0,0,0,0" minimumSize="0" direction="0" penAlpha="255" scaleDependency="Area" labelPlacementMethod="XHeight" width="15" backgroundColor="#ffffff" showAxis="1" opacity="1" lineSizeType="MM" spacingUnit="MM" sizeScale="3x:0,0,0,0,0,0" minScaleDenominator="0" diagramOrientation="Up" rotationOffset="270" penWidth="0" scaleBasedVisibility="0" sizeType="MM" maxScaleDenominator="1e+08">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <axisSymbol>
        <symbol alpha="1" force_rhr="0" type="line" name="" clip_to_extent="1">
          <layer locked="0" pass="0" enabled="1" class="SimpleLine">
            <prop k="align_dash_pattern" v="0"/>
            <prop k="capstyle" v="square"/>
            <prop k="customdash" v="5;2"/>
            <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="customdash_unit" v="MM"/>
            <prop k="dash_pattern_offset" v="0"/>
            <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="dash_pattern_offset_unit" v="MM"/>
            <prop k="draw_inside_polygon" v="0"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="line_color" v="35,35,35,255"/>
            <prop k="line_style" v="solid"/>
            <prop k="line_width" v="0.26"/>
            <prop k="line_width_unit" v="MM"/>
            <prop k="offset" v="0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="ring_filter" v="0"/>
            <prop k="tweak_dash_pattern_on_corners" v="0"/>
            <prop k="use_custom_dash" v="0"/>
            <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings showAll="1" linePlacementFlags="18" zIndex="0" obstacle="0" dist="0" placement="1" priority="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration type="Map">
      <Option type="Map" name="QgsGeometryGapCheck">
        <Option value="0" type="double" name="allowedGapsBuffer"/>
        <Option value="false" type="bool" name="allowedGapsEnabled"/>
        <Option value="" type="QString" name="allowedGapsLayer"/>
      </Option>
    </checkConfiguration>
  </geometryOptions>
  <legend type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration/>
  <aliases/>
  <defaults/>
  <constraints/>
  <constraintExpressions/>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column hidden="1" width="-1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable/>
  <labelOnTop/>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression></previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
