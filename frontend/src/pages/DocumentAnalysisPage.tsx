import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import { DocumentItem, ExtractedField } from '../types';
import { CurrencyDisplay, formatINR } from '../components/common/CurrencyDisplay';
import {
  FileCheck2,
  FileText,
  CheckCircle,
  AlertTriangle,
  Edit2,
  Save,
  Check,
  Eye,
  ArrowRight,
  Layers,
  Sparkles,
} from 'lucide-react';

export const DocumentAnalysisPage: React.FC = () => {
  const { financialYear, showToast, refreshAll } = useTax();
  const [searchParams] = useSearchParams();
  const docIdParam = searchParams.get('docId');

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [conflicts, setConflicts] = useState<{ [key: string]: ExtractedField[] }>({});

  const loadData = useCallback(async () => {
    try {
      const docs = await api.documents.list(financialYear);
      setDocuments(docs);

      let targetDocId = selectedDocId;
      if (!targetDocId && docIdParam) {
        targetDocId = docIdParam;
      } else if (!targetDocId && docs.length > 0) {
        targetDocId = docs[0].id;
      }
      setSelectedDocId(targetDocId);

      if (targetDocId) {
        const extracted = await api.extraction.getFields(targetDocId);
        setFields(extracted);
      }

      // Check conflicts across all documents for this FY
      const allFields = await api.extraction.getFields(undefined, financialYear);
      const conflictMap: { [key: string]: ExtractedField[] } = {};
      allFields.forEach((f) => {
        if (f.conflict_flag) {
          if (!conflictMap[f.field_key]) {
            conflictMap[f.field_key] = [];
          }
          conflictMap[f.field_key].push(f);
        }
      });
      setConflicts(conflictMap);
    } catch (err) {
      console.error(err);
      showToast('Could not load extraction data', 'error');
    }
  }, [docIdParam, financialYear, selectedDocId, showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSelectDoc = async (id: string) => {
    setSelectedDocId(id);
    try {
      const extracted = await api.extraction.getFields(id);
      setFields(extracted);
    } catch (err) {
      showToast('Failed to load fields for document', 'error');
    }
  };

  const handleStartEdit = (field: ExtractedField) => {
    setEditingFieldId(field.id);
    setEditValue(field.field_value);
  };

  const handleSaveEdit = async (fieldId: string) => {
    try {
      await api.extraction.updateField(fieldId, {
        field_value: editValue,
      });
      showToast('Field updated and flagged as user-edited.', 'success');
      setEditingFieldId(null);
      await loadData();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to update field', 'error');
    }
  };

  const handleConfirmField = async (fieldId: string) => {
    try {
      await api.extraction.confirmField(fieldId);
      showToast('Field confirmed and committed to financial profile.', 'success');
      await loadData();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to confirm field', 'error');
    }
  };

  const handleConfirmAll = async () => {
    try {
      for (const field of fields) {
        if (field.status !== 'confirmed') {
          await api.extraction.confirmField(field.id);
        }
      }
      showToast('All fields confirmed and synced to tax engine!', 'success');
      await loadData();
      await refreshAll();
    } catch (err: any) {
      showToast('Error confirming fields', 'error');
    }
  };

  const handleResolveConflict = async (key: string, chosenFieldId: string) => {
    try {
      await api.extraction.resolveConflict(key, { chosen_field_id: chosenFieldId });
      showToast(`Conflict on ${key} resolved successfully!`, 'success');
      await loadData();
      await refreshAll();
    } catch (err: any) {
      showToast('Failed to resolve conflict', 'error');
    }
  };

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-indigo-100 text-indigo-700">
              <FileCheck2 className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              AI Verification Workbench
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Side-by-side inspection of source documents and AI-extracted structured fields with confidence scores.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleConfirmAll}
            className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Confirm All Fields</span>
          </button>
        </div>
      </div>

      {/* Conflict Resolution Banner (if any) */}
      {Object.keys(conflicts).length > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Multi-Document Discrepancy Detected ({Object.keys(conflicts).length} conflicts)</span>
          </div>

          <div className="space-y-2">
            {Object.entries(conflicts).map(([fieldKey, conflictingFields]) => (
              <div
                key={fieldKey}
                className="bg-white p-3 rounded-lg border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-800">
                    Field: <code className="bg-slate-100 px-1 py-0.5 rounded">{fieldKey}</code>
                  </span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {conflictingFields.map((cf) => (
                      <span key={cf.id} className="text-slate-600 bg-slate-50 border px-2 py-0.5 rounded text-[11px]">
                        Value: <strong>{cf.field_value}</strong> (Doc ID: {cf.document_id.slice(0, 6)}...)
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {conflictingFields.map((cf, idx) => (
                    <button
                      key={cf.id}
                      onClick={() => handleResolveConflict(fieldKey, cf.id)}
                      className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded border border-indigo-200"
                    >
                      Choose Source #{idx + 1}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Side-by-Side Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Pane: Document Selector & Preview */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden flex flex-col h-[700px]">
          <div className="p-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700">Source Document Viewer</span>
            <select
              value={selectedDocId}
              onChange={(e) => handleSelectDoc(e.target.value)}
              className="text-xs p-1.5 border border-slate-300 rounded bg-white font-medium text-slate-700 max-w-[200px] truncate"
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.file_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 bg-slate-900/5 p-4 flex flex-col items-center justify-center overflow-hidden">
            {selectedDoc ? (
              <div className="w-full h-full flex flex-col bg-white rounded-lg shadow-inner border border-slate-200 overflow-hidden">
                <div className="p-2 bg-slate-100 border-b border-slate-200 flex items-center justify-between text-xs text-slate-600">
                  <span className="font-medium truncate">{selectedDoc.file_name}</span>
                  <a
                    href={api.documents.getViewUrl(selectedDoc.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-indigo-600 hover:underline"
                  >
                    <span>Open Raw</span>
                    <Eye className="w-3.5 h-3.5" />
                  </a>
                </div>
                <iframe
                  src={api.documents.getViewUrl(selectedDoc.id)}
                  title="Document Preview"
                  className="w-full flex-1 border-0"
                />
              </div>
            ) : (
              <div className="text-center text-xs text-slate-400">
                <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                Select a document from the dropdown above to view its contents.
              </div>
            )}
          </div>
        </div>

        {/* Right Pane: Extracted Fields Table with Inline Editing */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden flex flex-col h-[700px]">
          <div className="p-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-800">
                Extracted Fields ({fields.length})
              </span>
              <p className="text-[11px] text-slate-400">
                Per-field confidence badge • Source snippets • Inline editor
              </p>
            </div>
            <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
              Syncs to Tax Engine
            </span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {fields.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No extracted fields found for this document. Click "Extract Data" on the Documents page.
              </div>
            ) : (
              fields.map((field) => {
                const isEditing = editingFieldId === field.id;
                const confPct = Math.round(field.confidence * 100);

                let badgeColor = 'bg-emerald-100 text-emerald-800 border-emerald-200';
                if (confPct < 50) {
                  badgeColor = 'bg-rose-100 text-rose-800 border-rose-200';
                } else if (confPct < 80) {
                  badgeColor = 'bg-amber-100 text-amber-800 border-amber-200';
                }

                return (
                  <div key={field.id} className="p-3.5 hover:bg-slate-50/70 transition-colors space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800">{field.field_label}</span>
                        <code className="text-[10px] text-slate-400 bg-slate-100 px-1 rounded">
                          {field.field_key}
                        </code>
                        {field.status === 'user_edited' && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-100 text-purple-700 font-semibold">
                            Edited by You
                          </span>
                        )}
                        {field.status === 'confirmed' && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-700 font-semibold flex items-center gap-1">
                            <Check className="w-3 h-3" /> Confirmed
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeColor}`}
                          title={`Extraction confidence score: ${confPct}%`}
                        >
                          {confPct}% Confidence
                        </span>
                      </div>
                    </div>

                    {/* Value row & edit form */}
                    <div className="flex items-center justify-between gap-3 bg-slate-50 p-2 rounded-lg border border-slate-200/60">
                      {isEditing ? (
                        <div className="flex items-center gap-2 flex-1">
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="text-xs p-1.5 bg-white border border-indigo-400 rounded flex-1 font-mono font-medium focus:outline-none"
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveEdit(field.id)}
                            className="p-1.5 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                            title="Save value"
                          >
                            <Save className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">
                            {field.normalized_value !== null && field.normalized_value !== undefined ? (
                              formatINR(field.normalized_value)
                            ) : (
                              field.field_value
                            )}
                          </span>
                          <button
                            onClick={() => handleStartEdit(field)}
                            className="p-1 text-slate-400 hover:text-indigo-600 rounded"
                            title="Edit value"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}

                      {field.status !== 'confirmed' && (
                        <button
                          onClick={() => handleConfirmField(field.id)}
                          className="px-2.5 py-1 bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-300 text-[11px] font-semibold rounded shadow-2xs transition-colors flex items-center gap-1 cursor-pointer"
                        >
                          <Check className="w-3 h-3" />
                          <span>Confirm</span>
                        </button>
                      )}
                    </div>

                    {/* Source Snippet preview */}
                    {field.source_snippet && (
                      <div className="text-[11px] text-slate-500 bg-white p-2 rounded border border-slate-100 flex items-start gap-1.5 font-mono">
                        <span className="text-slate-400 shrink-0 font-sans">Source snippet:</span>
                        <span className="text-slate-700 truncate">{field.source_snippet}</span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
