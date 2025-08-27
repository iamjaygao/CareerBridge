import React, { useEffect, useState } from 'react';
import { Box, Paper, Typography, LinearProgress } from '@mui/material';

interface PerformanceMetrics {
  fps: number;
  memory: number;
  loadTime: number;
  renderTime: number;
}

const PerformanceMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 0,
    memory: 0,
    loadTime: 0,
    renderTime: 0,
  });
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Only show in development
    if (process.env.NODE_ENV === 'development') {
      setIsVisible(true);
      startMonitoring();
    }
  }, []);

  const startMonitoring = () => {
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

    const measureMemory = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const usedMemory = Math.round(memory.usedJSHeapSize / 1024 / 1024);
        setMetrics(prev => ({ ...prev, memory: usedMemory }));
      }
    };

    const measureLoadTime = () => {
      const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
      setMetrics(prev => ({ ...prev, loadTime }));
    };

    // Start measurements
    measureFPS();
    setInterval(measureMemory, 1000);
    
    if (document.readyState === 'complete') {
      measureLoadTime();
    } else {
      window.addEventListener('load', measureLoadTime);
    }

    // Measure render time
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'measure') {
          setMetrics(prev => ({ ...prev, renderTime: Math.round(entry.duration) }));
        }
      }
    });
    observer.observe({ entryTypes: ['measure'] });
  };

  if (!isVisible) return null;

  const getFPSColor = (fps: number) => {
    if (fps >= 55) return 'success.main';
    if (fps >= 30) return 'warning.main';
    return 'error.main';
  };

  const getMemoryColor = (memory: number) => {
    if (memory < 50) return 'success.main';
    if (memory < 100) return 'warning.main';
    return 'error.main';
  };

  return (
    <Paper
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        p: 2,
        minWidth: 200,
        zIndex: 9999,
        bgcolor: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
      }}
    >
      <Typography variant="caption" sx={{ color: 'grey.300', mb: 1, display: 'block' }}>
        Performance Monitor
      </Typography>
      
      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption">FPS</Typography>
          <Typography variant="caption" sx={{ color: getFPSColor(metrics.fps) }}>
            {metrics.fps}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={(Math.min(metrics.fps, 60) / 60) * 100}
          sx={{
            height: 4,
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              bgcolor: getFPSColor(metrics.fps),
            },
          }}
        />
      </Box>

      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption">Memory</Typography>
          <Typography variant="caption" sx={{ color: getMemoryColor(metrics.memory) }}>
            {metrics.memory}MB
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={(Math.min(metrics.memory, 200) / 200) * 100}
          sx={{
            height: 4,
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              bgcolor: getMemoryColor(metrics.memory),
            },
          }}
        />
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
        <Typography variant="caption">Load: {metrics.loadTime}ms</Typography>
        <Typography variant="caption">Render: {metrics.renderTime}ms</Typography>
      </Box>
    </Paper>
  );
};

export default PerformanceMonitor; 