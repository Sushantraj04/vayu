import React from 'react';
import { 
  FileText, 
  ExternalLink, 
  Code2, 
  ShieldCheck, 
  Layers, 
  Share2, 
  Terminal,
  BookOpen
} from 'lucide-react';

export const DocsView: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
        <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-brand-600 dark:text-brand-400" />
          <span>VAYU-NET Digital Public Good (DPG) Documentation</span>
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Standards compliance, OpenAPI specifications, and multi-jurisdiction adoption guide for BRICS nations.
        </p>
      </div>

      {/* Quick Links Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-brand-500 transition-all shadow-xs group block"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400">
                <Code2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-brand-600">
                  Interactive OpenAPI Specification (Swagger)
                </h3>
                <span className="text-[11px] text-slate-500 font-mono">/docs</span>
              </div>
            </div>
            <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-brand-500" />
          </div>
          <p className="text-xs text-slate-500 mt-3 leading-relaxed">
            Full REST API documentation with automated request payloads, Bearer JWT auth, and live endpoints testing.
          </p>
        </a>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-2">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400">
              <Share2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                Federated Node Onboarding Guide
              </h3>
              <span className="text-[11px] text-slate-500 font-mono">docs/FEDERATED_ONBOARDING.md</span>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-3 leading-relaxed">
            Step-by-step instructions for municipal departments to connect an isolated PyTorch air node to the network.
          </p>
        </div>
      </div>

      {/* Digital Public Good Standard Check */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Digital Public Good (DPG) Standard Checklist</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 flex items-start gap-2.5">
            <span className="text-emerald-500 font-bold">✓</span>
            <div>
              <strong className="text-slate-900 dark:text-white">Open Standards:</strong>
              <p className="text-slate-500 text-[11px] mt-0.5">OASIS Common Alerting Protocol (CAP 1.2) XML/JSON export compliant.</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 flex items-start gap-2.5">
            <span className="text-emerald-500 font-bold">✓</span>
            <div>
              <strong className="text-slate-900 dark:text-white">Privacy by Design:</strong>
              <p className="text-slate-500 text-[11px] mt-0.5">EXIF location metadata stripped; 500m coordinate jittering for public anonymity.</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 flex items-start gap-2.5">
            <span className="text-emerald-500 font-bold">✓</span>
            <div>
              <strong className="text-slate-900 dark:text-white">Zero Synthetic Data:</strong>
              <p className="text-slate-500 text-[11px] mt-0.5">Strict truthfulness in UI. Modelled vs measured telemetry labeled with integrity.</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 flex items-start gap-2.5">
            <span className="text-emerald-500 font-bold">✓</span>
            <div>
              <strong className="text-slate-900 dark:text-white">Config-Driven Extensibility:</strong>
              <p className="text-slate-500 text-[11px] mt-0.5">Any city or nation can define their corridor in YAML without code modifications.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
