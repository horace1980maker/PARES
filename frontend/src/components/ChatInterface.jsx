import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { exportToDocx } from '../exportUtils';

import config from '../config';

const ChatInterface = ({ selectedOrg, selectedCountry, onClose, setMapMarkers }) => {
    const { t, i18n } = useTranslation();

    // Safety check
    if (!selectedOrg) return null;

    const [isMinimized, setIsMinimized] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // Draggable state
    const [position, setPosition] = useState({ x: window.innerWidth - 420, y: 24 });
    const [isDragging, setIsDragging] = useState(false);

    // Refs for mutable data during drag (avoids re-renders and dependency issues)
    const chatWindowRef = useRef(null);
    const dragRef = useRef({ x: window.innerWidth - 420, y: 24 });
    const dragOffsetRef = useRef({ x: 0, y: 0 });

    const sendMessage = async () => {
        if (!inputMessage.trim()) return;

        const userMessage = { role: 'user', content: inputMessage };
        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const response = await fetch(`${config.API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    organizacion: selectedOrg.nombre,
                    mensaje: inputMessage,
                    pais: selectedCountry  // Send country for Hybrid RAG
                }),
            });

            const data = await response.json();

            let finalContent = data.respuesta;

            // Extract map data if present
            const mapRegex = /```map_data\s*([\s\S]*?)```/;
            const match = finalContent.match(mapRegex);

            if (match && setMapMarkers) {
                try {
                    const mapJson = JSON.parse(match[1]);
                    if (Array.isArray(mapJson)) {
                        console.log("Updating map markers:", mapJson);
                        setMapMarkers(mapJson);
                        // Remove the JSON block from the message displayed to user
                        finalContent = finalContent.replace(match[0], '').trim();
                    }
                } catch (e) {
                    console.error("Error parsing map data:", e);
                }
            }

            const botMessage = { role: 'assistant', content: finalContent };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('Error en chat:', error);
            const errorMessage = {
                role: 'assistant',
                content: i18n.language === 'es'
                    ? 'Error al procesar tu mensaje. Por favor intenta de nuevo.'
                    : 'Error processing your message. Please try again.'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // Drag handlers
    const handleMouseDown = (e) => {
        setIsDragging(true);
        // Calculate offset and store in ref
        dragOffsetRef.current = {
            x: e.clientX - dragRef.current.x,
            y: e.clientY - dragRef.current.y
        };
    };

    const handleMouseMove = useCallback((e) => {
        if (!chatWindowRef.current) return;

        e.preventDefault();

        const newX = e.clientX - dragOffsetRef.current.x;
        const newY = e.clientY - dragOffsetRef.current.y;

        // Update ref
        dragRef.current = { x: newX, y: newY };

        // Direct DOM update
        chatWindowRef.current.style.left = `${newX}px`;
        chatWindowRef.current.style.top = `${newY}px`;
    }, []); // No dependencies! Stable function.

    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
        setPosition(dragRef.current); // Sync state
    }, []);

    // Sync ref when position changes externally
    useEffect(() => {
        dragRef.current = position;
    }, [position]);

    // Global listeners
    useEffect(() => {
        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, handleMouseMove, handleMouseUp]);

    return (
        <div
            ref={chatWindowRef}
            className={`fixed w-96 ${isMinimized ? 'h-auto' : 'h-[500px]'} bg-white rounded-xl shadow-2xl border border-nature-200 flex flex-col z-50 transition-height duration-300`}
            style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
                cursor: isDragging ? 'grabbing' : 'default',
                // Remove transition-all to prevent fighting with drag
            }}
        >
            {/* Header */}
            <div
                className="bg-gradient-to-r from-nature-600 to-nature-500 p-3 rounded-t-xl flex justify-between items-center cursor-grab active:cursor-grabbing select-none"
                onMouseDown={handleMouseDown}
            >
                <h3 className="text-white font-semibold text-base select-none">
                    {t('chatWith')} {selectedOrg.nombre}
                </h3>
                <div className="flex gap-2 items-center">
                    <button
                        onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
                        onMouseDown={(e) => e.stopPropagation()}
                        className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                        title={isMinimized ? t('maximize') || "Maximize" : t('minimize') || "Minimize"}
                    >
                        {isMinimized ? (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                            </svg>
                        )}
                    </button>
                    <button
                        onClick={(e) => { e.stopPropagation(); onClose(); }}
                        onMouseDown={(e) => e.stopPropagation()}
                        className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                        title={t('close') || "Close"}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Content */}
            {!isMinimized && (
                <>
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {messages.length === 0 && (
                            <div className="text-center text-nature-400 mt-8">
                                <p className="text-sm">{t('chatPlaceholder')}</p>
                            </div>
                        )}
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                            >
                                <div
                                    className={`max-w-[80%] p-3 rounded-lg ${msg.role === 'user'
                                        ? 'bg-nature-600 text-white'
                                        : 'bg-nature-100 text-nature-900'
                                        }`}
                                >
                                    <div className="text-sm markdown-content">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                ul: ({ node, ...props }) => <ul className="list-disc ml-4 mb-2" {...props} />,
                                                ol: ({ node, ...props }) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                                                li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                                                h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-2" {...props} />,
                                                h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-2" {...props} />,
                                                h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-1" {...props} />,
                                                blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-nature-300 pl-2 italic my-2" {...props} />,
                                                a: ({ node, ...props }) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                                strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
                                                em: ({ node, ...props }) => <em className="italic" {...props} />,
                                                code: ({ node, inline, ...props }) =>
                                                    inline
                                                        ? <code className="bg-black/10 rounded px-1 py-0.5 font-mono text-xs" {...props} />
                                                        : <code className="block bg-black/10 rounded p-2 font-mono text-xs my-2 whitespace-pre-wrap" {...props} />
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                                {/* Export button for assistant messages */}
                                {msg.role === 'assistant' && (
                                    <button
                                        onClick={() => exportToDocx(msg.content, `Respuesta_Chat_${idx + 1}.docx`)}
                                        className="text-xs text-nature-500 hover:text-nature-700 mt-1 flex items-center gap-1 transition-colors"
                                        title="Exportar a Word"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                        Exportar
                                    </button>
                                )}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-nature-100 text-nature-900 p-3 rounded-lg">
                                    <div className="flex gap-1">
                                        <div className="w-2 h-2 bg-nature-600 rounded-full animate-bounce"></div>
                                        <div className="w-2 h-2 bg-nature-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-2 h-2 bg-nature-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-nature-200">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={inputMessage}
                                onChange={(e) => setInputMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={t('typeMessage')}
                                className="flex-1 px-4 py-2 border border-nature-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-nature-500 text-sm"
                                disabled={isLoading}
                            />
                            <button
                                onClick={sendMessage}
                                disabled={isLoading || !inputMessage.trim()}
                                className="px-4 py-2 bg-nature-600 text-white rounded-lg hover:bg-nature-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                            >
                                {t('send')}
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default ChatInterface;
