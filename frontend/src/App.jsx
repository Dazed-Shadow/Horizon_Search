import React from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import SearchPage from "./pages/SearchPage";
import LicensingPage from "./pages/LicensingPage";
import ContractPrimerPage from "./pages/ContractPrimerPage";
import StartHerePage from "./pages/StartHerePage";
import MissionPage from "./pages/MissionPage";
import TrailblazersPage from "./pages/TrailblazersPage";
export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/start" element={<StartHerePage />} />
        <Route path="/mission" element={<MissionPage />} />
        <Route path="/trailblazers" element={<TrailblazersPage />} />
        <Route path="/licensing" element={<LicensingPage />} />
        <Route path="/primer" element={<ContractPrimerPage />} />
      </Routes>
      <footer className="border-t border-gray-200 mt-auto py-5 text-center text-xs text-gray-400">
        Horizon Search · Matching services to those who serve · Contract data sourced from{" "}
        <a href="https://sam.gov" target="_blank" rel="noopener noreferrer" className="underline">SAM.gov</a>
      </footer>
    </div>
  );
}
