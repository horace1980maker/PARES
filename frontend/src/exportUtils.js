import config from './config';

/**
 * Downloads content as a DOCX file
 * @param {string} content - Markdown formatted content to export
 * @param {string} filename - Name of the file to download
 */
export const exportToDocx = async (content, filename) => {
    try {
        const response = await fetch(`${config.API_URL}/export-docx`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content,
                filename: filename.endsWith('.docx') ? filename : `${filename}.docx`
            })
        });

        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename.endsWith('.docx') ? filename : `${filename}.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error exporting to DOCX:", error);
        alert("Error al exportar el documento. Por favor intente nuevamente.");
    }
};

/**
 * Opens organization report in new window
 * @param {string} orgFolder - Organization folder name
 */
export const openOrgReport = (orgFolder) => {
    const reportUrl = `${config.API_URL}/get-report/${encodeURIComponent(orgFolder)}`;
    window.open(reportUrl, '_blank');
};
