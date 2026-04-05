import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import SOCPage from './pages/SOCPage';
import HeatmapPage from './pages/HeatmapPage';
import ForecastPage from './pages/ForecastPage';
import DocsPage from './pages/DocsPage';
import PlaceholderPage from './pages/PlaceholderPage';
import TechGuideModulesPage from './pages/TechGuideModulesPage';
import ArchitectureGuidePage from './pages/ArchitectureGuidePage';

import RunScanPage from './pages/RunScanPage';
import ScanResultsPage from './pages/ScanResultsPage';
import AssetManagementPage from './pages/AssetManagementPage';
import CBOMRecordsPage from './pages/CBOMRecordsPage';
import RiskAnalysisPage from './pages/RiskAnalysisPage';
import PQCClassificationPage from './pages/PQCClassificationPage';
import CyberRatingPage from './pages/CyberRatingPage';
import ReportsPage from './pages/ReportsPage';
import UserManagementPage from './pages/UserManagementPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  // Simple auth check simulation (could be expanded)
  const isAuthenticated = true; 

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="scan" element={<RunScanPage />} />
        <Route path="results" element={<ScanResultsPage />} />
        <Route path="assets" element={<AssetManagementPage />} />
        <Route path="cbom" element={<CBOMRecordsPage />} />
        <Route path="risk" element={<RiskAnalysisPage />} />
        <Route path="pqc" element={<PQCClassificationPage />} />
        <Route path="cyber-rating" element={<CyberRatingPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="users" element={<UserManagementPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="soc" element={<SOCPage />} />
        <Route path="heatmap" element={<HeatmapPage />} />
        <Route path="forecast" element={<ForecastPage />} />
        <Route path="docs" element={<DocsPage />} />
        <Route path="tech-guide" element={<TechGuideModulesPage />} />
        <Route path="architecture" element={<ArchitectureGuidePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
