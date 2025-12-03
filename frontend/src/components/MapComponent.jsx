import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMapEvents } from 'react-leaflet';
import { useTranslation } from 'react-i18next';
import 'leaflet/dist/leaflet.css';
import TerritorialInsightCard from './TerritorialInsightCard';

const MapComponent = ({ onCountrySelect, selectedCountry }) => {
    const { t } = useTranslation();
    const [geoJsonData, setGeoJsonData] = useState(null);
    const [insightData, setInsightData] = useState(null);
    const [isInsightLoading, setIsInsightLoading] = useState(false);
    const [showInsight, setShowInsight] = useState(false);

    useEffect(() => {
        fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
            .then(response => response.json())
            .then(data => setGeoJsonData(data));
    }, []);

    const fetchInsight = async (lat, lng) => {
        setIsInsightLoading(true);
        setShowInsight(true);
        setInsightData(null);
        try {
            const response = await fetch('http://localhost:8001/insight-territorial', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ lat, lng }),
            });
            const data = await response.json();
            setInsightData(data.respuesta);
        } catch (error) {
            console.error("Error obteniendo insight:", error);
            setInsightData("Error obteniendo datos. Por favor intenta de nuevo.");
        } finally {
            setIsInsightLoading(false);
        }
    };

    const MapEvents = () => {
        useMapEvents({
            click(e) {
                const { lat, lng } = e.latlng;
                console.log("Clic en:", lat, lng);
                fetchInsight(lat, lng);
            },
        });
        return null;
    };

    const onEachFeature = (feature, layer) => {
        layer.on({
            click: (e) => {
                onCountrySelect(feature.properties.name);
            },
            mouseover: (e) => {
                const layer = e.target;
                layer.setStyle({
                    weight: 2,
                    color: '#009ee2',
                    dashArray: '',
                    fillOpacity: 0.7
                });
            },
            mouseout: (e) => {
                const layer = e.target;
                layer.setStyle({
                    weight: 1,
                    color: '#007bbd',
                    fillOpacity: 0.2
                });
            }
        });
    };

    const style = (feature) => {
        return {
            fillColor: selectedCountry === feature.properties.name ? '#009ee2' : '#007bbd',
            weight: 1,
            opacity: 1,
            color: 'white',
            dashArray: '3',
            fillOpacity: selectedCountry === feature.properties.name ? 0.6 : 0.2
        };
    };

    return (
        <div className="h-full w-full rounded-xl overflow-hidden shadow-lg border border-nature-200 relative">
            <MapContainer center={[10, -80]} zoom={4} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
                <MapEvents />
                {geoJsonData && (
                    <GeoJSON
                        data={geoJsonData}
                        style={style}
                        onEachFeature={onEachFeature}
                    />
                )}
            </MapContainer>

            {showInsight && (
                <TerritorialInsightCard
                    data={insightData}
                    isLoading={isInsightLoading}
                    onClose={() => setShowInsight(false)}
                />
            )}
        </div>
    );
};

export default MapComponent;
