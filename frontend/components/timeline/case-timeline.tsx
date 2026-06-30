import React from "react";
import { motion } from "framer-motion";

const events = [
  { id: 1, title: "FIR Filed", date: "2026-06-10", desc: "First Information Report registered at MG Road station." },
  { id: 2, title: "Evidence Gathered", date: "2026-06-12", desc: "CCTV footage obtained from commercial building entrance." },
  { id: 3, title: "Suspect Apprehended", date: "2026-06-15", desc: "Accused tracked and detained by beat squad officers." },
];

export default function CaseTimeline() {
  return (
    <div className="space-y-6 relative pl-6 border-l border-slate-200 dark:border-slate-800">
      {events.map((evt, idx) => (
        <motion.div
          key={evt.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="relative"
        >
          <span className="absolute -left-9 top-1 w-6 h-6 rounded-full bg-primary border-4 border-background flex items-center justify-center"></span>
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-sm">{evt.title}</h3>
              <span className="text-xs text-muted-foreground">{evt.date}</span>
            </div>
            <p className="text-xs text-muted-foreground">{evt.desc}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
