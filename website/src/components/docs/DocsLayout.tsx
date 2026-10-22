import React, { useState } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { DocsSidebar, DOC_SECTIONS } from './DocsSidebar';
import { Menu, X, ChevronRight, ArrowLeft, ArrowRight, Shield } from 'lucide-react';
import { Navbar } from '../layout/Navbar';
import { Footer } from '../layout/Footer';

export const DocsLayout: React.FC = () => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const location = useLocation();

  // Find current item, previous, and next
  const allItems = DOC_SECTIONS.flatMap((s) => s.items);
  const currentIndex = allItems.findIndex((item) =>
    item.path === '/docs' ? location.pathname === '/docs' : location.pathname.startsWith(item.path)
  );

  const currentItem = currentIndex >= 0 ? allItems[currentIndex] : allItems[0];
  const prevItem = currentIndex > 0 ? allItems[currentIndex - 1] : null;
  const nextItem = currentIndex < allItems.length - 1 ? allItems[currentIndex + 1] : null;

  return (
    <div className="min-h-screen flex flex-col bg-[#060913] text-slate-100 font-sans">
      <Navbar />

      <div className="flex-1 flex max-w-7xl w-full mx-auto relative pt-16">
        {/* Mobile toggle button */}
        <div className="lg:hidden fixed bottom-6 right-6 z-40">
          <button
            onClick={() => setMobileSidebarOpen(!mobileSidebarOpen)}
            className="p-3 bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-full shadow-2xl border border-cyan-400/40 flex items-center justify-center cursor-pointer"
            aria-label="Toggle Documentation Sidebar"
          >
            {mobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile sidebar overlay */}
        {mobileSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-30 lg:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
        )}

        {/* Sidebar Container */}
        <div
          className={`fixed lg:sticky top-16 bottom-0 left-0 w-72 z-30 transform transition-transform duration-300 ease-in-out lg:transform-none ${
            mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          <DocsSidebar onCloseMobile={() => setMobileSidebarOpen(false)} />
        </div>

        {/* Main Content Area */}
        <main className="flex-1 min-w-0 px-4 sm:px-8 py-8 lg:px-12 overflow-y-auto">
          {/* Breadcrumbs */}
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-6 pb-3 border-b border-slate-800/60">
            <Link to="/" className="hover:text-cyan-400 transition-colors">
              Home
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <Link to="/docs" className="hover:text-cyan-400 transition-colors">
              Documentation
            </Link>
            {currentItem && currentItem.path !== '/docs' && (
              <>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                <span className="text-cyan-400 font-semibold truncate">{currentItem.label}</span>
              </>
            )}
          </div>

          {/* Page Content */}
          <div className="prose prose-invert max-w-4xl prose-headings:font-bold prose-headings:text-slate-100 prose-a:text-cyan-400 hover:prose-a:text-cyan-300">
            <Outlet />
          </div>

          {/* Next / Previous Page Navigation */}
          <div className="mt-16 pt-8 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 max-w-4xl">
            {prevItem ? (
              <Link
                to={prevItem.path}
                className="w-full sm:w-auto flex items-center gap-3 p-3 rounded-xl border border-slate-800 hover:border-cyan-700/60 bg-[#0a0f1d] hover:bg-[#0e1629] transition-all group"
              >
                <ArrowLeft className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                <div className="text-left">
                  <span className="block text-[10px] uppercase font-mono text-slate-500">Previous</span>
                  <span className="text-xs font-semibold text-slate-300 group-hover:text-cyan-300">{prevItem.label}</span>
                </div>
              </Link>
            ) : <div />}

            {nextItem ? (
              <Link
                to={nextItem.path}
                className="w-full sm:w-auto flex items-center justify-end gap-3 p-3 rounded-xl border border-slate-800 hover:border-cyan-700/60 bg-[#0a0f1d] hover:bg-[#0e1629] transition-all group text-right"
              >
                <div>
                  <span className="block text-[10px] uppercase font-mono text-slate-500">Next Step</span>
                  <span className="text-xs font-semibold text-slate-300 group-hover:text-cyan-300">{nextItem.label}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              </Link>
            ) : <div />}
          </div>
        </main>
      </div>

      <Footer />
    </div>
  );
};
