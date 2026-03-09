"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { Plus, Search, Phone, User, Mail } from "lucide-react";
import { toast } from "sonner";

export default function CRMPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    full_name: "", phone: "", email: "",
    budget_min: "", budget_max: "",
    preferred_rooms: "", preferred_districts: "", notes: "",
  });

  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers"],
    queryFn: () => api.get("/customers/").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post("/customers/", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["customers"] });
      setShowForm(false);
      setForm({ full_name: "", phone: "", email: "", budget_min: "", budget_max: "", preferred_rooms: "", preferred_districts: "", notes: "" });
      toast.success("Müşteri eklendi!");
    },
    onError: () => toast.error("Müşteri eklenemedi"),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">CRM — Müşteriler</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Yeni Müşteri
        </button>
      </div>

      {/* Müşteri Ekleme Formu */}
      {showForm && (
        <div className="bg-white rounded-xl border p-6">
          <h3 className="font-bold text-gray-900 mb-4">Yeni Müşteri Ekle</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input placeholder="Ad Soyad *" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" required />
            <input placeholder="Telefon *" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" required />
            <input placeholder="E-posta" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" />
            <input placeholder="Tercih Edilen Odalar (2+1, 3+1)" value={form.preferred_rooms} onChange={(e) => setForm({ ...form, preferred_rooms: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" />
            <input type="number" placeholder="Min Bütçe (TL)" value={form.budget_min} onChange={(e) => setForm({ ...form, budget_min: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" />
            <input type="number" placeholder="Max Bütçe (TL)" value={form.budget_max} onChange={(e) => setForm({ ...form, budget_max: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" />
            <input placeholder="Tercih Edilen İlçeler" value={form.preferred_districts} onChange={(e) => setForm({ ...form, preferred_districts: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" />
            <textarea placeholder="Notlar" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="px-4 py-2 border rounded-lg text-sm" rows={2} />
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => createMutation.mutate({
                ...form,
                budget_min: form.budget_min ? Number(form.budget_min) : null,
                budget_max: form.budget_max ? Number(form.budget_max) : null,
              })}
              disabled={!form.full_name || !form.phone}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              Kaydet
            </button>
            <button onClick={() => setShowForm(false)} className="px-6 py-2 border rounded-lg text-sm">İptal</button>
          </div>
        </div>
      )}

      {/* Müşteri Listesi */}
      <div className="bg-white rounded-xl border">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b bg-gray-50">
                <th className="px-5 py-3 font-medium">Ad Soyad</th>
                <th className="px-5 py-3 font-medium">Telefon</th>
                <th className="px-5 py-3 font-medium">Bütçe</th>
                <th className="px-5 py-3 font-medium">Oda</th>
                <th className="px-5 py-3 font-medium">İlçe</th>
                <th className="px-5 py-3 font-medium">Eşleşme</th>
                <th className="px-5 py-3 font-medium">Son İletişim</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {customers?.map((c: any) => (
                <tr key={c.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-5 py-3 font-medium text-gray-900">{c.full_name}</td>
                  <td className="px-5 py-3">
                    <a href={`tel:${c.phone}`} className="text-blue-600 flex items-center gap-1">
                      <Phone className="w-3 h-3" /> {c.phone}
                    </a>
                  </td>
                  <td className="px-5 py-3 text-gray-600">
                    {c.budget_min && c.budget_max
                      ? `${(c.budget_min / 1e6).toFixed(1)}M - ${(c.budget_max / 1e6).toFixed(1)}M`
                      : "—"}
                  </td>
                  <td className="px-5 py-3 text-gray-600">{c.preferred_rooms || "—"}</td>
                  <td className="px-5 py-3 text-gray-600">{c.preferred_districts || "—"}</td>
                  <td className="px-5 py-3">
                    {c.matched_listing_ids?.length > 0 && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                        {c.matched_listing_ids.length} eşleşme
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-gray-400 text-xs">
                    {c.last_contact_at ? new Date(c.last_contact_at).toLocaleDateString("tr-TR") : "—"}
                  </td>
                </tr>
              ))}
              {(!customers || customers.length === 0) && (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-gray-400">
                    Henüz müşteri eklenmemiş
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
