import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './i18n';
import MapComponent from './components/MapComponent';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import LanguageToggle from './components/LanguageToggle';

function App() {
  const { t } = useTranslation();
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [organizations, setOrganizations] = useState([]);

  React.useEffect(() => {
    if (selectedCountry) {
      console.log("Obteniendo organizaciones para:", selectedCountry);
      fetch(`http://localhost:8001/organizaciones/${selectedCountry}`)
        .then(res => res.json())
        .then(data => {
          console.log("Organizaciones obtenidas:", data);
          setOrganizations(data);
        })
        .catch(err => console.error("Error obteniendo organizaciones:", err));
    } else {
      setOrganizations([]);
    }
  }, [selectedCountry]);

  const handleCountrySelect = (countryName) => {
    setSelectedCountry(countryName);
    setSelectedOrg(null);
  };

  const handleOrgSelect = (org) => {
    console.log("Organización seleccionada:", org);
    setSelectedOrg(org);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-nature-50 overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-nature-200 px-6 py-4 shadow-sm z-20 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="bg-nature-600 p-2 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-nature-900 tracking-tight">{t('appTitle')}</h1>
            <p className="text-xs text-nature-500">{t('projectName')}</p>
          </div>
        </div>

        {/* Language Toggle */}
        <LanguageToggle />
      </header>

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Map Area */}
        <div className="flex-1 p-4 relative z-0">
          <MapComponent
            onCountrySelect={handleCountrySelect}
            selectedCountry={selectedCountry}
          />
        </div>

        {/* Sidebar */}
        <Sidebar
          selectedCountry={selectedCountry}
          organizations={organizations}
          onOrgSelect={handleOrgSelect}
        />
      </div>

      {/* Chat Interface (Floating) */}
      {selectedOrg && (
        <ChatInterface
          selectedOrg={selectedOrg}
          onClose={() => setSelectedOrg(null)}
        />
      )}
    </div>
  );
}

export default App;
