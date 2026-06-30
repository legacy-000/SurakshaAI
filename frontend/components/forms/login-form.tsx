import React from "react";

export default function LoginForm() {
  return (
    <form className="space-y-4 max-w-sm w-full mx-auto p-6 bg-card border rounded-xl">
      <h3 className="text-xl font-semibold text-primary">Officer authentication Portal</h3>
      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">Badge/Username</label>
        <input 
          type="text" 
          placeholder="KA-2026-X" 
          className="w-full bg-background border rounded px-3 py-2 text-sm" 
        />
      </div>
      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">Security PIN</label>
        <input 
          type="password" 
          placeholder="••••••" 
          className="w-full bg-background border rounded px-3 py-2 text-sm" 
        />
      </div>
      <button 
        type="submit" 
        className="w-full py-2 bg-primary text-primary-foreground font-semibold rounded text-sm hover:opacity-90 transition"
      >
        Sign In
      </button>
    </form>
  );
}
