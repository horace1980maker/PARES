import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './i18n';
import MapComponent from './components/MapComponent';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import LanguageToggle from './components/LanguageToggle';
import TerritorialInsightCard from './components/TerritorialInsightCard';

import config from './config';

function App() {
  const { t } = useTranslation();
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [territorialInsight, setTerritorialInsight] = useState(null);
  const [isInsightLoading, setIsInsightLoading] = useState(false);
  const [mapMarkers, setMapMarkers] = useState([]);

  React.useEffect(() => {
    if (selectedCountry) {
      console.log("Obteniendo organizaciones para:", selectedCountry);
      fetch(`${config.API_URL}/organizaciones/${selectedCountry}`)
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

  // Fetch territorial insight when organization is selected
  React.useEffect(() => {
    setMapMarkers([]); // Clear markers on new org selection
    if (selectedOrg) {
      console.log("Obteniendo análisis territorial para:", selectedOrg.nombre);
      setIsInsightLoading(true);
      setTerritorialInsight(null);

      fetch(`${config.API_URL}/insight-territorial`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          organizacion: selectedOrg.nombre,
          mensaje: "" // Not used but required by ChatRequest model
        }),
      })
        .then(res => res.json())
        .then(data => {
          console.log("Análisis territorial obtenido:", data);
          setTerritorialInsight(data.respuesta);
        })
        .catch(err => {
          console.error("Error obteniendo análisis territorial:", err);
          setTerritorialInsight("Error obteniendo análisis territorial. Por favor intente nuevamente.");
        })
        .finally(() => {
          setIsInsightLoading(false);
        });
    } else {
      setTerritorialInsight(null);
    }
  }, [selectedOrg]);

  const handleCountrySelect = (countryName) => {
    setSelectedCountry(countryName);
    setSelectedOrg(null);
    setTerritorialInsight(null);
    setMapMarkers([]);
  };

  const handleOrgSelect = (org) => {
    console.log("Organización seleccionada:", org);
    setSelectedOrg(org);
    // mapMarkers cleared by useEffect
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-nature-50 overflow-hidden">
      {/* Header would go here if you have one */}

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Map Area - Reduced size */}
        <div className="flex-1 p-4 relative z-0">
          <MapComponent
            onCountrySelect={handleCountrySelect}
            selectedCountry={selectedCountry}
            markers={mapMarkers}
          />

          {/* Territorial Insight Card - Positioned over map */}
          {selectedOrg && (
            <TerritorialInsightCard
              data={territorialInsight}
              isLoading={isInsightLoading}
              onClose={() => {
                setSelectedOrg(null);
                setTerritorialInsight(null);
                setMapMarkers([]);
              }}
            />
          )}
        </div>

        {/* Sidebar */}
        <Sidebar
          selectedCountry={selectedCountry}
          organizations={organizations}
          onOrgSelect={handleOrgSelect}
        />
      </div>

      {/* Chat Interface (Floating & Draggable) */}
      {selectedOrg && (
        <ChatInterface
          selectedOrg={selectedOrg}
          selectedCountry={selectedCountry}
          onClose={() => setSelectedOrg(null)}
          setMapMarkers={setMapMarkers}
        />
      )}
    </div>
  );
}

export default App;
