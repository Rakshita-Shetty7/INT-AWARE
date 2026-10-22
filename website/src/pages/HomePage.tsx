import React from 'react';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';
import { Hero } from '../components/home/Hero';
import { ProblemSolution } from '../components/home/ProblemSolution';
import { FeaturesGrid } from '../components/home/FeaturesGrid';
import { InteractiveArchitecture } from '../components/home/InteractiveArchitecture';
import { ProjectDemoSection } from '../components/home/ProjectDemoSection';
import { LiveMetricsHonesty } from '../components/home/LiveMetricsHonesty';
import { TechStackSection } from '../components/home/TechStackSection';
import { QuickstartPreview } from '../components/home/QuickstartPreview';

export const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#060913] text-slate-100 font-sans">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <ProblemSolution />
        <FeaturesGrid />
        <InteractiveArchitecture />
        <ProjectDemoSection />
        <LiveMetricsHonesty />
        <TechStackSection />
        <QuickstartPreview />
      </main>
      <Footer />
    </div>
  );
};
