import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
    es: {
        translation: {
            // Header
            "appTitle": "MAPA INTERACTIVO",
            "projectName": "Proyecto PARES",

            // Map
            "Talk to your data in your own words.": "Habla con tus datos en tus propias palabras.",
            "Let's Start": "Comencemos",
            "selectCountry": "Selecciona un País",
            "exploreMap": "Explora el mapa para encontrar organizaciones que implementan Soluciones Basadas en Naturaleza.",

            // Sidebar
            "organizations": "Organizaciones",
            "noOrganizations": "No se encontraron organizaciones para este país.",
            "knowledgeBase": "Base de Conocimiento",
            "uploadDocuments": "Subir Documentos",
            "pdfSupported": "Archivos PDF soportados",
            "uploadInfo": "Sube documentos para mejorar el chat RAG de estas organizaciones.",

            // Chat
            "chatWith": "Chat con",
            "typeMessage": "Escribe tu mensaje...",
            "send": "Enviar",
            "chatPlaceholder": "Pregunta sobre esta organización...",
            "minimize": "Minimizar",
            "maximize": "Maximizar",

            // Territorial Insights
            "territorialInsight": "Análisis Territorial",
            "analyzing": "Analizando territorio...",
            "close": "Cerrar",

            // Language
            "language": "Idioma",
            "spanish": "Español",
            "english": "English",

            // Areas
            "conservation": "Conservación",
            "sustainableDevelopment": "Desarrollo Sostenible",
            "research": "Investigación",
            "financing": "Financiamiento",
            "protectedAreas": "Áreas Protegidas",
            "communityDevelopment": "Desarrollo Comunitario",
            "ecodevelopment": "Ecodesarrollo"
        }
    },
    en: {
        translation: {
            // Header
            "appTitle": "INTERACTIVE MAP",
            "projectName": "PARES Project",

            // Map
            "Talk to your data in your own words.": "Talk to your data in your own words.",
            "Let's Start": "Let's Start",
            "selectCountry": "Select a Country",
            "exploreMap": "Explore the map to find Nature-based Solutions organizations.",

            // Sidebar
            "organizations": "Organizations",
            "noOrganizations": "No organizations found for this country.",
            "knowledgeBase": "Knowledge Base",
            "uploadDocuments": "Upload Documents",
            "pdfSupported": "PDF files supported",
            "uploadInfo": "Upload documents to enhance the RAG chat for these organizations.",

            // Chat
            "chatWith": "Chat with",
            "typeMessage": "Type your message...",
            "send": "Send",
            "chatPlaceholder": "Ask about this organization...",
            "minimize": "Minimize",
            "maximize": "Maximize",

            // Territorial Insights
            "territorialInsight": "Territorial Insight",
            "analyzing": "Analyzing territory...",
            "close": "Close",

            // Language
            "language": "Language",
            "spanish": "Español",
            "english": "English",

            // Areas
            "conservation": "Conservation",
            "sustainableDevelopment": "Sustainable Development",
            "research": "Research",
            "financing": "Financing",
            "protectedAreas": "Protected Areas",
            "communityDevelopment": "Community Development",
            "ecodevelopment": "Ecodevelopment"
        }
    }
};

i18n
    .use(initReactI18next)
    .init({
        resources,
        lng: 'es', // Idioma por defecto: Español
        fallbackLng: 'es',
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;
