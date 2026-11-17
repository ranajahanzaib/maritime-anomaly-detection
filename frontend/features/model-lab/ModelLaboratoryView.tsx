"use client";

import React, { useState, useEffect } from "react";
import {
  Cpu,
  Play,
  RotateCw,
  CheckCircle2,
  TrendingDown,
  Layers,
  BarChart2,
  ShieldCheck,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { ModelRecord, EvaluationRun, DatasetItem } from "@/lib/types";
import { api } from "@/lib/api";

export function ModelLaboratoryView() {
  const [models, setModels] = useState<ModelRecord[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationRun[]>([]);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Training form state
  const [trainingName, setTrainingName] = useState<string>("TCN Trajectory Autoencoder v2");
  const [modelType, setModelType] = useState<string>("TCN_AUTOENCODER");
  const [epochs, setEpochs] = useState<number>(12);
  const [batchSize, setBatchSize] = useState<number>(16);
  const [lr, setLr] = useState<number>(0.002);
  const [trainingSubmitted, setTrainingSubmitted] = useState<boolean>(false);
  const [evalSubmitted, setEvalSubmitted] = useState<boolean>(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [mList, eList, dList] = await Promise.all([
        api.getModels(),
        api.getEvaluations(),
        api.getDatasets(),
      ]);
      setModels(mList);
      setEvaluations(eList);
      setDatasets(dList);
      if (mList.length > 0 && !selectedModel) {
        setSelectedModel(mList[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTraining = async () => {
    try {
      setTrainingSubmitted(true);
      await api.trainModel({
        name: trainingName,
        model_type: modelType,
        epochs: epochs,
        batch_size: batchSize,
        learning_rate: lr,
      });
      setTimeout(() => {
        setTrainingSubmitted(false);
        loadData();
      }, 4000);
    } catch (e) {
      console.error(e);
      setTrainingSubmitted(false);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setEvalSubmitted(true);
      await api.runEvaluation({
        dataset_name: "SYNTHETIC_BENCHMARK",
        model_id: selectedModel?.id || "model_tcn_autoencoder_v1",
      });
      setTimeout(() => {
        setEvalSubmitted(false);
        loadData();
      }, 3000);
    } catch (e) {
      console.error(e);
      setEvalSubmitted(false);
    }
  };

  const lossHistory = selectedModel?.training_loss_history || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-sky-400" />
            <span>Model Laboratory & Representation Learning</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Train, tune, and evaluate temporal convolutional autoencoders, trajectory transformers, and unsupervised outlier models.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={loadData}
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-mono transition"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh Registry</span>
          </button>
        </div>
      </div>

      {/* Top Section: Launch Training Experiment & Selected Model Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Launch Training Form */}
        <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
            <Play className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Launch Sequence Model Training
            </h2>
          </div>

          <div className="space-y-2.5 text-slate-300">
            <div>
              <label className="text-slate-500 block text-[10px] uppercase">Experiment Name</label>
              <input
                type="text"
                value={trainingName}
                onChange={(e) => setTrainingName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 mt-1 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div>
              <label className="text-slate-500 block text-[10px] uppercase">Model Architecture</label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 mt-1 focus:outline-none focus:border-sky-500"
              >
                <option value="TCN_AUTOENCODER">Temporal Conv Autoencoder (Causal Dilated 1D)</option>
                <option value="TRAJECTORY_TRANSFORMER">Trajectory Transformer Encoder (Self-Attention)</option>
              </select>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-slate-500 block text-[10px] uppercase">Epochs</label>
                <input
                  type="number"
                  value={epochs}
                  onChange={(e) => setEpochs(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 mt-1"
                />
              </div>
              <div>
                <label className="text-slate-500 block text-[10px] uppercase">Batch Size</label>
                <input
                  type="number"
                  value={batchSize}
                  onChange={(e) => setBatchSize(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 mt-1"
                />
              </div>
              <div>
                <label className="text-slate-500 block text-[10px] uppercase">LR</label>
                <input
                  type="number"
                  step="0.001"
                  value={lr}
                  onChange={(e) => setLr(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 mt-1"
                />
              </div>
            </div>

            <button
              disabled={trainingSubmitted}
              onClick={handleStartTraining}
              className="w-full mt-2 py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white font-medium flex items-center justify-center space-x-1.5 transition"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{trainingSubmitted ? "Submitting to Worker..." : "Start Training Run"}</span>
            </button>
          </div>
        </div>

        {/* Selected Model Details & Loss Chart */}
        <div className="lg:col-span-2 p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-4 h-4 text-sky-400" />
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                Model Performance & Convergence: {selectedModel?.name || "None"}
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={selectedModel?.id || ""}
                onChange={(e) => {
                  const m = models.find((x) => x.id === e.target.value);
                  if (m) setSelectedModel(m);
                }}
                className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-sky-300 font-mono"
              >
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.model_type})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Validation Metrics Summary */}
          {selectedModel && selectedModel.validation_metrics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 font-mono text-xs">
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">Final Val Loss</span>
                <span className="text-slate-200 font-bold">
                  {selectedModel.validation_metrics.final_val_loss?.toFixed(5) || "N/A"}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">Anomaly Threshold</span>
                <span className="text-amber-400 font-bold">
                  {selectedModel.validation_metrics.anomaly_threshold?.toFixed(5) || "N/A"}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">Training Windows</span>
                <span className="text-sky-400 font-bold">
                  {selectedModel.validation_metrics.total_windows || "N/A"}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-950 border border-slate-800">
                <span className="text-[10px] text-slate-500 block">Status</span>
                <span className="text-emerald-400 font-bold">
                  {selectedModel.status}
                </span>
              </div>
            </div>
          )}

          {/* Loss Convergence Chart */}
          <div className="h-52 w-full pt-2">
            {lossHistory.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lossHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} name="Epoch" />
                  <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} domain={[0, "auto"]} />
                  <Tooltip contentStyle={{ backgroundColor: "#0b111a", borderColor: "#1e293b", fontSize: 11, fontFamily: "monospace" }} />
                  <Line type="monotone" dataKey="train_loss" stroke="#38bdf8" strokeWidth={2} dot={false} name="Train MSE" />
                  <Line type="monotone" dataKey="val_loss" stroke="#10b981" strokeWidth={2} dot={false} name="Val MSE" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs font-mono text-slate-500">
                No loss history recorded for this model.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Model Comparison Table */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Model Version Comparison & Architecture Registry
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 text-[11px]">
                <th className="py-2 px-3">Model Name</th>
                <th className="py-2 px-3">Type</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Val Loss</th>
                <th className="py-2 px-3">Anomaly Threshold</th>
                <th className="py-2 px-3">Epochs</th>
                <th className="py-2 px-3">Artifact Path</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {models.map((m) => (
                <tr
                  key={m.id}
                  onClick={() => setSelectedModel(m)}
                  className={`hover:bg-slate-800/40 cursor-pointer ${
                    selectedModel?.id === m.id ? "bg-sky-950/30" : ""
                  }`}
                >
                  <td className="py-2 px-3 font-bold text-sky-400">{m.name}</td>
                  <td className="py-2 px-3 text-slate-400">{m.model_type}</td>
                  <td className="py-2 px-3 text-emerald-400 font-bold">{m.status}</td>
                  <td className="py-2 px-3">
                    {m.validation_metrics?.final_val_loss?.toFixed(5) || "—"}
                  </td>
                  <td className="py-2 px-3 text-amber-400 font-bold">
                    {m.validation_metrics?.anomaly_threshold?.toFixed(5) || "—"}
                  </td>
                  <td className="py-2 px-3 text-slate-400">{m.hyperparameters?.epochs || "—"}</td>
                  <td className="py-2 px-3 text-slate-500 truncate max-w-xs">{m.artifact_path}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Benchmark Evaluation Runs Section */}
      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center space-x-2">
            <BarChart2 className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Evaluation Runs Against Annotated Ground-Truth
            </h2>
          </div>
          <button
            disabled={evalSubmitted}
            onClick={handleRunEvaluation}
            className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white text-xs font-medium transition flex items-center space-x-1"
          >
            <span>{evalSubmitted ? "Executing Benchmark..." : "Run Evaluation Benchmark"}</span>
          </button>
        </div>

        {evaluations.length === 0 ? (
          <div className="py-6 text-center text-slate-500">
            No evaluation runs executed yet. Click &quot;Run Evaluation Benchmark&quot; to test.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            {evaluations.map((ev) => (
              <div key={ev.id} className="p-3.5 rounded bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-200">{ev.name}</span>
                  <span className="text-[10px] text-slate-500">{ev.dataset_name}</span>
                </div>
                <div className="grid grid-cols-4 gap-2 pt-1">
                  <div className="text-center p-1.5 rounded bg-slate-900">
                    <span className="text-[9px] text-slate-500 block">F1 SCORE</span>
                    <span className="text-sm font-bold text-emerald-400">
                      {ev.metrics.f1?.toFixed(3)}
                    </span>
                  </div>
                  <div className="text-center p-1.5 rounded bg-slate-900">
                    <span className="text-[9px] text-slate-500 block">PRECISION</span>
                    <span className="text-sm font-bold text-sky-400">
                      {ev.metrics.precision?.toFixed(3)}
                    </span>
                  </div>
                  <div className="text-center p-1.5 rounded bg-slate-900">
                    <span className="text-[9px] text-slate-500 block">RECALL</span>
                    <span className="text-sm font-bold text-cyan-400">
                      {ev.metrics.recall?.toFixed(3)}
                    </span>
                  </div>
                  <div className="text-center p-1.5 rounded bg-slate-900">
                    <span className="text-[9px] text-slate-500 block">ROC-AUC</span>
                    <span className="text-sm font-bold text-purple-400">
                      {ev.metrics.roc_auc?.toFixed(3)}
                    </span>
                  </div>
                </div>
                <div className="text-[10px] text-slate-500 pt-1 font-sans">
                  {ev.report_text}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
