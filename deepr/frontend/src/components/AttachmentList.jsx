import React from 'react';
import { FileText, Image, FileCode, File, Download, X } from 'lucide-react';
import { API_URL } from '../config';

const getFileIcon = (fileType) => {
    switch (fileType) {
        case 'image':
            return <Image size={16} className="text-blue-400" />;
        case 'pdf':
            return <FileText size={16} className="text-red-400" />;
        case 'text':
            return <FileCode size={16} className="text-green-400" />;
        default:
            return <File size={16} className="text-slate-400" />;
    }
};

const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const AttachmentList = ({ attachments, onRemove, uploading }) => {
    if (!attachments || attachments.length === 0) return null;

    const handleDownload = async (attachmentId, filename) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_URL}/api/attachments/${attachmentId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                console.error('Download failed:', response.statusText);
            }
        } catch (error) {
            console.error('Download error:', error);
        }
    };

    return (
        <div className="mt-3 flex flex-wrap gap-2">
            {attachments.map(att => (
                <div
                    key={att.id}
                    className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded px-3 py-2 text-sm text-slate-300 transition-colors group relative pr-8 pl-3"
                >
                    <div onClick={() => handleDownload(att.id, att.filename)} className="flex items-center gap-2 cursor-pointer flex-1">
                        {getFileIcon(att.file_type)}
                        <span className="max-w-[200px] truncate" title={att.filename}>{att.filename}</span>
                        <span className="text-xs text-slate-500">({formatFileSize(att.file_size)})</span>
                    </div>

                    {/* Download Icon */}
                    <button
                        onClick={(e) => { e.stopPropagation(); handleDownload(att.id, att.filename); }}
                        className="text-slate-500 hover:text-blue-400 transition-colors"
                        title="Download"
                    >
                        <Download size={14} />
                    </button>

                    {/* Remove Button - Only if onRemove is provided */}
                    {onRemove && (
                        <button
                            onClick={(e) => { e.stopPropagation(); onRemove(att.id); }}
                            className="absolute -top-2 -right-2 bg-slate-600 hover:bg-red-500 text-white rounded-full p-1 shadow-md opacity-0 group-hover:opacity-100 transition-all transform hover:scale-110"
                            title="Remove attachment"
                        >
                            <X size={12} />
                        </button>
                    )}
                </div>
            ))}
        </div>
    );
};

export default AttachmentList;
