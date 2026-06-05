// Selective ECharts registration to keep the bundle small.
import {
  BarChart,
  GaugeChart,
  HeatmapChart,
  LineChart,
  PieChart,
} from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  GaugeChart,
  LineChart,
  BarChart,
  PieChart,
  HeatmapChart,
  GridComponent,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

export default echarts;
