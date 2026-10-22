import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { DocsLayout } from './components/docs/DocsLayout';
import { DocsOverviewPage } from './pages/docs/DocsOverviewPage';
import { QuickstartPage } from './pages/docs/QuickstartPage';
import { ArchitectureDocsPage } from './pages/docs/ArchitectureDocsPage';
import { WindowsInstallPage } from './pages/docs/WindowsInstallPage';
import { LinuxInstallPage } from './pages/docs/LinuxInstallPage';
import { MacInstallPage } from './pages/docs/MacInstallPage';
import { ManualInstallPage } from './pages/docs/ManualInstallPage';
import { EnvVarsPage } from './pages/docs/EnvVarsPage';
import { DockerServicesPage } from './pages/docs/DockerServicesPage';
import { ApiReferencePage } from './pages/docs/ApiReferencePage';
import { ModelPerformanceDocsPage } from './pages/docs/ModelPerformanceDocsPage';
import { VercelDeploymentPage } from './pages/docs/VercelDeploymentPage';
import { TroubleshootingPage } from './pages/docs/TroubleshootingPage';
import { MaintenancePage } from './pages/docs/MaintenancePage';
import { ContributingPage } from './pages/docs/ContributingPage';

export default function App() {
  return (
    <HashRouter>
      <Routes>
        {/* Public Landing Website */}
        <Route path="/" element={<HomePage />} />

        {/* Dedicated Documentation Portal */}
        <Route path="/docs" element={<DocsLayout />}>
          <Route index element={<DocsOverviewPage />} />
          <Route path="quickstart" element={<QuickstartPage />} />
          <Route path="architecture" element={<ArchitectureDocsPage />} />

          {/* OS Installation Guides */}
          <Route path="installation/windows" element={<WindowsInstallPage />} />
          <Route path="installation/linux" element={<LinuxInstallPage />} />
          <Route path="installation/macos" element={<MacInstallPage />} />
          <Route path="installation/manual" element={<ManualInstallPage />} />

          {/* Configuration & Topology */}
          <Route path="configuration/env-vars" element={<EnvVarsPage />} />
          <Route path="configuration/docker-services" element={<DockerServicesPage />} />
          <Route path="configuration/vercel-deployment" element={<VercelDeploymentPage />} />

          {/* Model Performance & Empirical Testing */}
          <Route path="model-performance" element={<ModelPerformanceDocsPage />} />

          {/* API Reference */}
          <Route path="api" element={<ApiReferencePage />} />

          {/* Operations & Community */}
          <Route path="troubleshooting" element={<TroubleshootingPage />} />
          <Route path="maintenance" element={<MaintenancePage />} />
          <Route path="contributing" element={<ContributingPage />} />
        </Route>

        {/* Catch-all redirect to Home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
