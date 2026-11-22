import React, { useState, useEffect, useCallback } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { DocumentItem } from '../types';
import { useDropzone } from 'react-dropzone';
import { Link } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  FileCheck2,
  Trash2,
  Lock,
  Play,
  AlertCircle,
  CheckCircle,
  Clock,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

export const UploadDocumentsPage: React.FC = () => {
  const { financialYear, showToast } = useTax();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [passwordModalDoc, setPasswordModalDoc] = useState<DocumentItem | null>(null);
  const [pdfPassword, setPdfPassword] = useState<string>('');

  const fetchDocs = useCallback(async () => {
    try {
      const data = await api.documents.list(financialYear);
      setDocuments(data);
    } catch (err: any) {
      showToast('Could not load documents', 'error');
    }
  }, [financialYear, showToast]);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      setIsUploading(true);

      for (const file of acceptedFiles) {
        try {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('financial_year', financialYear);
          formData.append('doc_type', 'other');

          const newDoc = await api.documents.upload(formData);
          showToast(`Uploaded ${file.name} successfully`, 'success');

          // Trigger extraction automatically
          try {
            await api.extraction.processDoc(newDoc.id);
            showToast(`Analyzed ${file.name} with AI extraction pipeline`, 'success');
          } catch (procErr: any) {
            if (procErr.response?.data?.detail?.includes('Password')) {
              showToast(`${file.name} is password protected`, 'info');
            }
          }
        } catch (err: any) {
          showToast(err.response?.data?.detail || `Failed to upload ${file.name}`, 'error');
        }
      }

      setIsUploading(false);
      await fetchDocs();
    },
    [financialYear, fetchDocs, showToast]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document and all its extracted data?')) return;
    try {
      await api.documents.delete(docId);
      showToast('Document deleted', 'info');
      await fetchDocs();
    } catch (err: any) {
      showToast('Failed to delete document', 'error');
    }
  };

  const handleProcessDoc = async (doc: DocumentItem, password?: string) => {
    setProcessingId(doc.id);
    try {
      await api.extraction.processDoc(doc.id, password);
      showToast(`Document ${doc.file_name} extracted successfully!`, 'success');
      setPasswordModalDoc(null);
      setPdfPassword('');
      await fetchDocs();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Extraction failed';
      if (msg.includes('Password') || doc.is_password_protected) {
        setPasswordModalDoc(doc);
      } else {
        showToast(msg, 'error');
      }
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <UploadCloud className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Financial Document Ingestion
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Upload Salary Slips, Form 16, Bank Statements, Insurance Receipts, Rent Receipts, AIS/26AS for FY {financialYear}.
          </p>
        </div>

        <Link
          to="/extraction"
          className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors"
        >
          <FileCheck2 className="w-4 h-4" />
          <span>Go to Verification Workbench</span>
        </Link>
      </div>

      {/* Drag & Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-indigo-500 bg-indigo-50/50 scale-[0.99]'
            : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center gap-2">
          <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-semibold text-slate-700">
            {isDragActive ? 'Drop your financial files here...' : 'Drag & drop documents here, or browse files'}
          </p>
          <p className="text-xs text-slate-400 max-w-md">
            Supports PDF, JPG, PNG, CSV, XLS, XLSX (up to 10MB each). All documents are AES-128 encrypted at rest.
          </p>
          {isUploading && (
            <div className="mt-2 text-xs font-semibold text-indigo-600 animate-pulse">
              Uploading & running AI OCR pipeline...
            </div>
          )}
        </div>
      </div>

      {/* Document List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-800">
            Uploaded Documents ({documents.length})
          </h2>
          <span className="text-xs text-slate-400">
            Financial Year: <strong>{financialYear}</strong>
          </span>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No documents uploaded yet for FY {financialYear}. Drag & drop sample files to begin.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {documents.map((doc) => {
              const isProcessing = processingId === doc.id;
              return (
                <div
                  key={doc.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2.5 rounded-lg bg-slate-100 text-slate-600 mt-0.5">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800">{doc.file_name}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-slate-100 text-slate-600 uppercase">
                          {doc.doc_type}
                        </span>
                        {doc.is_password_protected && (
                          <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                            <Lock className="w-3 h-3" /> Protected
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-400">
                        <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          {doc.status === 'PROCESSED' && (
                            <span className="text-emerald-600 font-medium flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" /> {doc.extracted_fields?.length || 0} fields extracted
                            </span>
                          )}
                          {doc.status === 'PENDING' && (
                            <span className="text-amber-600 font-medium flex items-center gap-1">
                              <Clock className="w-3 h-3" /> Ready for extraction
                            </span>
                          )}
                          {doc.status === 'PROCESSING' && (
                            <span className="text-indigo-600 font-medium animate-pulse">
                              Processing OCR...
                            </span>
                          )}
                          {doc.status === 'ERROR' && (
                            <span className="text-rose-600 font-medium flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" /> {doc.error_message || 'Extraction failed'}
                            </span>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    {doc.status !== 'PROCESSED' ? (
                      <button
                        onClick={() => handleProcessDoc(doc)}
                        disabled={isProcessing}
                        className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-md border border-indigo-200 transition-colors cursor-pointer"
                      >
                        <Play className="w-3 h-3" />
                        <span>{isProcessing ? 'Analyzing...' : 'Extract Data'}</span>
                      </button>
                    ) : (
                      <Link
                        to={`/extraction?docId=${doc.id}`}
                        className="flex items-center gap-1 px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-md border border-emerald-200 transition-colors"
                      >
                        <FileCheck2 className="w-3 h-3" />
                        <span>Review Fields</span>
                      </Link>
                    )}

                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Password Modal */}
      {passwordModalDoc && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-5 space-y-4 border border-slate-200">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-amber-100 text-amber-700">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-800">Password Required</h3>
                <p className="text-[11px] text-slate-500">
                  {passwordModalDoc.file_name} is password protected.
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600">
              For security, passwords are never stored. They are used in-memory solely to unlock and parse this document.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Document Password (e.g. PAN in uppercase, or DOB)
              </label>
              <input
                type="password"
                value={pdfPassword}
                onChange={(e) => setPdfPassword(e.target.value)}
                placeholder="Enter password..."
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setPasswordModalDoc(null)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={() => handleProcessDoc(passwordModalDoc, pdfPassword)}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md shadow-xs"
              >
                Unlock & Process
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
