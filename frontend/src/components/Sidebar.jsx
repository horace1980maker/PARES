import React from 'react';
import { useTranslation } from 'react-i18next';
import { openOrgReport } from '../exportUtils';

// Map org names to their folder names for report generation
const ORG_NAME_TO_FOLDER = {
    "Corporación Biocomercio": "Corporación Biocomercio",
    "Tierra Viva": "TIERRA VIVA",
    "Corporación Toisán": "Corporación Toisán",
    "CECROPIA": "CECROPIA",
    "FONCET": "FONCET",
    "Fundación PUCA": "Fundación PUCA",
    "CODDEFFAGOLF": "CODDEFFAGOLF",
    "FENAPROCACAHO": "FENAPROCACAHO",
    "Asociación ADEL LA Unión": "Asociación ADEL LA Unión",
    "Defensores de la Naturaleza": "Defensores de la Naturaleza",
    "ASOVERDE": "ASOVERDE",
    "ECO": "ECO"
};

const Sidebar = ({ selectedCountry, organizations, onOrgSelect }) => {
    const { t, i18n } = useTranslation();

    return (
        <div className="w-96 bg-white border-l border-nature-200 p-6 flex flex-col h-full shadow-xl z-50 overflow-y-auto">
            {/* Welcome Section */}
            <div className="mb-6 pb-6 border-b border-nature-200">
                <p className="text-lg text-nature-700">
                    {t("Talk to your data in your own words.")}
                </p>
            </div>

            <h2 className="text-2xl font-bold text-nature-900 mb-6">
                {selectedCountry ? selectedCountry : t('selectCountry')}
            </h2>

            {selectedCountry ? (
                <div className="flex-1 overflow-y-auto space-y-4">
                    <h3 className="text-sm font-semibold text-nature-500 uppercase tracking-wider">
                        {t('organizations')}
                    </h3>
                    {organizations.length > 0 ? (
                        organizations.map((org, index) => (
                            <div
                                key={org.id || index}
                                className="p-4 bg-nature-50 rounded-lg border border-nature-100 hover:border-nature-300 transition-colors group"
                            >
                                <div
                                    className="cursor-pointer"
                                    onClick={() => onOrgSelect(org)}
                                >
                                    <h4 className="font-bold text-nature-800 group-hover:text-nature-600 transition-colors">
                                        {org.nombre}
                                    </h4>
                                    <p className="text-xs text-nature-600 mt-1">
                                        {i18n.language === 'es' ? org.descripcion : org.descripcion_en}
                                    </p>
                                    {org.area && (
                                        <span className="inline-block mt-2 px-2 py-1 bg-nature-200 text-nature-700 text-xs rounded-full">
                                            {org.area}
                                        </span>
                                    )}
                                </div>

                                {/* Generar Reporte Button */}
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        const folderName = ORG_NAME_TO_FOLDER[org.nombre];
                                        if (folderName) {
                                            openOrgReport(folderName);
                                        } else {
                                            alert('Reporte no disponible para esta organización');
                                        }
                                    }}
                                    className="mt-3 w-full px-3 py-2 bg-nature-600 hover:bg-nature-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Generar Reporte
                                </button>
                            </div>
                        ))
                    ) : (
                        <p className="text-nature-400 italic">{t('noOrganizations')}</p>
                    )}
                </div>
            ) : (
                <div className="flex-1 flex items-center justify-center text-center text-nature-400">
                    <p>{t('exploreMap')}</p>
                </div>
            )}
        </div>
    );
};

export default Sidebar;
