"use client";
import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { toast } from "sonner";

export function VoiceRecorder() {
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [extractedData, setExtractedData] = useState<Record<string, any> | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const transcribeMutation = useMutation({
    mutationFn: (audioBase64: string) =>
      api.post("/voice/transcribe", { audio_base64: audioBase64, format: "webm" }).then((r) => r.data),
    onSuccess: (data) => {
      setTranscript(data.transcript);
      setExtractedData(data.extracted_data);
      toast.success("Sesli not işlendi!");
    },
    onError: () => toast.error("Ses işlenemedi"),
  });

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(",")[1];
          transcribeMutation.mutate(base64);
        };
        reader.readAsDataURL(blob);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      toast.error("Mikrofon erişimi reddedildi");
    }
  }

  function stopRecording() {
    mediaRecorder.current?.stop();
    setRecording(false);
  }

  return (
    <div className="bg-white rounded-xl border p-5 space-y-4">
      <h3 className="font-bold text-gray-900">Sesli CRM Asistanı</h3>
      <p className="text-sm text-gray-500">
        Klavye kullanmadan sesli not bırakın — yapay zeka bütçe, oda sayısı gibi detayları otomatik çıkartır.
      </p>

      <div className="flex items-center gap-4">
        <button
          onClick={recording ? stopRecording : startRecording}
          disabled={transcribeMutation.isPending}
          className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all ${
            recording
              ? "bg-red-600 text-white animate-pulse"
              : "bg-blue-600 text-white hover:bg-blue-700"
          } disabled:opacity-50`}
        >
          {transcribeMutation.isPending ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> İşleniyor...</>
          ) : recording ? (
            <><MicOff className="w-5 h-5" /> Durdur</>
          ) : (
            <><Mic className="w-5 h-5" /> Kaydet</>
          )}
        </button>
      </div>

      {transcript && (
        <div className="space-y-3">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">Transkript:</p>
            <p className="text-sm text-gray-900">{transcript}</p>
          </div>
          {extractedData && Object.keys(extractedData).length > 0 && (
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-xs text-blue-600 mb-2 font-medium">Çıkartılan Veriler:</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(extractedData).map(([key, value]) => (
                  value && (
                    <div key={key}>
                      <span className="text-gray-500 capitalize">{key.replace("_", " ")}:</span>{" "}
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
