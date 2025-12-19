import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis as _PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  Scatter,
  ScatterChart,
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';

const PolarAngleAxis = _PolarAngleAxis as unknown as any;

export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: any;
}

export interface ChartConfig {
  type: 'line' | 'area' | 'bar' | 'pie' | 'radar' | 'scatter' | 'composed';
  data: ChartDataPoint[];
  xAxis?: string;
  yAxis?: string;
  colors?: string[];
  title?: string;
  subtitle?: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  animate?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const EnhancedCharts: React.FC<ChartConfig> = ({
  type,
  data,
  xAxis = 'name',
  yAxis = 'value',
  colors = COLORS,
  title,
  subtitle,
  height = 400,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  animate = true,
}) => {

  const renderChart = () => {
    const commonProps = {
      data,
      height,
      margin: { top: 20, right: 30, left: 20, bottom: 5 },
    };

    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={xAxis} />
            <YAxis />
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
            {Object.keys(data[0] || {}).filter(key => key !== xAxis).map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={{ fill: colors[index % colors.length], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
                animationDuration={animate ? 1000 : 0}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={xAxis} />
            <YAxis />
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
            {Object.keys(data[0] || {}).filter(key => key !== xAxis).map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[index % colors.length]}
                fill={colors[index % colors.length]}
                fillOpacity={0.3}
                animationDuration={animate ? 1000 : 0}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={xAxis} />
            <YAxis />
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
            {Object.keys(data[0] || {}).filter(key => key !== xAxis).map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[index % colors.length]}
                animationDuration={animate ? 1000 : 0}
              />
            ))}
          </BarChart>
        );

      case 'pie':
        return (
          <PieChart {...commonProps}>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey={yAxis}
              animationDuration={animate ? 1000 : 0}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
          </PieChart>
        );

      case 'radar':
        return (
          <RadarChart {...commonProps}>
            <PolarGrid />
            <PolarAngleAxis dataKey={xAxis} />
            <PolarRadiusAxis />
            {Object.keys(data[0] || {}).filter(key => key !== xAxis).map((key, index) => (
              <Radar
                key={key}
                name={key}
                dataKey={key}
                stroke={colors[index % colors.length]}
                fill={colors[index % colors.length]}
                fillOpacity={0.3}
                animationDuration={animate ? 1000 : 0}
              />
            ))}
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
          </RadarChart>
        );

      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            {showGrid && <CartesianGrid />}
            <XAxis type="number" dataKey={xAxis} name={xAxis} />
            <YAxis type="number" dataKey={yAxis} name={yAxis} />
            {showTooltip && <Tooltip cursor={{ strokeDasharray: '3 3' }} />}
            {showLegend && <Legend />}
            {Object.keys(data[0] || {}).filter(key => key !== xAxis && key !== yAxis).map((key, index) => (
              <Scatter
                key={key}
                name={key}
                dataKey={key}
                fill={colors[index % colors.length]}
                animationDuration={animate ? 1000 : 0}
              />
            ))}
          </ScatterChart>
        );

      case 'composed':
        return (
          <ComposedChart {...commonProps}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={xAxis} />
            <YAxis />
            {showTooltip && <Tooltip />}
            {showLegend && <Legend />}
            {Object.keys(data[0] || {}).filter(key => key !== xAxis).map((key, index) => {
              if (key.includes('bar')) {
                return (
                  <Bar
                    key={key}
                    dataKey={key}
                    fill={colors[index % colors.length]}
                    animationDuration={animate ? 1000 : 0}
                  />
                );
              } else if (key.includes('line')) {
                return (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={colors[index % colors.length]}
                    strokeWidth={2}
                    animationDuration={animate ? 1000 : 0}
                  />
                );
              } else {
                return (
                  <Area
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={colors[index % colors.length]}
                    fill={colors[index % colors.length]}
                    fillOpacity={0.3}
                    animationDuration={animate ? 1000 : 0}
                  />
                );
              }
            })}
          </ComposedChart>
        );

      default:
        return <Typography>Unsupported chart type</Typography>;
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      {(title || subtitle) && (
        <Box sx={{ mb: 2 }}>
          {title && (
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
          )}
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        {renderChart()}
      </ResponsiveContainer>
    </Paper>
  );
};

// Specialized chart components
export const LineChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="line" />
);

export const AreaChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="area" />
);

export const BarChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="bar" />
);

export const PieChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="pie" />
);

export const RadarChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="radar" />
);

export const ScatterChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="scatter" />
);

export const ComposedChartComponent: React.FC<Omit<ChartConfig, 'type'>> = (props) => (
  <EnhancedCharts {...props} type="composed" />
);

export default EnhancedCharts;

