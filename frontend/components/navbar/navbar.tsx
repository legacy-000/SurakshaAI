import React from "react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-card px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* State emblem placeholder */}
        <span className="font-semibold text-lg text-primary tracking-wide">SURAKSHA AI</span>
        <span className="h-4 w-px bg-border"></span>
        <span className="text-sm text-muted-foreground">Karnataka Police Department</span>
      </div>
      
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium">Control Room Bangalore</span>
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
          KA
        </div>
      </div>
    </header>
  );
}
