import { useState } from 'react';
import { HelpCircle, X, BrainCircuit, Activity, CalendarCheck, CheckCircle2, RotateCcw } from 'lucide-react';

export function HowChronOSWorks() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-1.5 text-xs font-medium text-[#7A7771] hover:text-[#2C2B29] transition-colors"
      >
        <HelpCircle className="w-4 h-4" />
        How ChronOS works
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-[#FAF9F6] border border-[#E5E0D8] rounded-2xl shadow-xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-[#E5E0D8] bg-white">
              <h3 className="text-lg font-bold text-[#2C2B29]">How ChronOS Works</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-[#7A7771] hover:text-[#2C2B29] rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex gap-4 items-start">
                <div className="p-2 bg-[#E5E0D8] rounded-lg text-[#2C2B29] mt-0.5"><BrainCircuit className="w-5 h-5" /></div>
                <div>
                  <h4 className="font-semibold text-[#2C2B29]">1. Brain Dump</h4>
                  <p className="text-sm text-[#5C5A56] mt-1">Paste your messy commitments into the Inbox. ChronOS extracts structured deadlines and effort.</p>
                </div>
              </div>
              
              <div className="flex gap-4 items-start">
                <div className="p-2 bg-[#F0EBE1] rounded-lg text-[#B57C45] mt-0.5"><Activity className="w-5 h-5" /></div>
                <div>
                  <h4 className="font-semibold text-[#2C2B29]">2. Run Analysis</h4>
                  <p className="text-sm text-[#5C5A56] mt-1">Compare deadlines against your available focus time. See your overall Time Health instantly.</p>
                </div>
              </div>

              <div className="flex gap-4 items-start">
                <div className="p-2 bg-[#FFF5F5] rounded-lg text-[#CC6633] mt-0.5"><CalendarCheck className="w-5 h-5" /></div>
                <div>
                  <h4 className="font-semibold text-[#2C2B29]">3. Review Proposals</h4>
                  <p className="text-sm text-[#5C5A56] mt-1">ChronOS suggests focus blocks or rescue actions (like scope reduction) to keep you on track.</p>
                </div>
              </div>

              <div className="flex gap-4 items-start">
                <div className="p-2 bg-[#EAF3EA] rounded-lg text-[#3D663D] mt-0.5"><CheckCircle2 className="w-5 h-5" /></div>
                <div>
                  <h4 className="font-semibold text-[#2C2B29]">4. Approve Actions</h4>
                  <p className="text-sm text-[#5C5A56] mt-1">Nothing is automatic. You approve only the actions that make sense for your reality.</p>
                </div>
              </div>

              <div className="flex gap-4 items-start">
                <div className="p-2 bg-[#E5E0D8] rounded-lg text-[#5C5A56] mt-0.5"><RotateCcw className="w-5 h-5" /></div>
                <div>
                  <h4 className="font-semibold text-[#2C2B29]">5. Reflect & Adjust</h4>
                  <p className="text-sm text-[#5C5A56] mt-1">After work sessions, quickly reflect so ChronOS can adjust risk estimates for your next analysis.</p>
                </div>
              </div>
            </div>
            <div className="p-4 bg-[#E5E0D8]/30 border-t border-[#E5E0D8] flex justify-end">
              <button
                onClick={() => setIsOpen(false)}
                className="px-6 py-2 bg-[#2C2B29] text-white text-sm font-semibold rounded-lg hover:bg-black transition-colors"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
