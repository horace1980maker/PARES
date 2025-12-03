import React from 'react';
import { useTranslation } from 'react-i18next';

const TerritorialInsightCard = ({ data, onClose, isLoading }) => {
    const { t } = useTranslation();

    if (!data && !isLoading) return null;

    const renderContent = (text) => {
        if (!text) return null;
        return text.split('\n').map((line, index) => {
            // Check for headers or bold text
            if (line.trim().startsWith('**') && line.trim().endsWith('**')) {
                return <h3 key={index} className="font-bold text-nature-800 mt-2 mb-1">{line.replace(/\*\*/g, '')}</h3>;
            }
            // Check for list items
            if (line.trim().startsWith('- ')) {
                return <li key={index} className="ml-4 list-disc text-nature-700">{line.replace('- ', '')}</li>;
            }

            // Handle bolding within lines
            const parts = line.split(/(\*\*.*?\*\*)/g);
            return (
                <p key={index} className="mb-1 text-nature-700 text-sm">
                    {parts.map((part, i) => {
                        if (part.startsWith('**') && part.endsWith('**')) {
                            return <strong key={i} className="text-nature-900">{part.replace(/\*\*/g, '')}</strong>;
                        }
                        return part;
                    })}
                </p>
            );
        });
    };

    return (
        <div className="absolute top-4 right-4 z-[1000] w-80 bg-white/90 backdrop-blur-md rounded-xl shadow-2xl border border-white/20 overflow-hidden animate-fade-in">
            <div className="bg-gradient-to-r from-nature-600 to-nature-500 p-4 flex justify-between items-center">
                <h2 className="text-white font-semibold text-lg">{t('territorialInsight')}</h2>
                <button
                    onClick={onClose}
                    className="text-white/80 hover:text-white hover:bg-white/20 rounded-full p-1 transition-colors"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L11.414 10 7.121 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                </button>
            </div>

            <div className="p-4 max-h-[70vh] overflow-y-auto custom-scrollbar">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-8 space-y-3">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-nature-600"></div>
                        <p className="text-nature-600 text-sm animate-pulse">{t('analyzing')}</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {renderContent(data)}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TerritorialInsightCard;
