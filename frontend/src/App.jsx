import React from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import SearchPage from "./pages/SearchPage";
import LicensingPage from "./pages/LicensingPage";
import ContractPrimerPage from "./pages/ContractPrimerPage";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/licensing" element={<LicensingPage />} />
        <Route path="/primer" element={<ContractPrimerPage />} />
      </Routes>
      <footer className="border-t border-gray-200 mt-auto py-5 text-center text-xs text-gray-400">
        Horizon Search · Contract data sourced from{" "}
        <a href="https://sam.gov" target="_blank" rel="noopener noreferrer" className="underline">SAM.gov</a>
        {" "}· Built for veteran-owned businesses
      </footer>
    </div>
  );
}
