import { useState } from 'react';
import { apiUrl, apiFetch as fetch } from '../lib/api';
import AppShell from '../components/layout/AppShell';
import { ExtractionReview } from '../components/intake/ExtractionReview';
import type { IntakeResponse } from '../types/api';

const MOCK_PROMPTS = {
  hackathon: "I have a hackathon this weekend starting Friday at 6pm and ending Sunday at 2pm. I need to finish the database schema by Saturday morning, build the UI by Saturday night, and prepare the pitch deck on Sunday. I also have a quick 30m sync with my team on Friday at 8pm.",
  assignment: "I have a massive physics assignment due next Wednesday at midnight. It usually takes me 5 hours total. I also have a quiz on Friday that I need to study 2 hours for. Tomorrow I want to start the assignment and do at least 1 hour.",
  interview: "I have an interview next Thursday at 10am. I need to do 3 mock interviews (1 hour each) before then. I should also spend 2 hours reviewing system design on Tuesday.",
  busy_day: "Today is packed. I need to review the Q3 report (takes 1 hr) before my 2pm meeting. I should also respond to emails for 30 mins, and try to squeeze in a 45 min workout before dinner at 7pm."
};

export default function Inbox() {
  const [text, setText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [intakeData, setIntakeData] = useState<IntakeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setIsProcessing(true);
    setError(null);
    try {
      const response = await fetch(apiUrl('/api/v1/ai/intake'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (!response.ok) {
        throw new Error("Failed to process brain dump.");
      }
      const data = await response.json();
      setIntakeData(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleComplete = () => {
    setIntakeData(null);
    setText("");
    // Optionally redirect to command canvas or show success
    alert("Commitments saved successfully!");
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto py-8">
        {!intakeData ? (
          <>
            <h2 className="text-3xl font-extrabold text-text-primary mb-2">Brain Dump Intake</h2>
            <p className="text-text-secondary mb-6">
              Dump your messy scheduling plans and let ChronOS parse them into structured commitments.
            </p>

            <div className="bg-warm-cream border border-warm-border rounded-2xl p-6 shadow-sm mb-6">
              <label className="block text-sm font-semibold text-text-primary mb-3">Messy Week Brain Dump</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="What's on your mind?"
                rows={6}
                className="w-full p-4 border border-warm-border rounded-xl bg-white resize-none text-text-primary focus:ring-2 focus:ring-accent-amber focus:outline-none transition-shadow"
              />
              
              <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
                <span className="text-xs font-semibold text-text-muted self-center mr-2">Quick Prompts:</span>
                <button onClick={() => setText(MOCK_PROMPTS.hackathon)} className="whitespace-nowrap px-3 py-1.5 bg-warm-ivory hover:bg-warm-border text-text-secondary text-xs font-medium rounded-lg transition-colors">Hackathon Week</button>
                <button onClick={() => setText(MOCK_PROMPTS.assignment)} className="whitespace-nowrap px-3 py-1.5 bg-warm-ivory hover:bg-warm-border text-text-secondary text-xs font-medium rounded-lg transition-colors">Assignment Crisis</button>
                <button onClick={() => setText(MOCK_PROMPTS.interview)} className="whitespace-nowrap px-3 py-1.5 bg-warm-ivory hover:bg-warm-border text-text-secondary text-xs font-medium rounded-lg transition-colors">Interview Prep</button>
                <button onClick={() => setText(MOCK_PROMPTS.busy_day)} className="whitespace-nowrap px-3 py-1.5 bg-warm-ivory hover:bg-warm-border text-text-secondary text-xs font-medium rounded-lg transition-colors">Busy Day</button>
              </div>

              <div className="mt-4 flex justify-between items-center border-t border-warm-border pt-4">
                {error ? <span className="text-sm text-risk-critical">{error}</span> : <div></div>}
                <button 
                  onClick={handleSubmit} 
                  disabled={isProcessing || !text.trim()} 
                  className="px-6 py-2.5 bg-accent-amber hover:bg-accent-terracotta disabled:bg-warm-border disabled:cursor-not-allowed text-white font-semibold rounded-lg text-sm shadow-sm transition-colors"
                >
                  {isProcessing ? 'Compiling...' : 'Compile Commitments'}
                </button>
              </div>
            </div>
          </>
        ) : (
          <ExtractionReview 
            agentRunId={intakeData.agent_run_id} 
            initialDrafts={intakeData.drafts} 
            onComplete={handleComplete} 
          />
        )}
      </div>
    </AppShell>
  );
}
