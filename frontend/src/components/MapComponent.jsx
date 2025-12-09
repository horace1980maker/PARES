import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { useTranslation } from 'react-i18next';
import 'leaflet/dist/leaflet.css';

const MapComponent = ({ onCountrySelect, selectedCountry }) => {
    const { t } = useTranslation();
    const [geoJsonData, setGeoJsonData] = useState(null);

    useEffect(() => {
        fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
            .then(response => response.json())
            .then(data => setGeoJsonData(data));
    }, []);

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
                {geoJsonData && (
                    <GeoJSON
                        data={geoJsonData}
                        style={style}
                        onEachFeature={onEachFeature}
                    />
                )}
            </MapContainer>
        </div>
    );
};

export default MapComponent;
