import React from 'react';
import { useTranslation } from 'react-i18next';

const Sidebar = ({ selectedCountry, organizations, onOrgSelect }) => {
    const { t, i18n } = useTranslation();



    return (
        <div className="w-80 bg-white border-l border-nature-200 p-6 flex flex-col h-full shadow-xl z-50">
            {/* Welcome Section */}
            <div className="mb-6 pb-6 border-b border-nature-200">
                <p className="text-lg text-nature-700 mb-4">
                    {t("Talk to your data in your own words.")}
                </p>
                <button className="w-full px-4 py-2 bg-nature-600 text-white rounded-lg hover:bg-nature-700 transition-colors font-medium">
                    {t("Let's Start")}
                </button>
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
                                className="p-4 bg-nature-50 rounded-lg border border-nature-100 hover:border-nature-300 transition-colors cursor-pointer group"
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
