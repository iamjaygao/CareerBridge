import React, { useEffect, useState } from 'react';
import { Box, Typography, Chip } from '@mui/material';

interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  memoryUsage: number;
  fps: number;
}

const PerformanceMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    fps: 0,
  });

  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    const measurePerformance = () => {
      // Measure page load time
      const loadTime = performance.now();
      
      // Measure memory usage (if available)
      const memoryUsage = (performance as any).memory 
        ? Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024)
        : 0;

      // Measure render time
      const renderStart = performance.now();
      requestAnimationFrame(() => {
        const renderTime = performance.now() - renderStart;
        setMetrics(prev => ({
          ...prev,
          loadTime,
          renderTime,
          memoryUsage,
        }));
      });
    };

    // Measure FPS
    let frameCount = 0;
    let lastTime = performance.now();
    
    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
        setMetrics(prev => ({ ...prev, fps }));
        frameCount = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(measureFPS);
    };

    measurePerformance();
    measureFPS();

    // Update metrics every 5 seconds
    const interval = setInterval(measurePerformance, 5000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // Only render in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        zIndex: 9999,
        bgcolor: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        p: 1,
        borderRadius: 1,
        fontSize: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
      }}
    >
      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
        Performance Monitor
      </Typography>
      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
        <Chip
          label={`FPS: ${metrics.fps}`}
          size="small"
          color={metrics.fps > 50 ? 'success' : metrics.fps > 30 ? 'warning' : 'error'}
          sx={{ height: 20, fontSize: '0.7rem' }}
        />
        <Chip
          label={`Memory: ${metrics.memoryUsage}MB`}
          size="small"
          color={metrics.memoryUsage < 100 ? 'success' : metrics.memoryUsage < 200 ? 'warning' : 'error'}
          sx={{ height: 20, fontSize: '0.7rem' }}
        />
        <Chip
          label={`Load: ${Math.round(metrics.loadTime)}ms`}
          size="small"
          color="info"
          sx={{ height: 20, fontSize: '0.7rem' }}
        />
      </Box>
    </Box>
  );
};

export default PerformanceMonitor; 