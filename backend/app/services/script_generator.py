"""
Akıllı Tele-Prompter — Senaryo Motoru
İlan durumuna göre satıcı arama senaryoları oluşturur.
"""

SCRIPTS = {
    "cold_call_fsbo": """[Sahibinden İlanı — İlk Arama]
C: Merhaba, ben {advisor_name}. {listing_district} bölgesindeki {room_count} ilanınızı gördüm.
C: Amacım size en kısa sürede ve en iyi fiyatla satmanızda yardımcı olmak.

S: "Emlakçıyla çalışmak istemiyorum"
C: Sizi çok iyi anlıyorum. Pek çok ev sahibi böyle düşünüyor. Ancak ilanınız {dom} gündür yayında ve bu süre uzadıkça alıcıların ilgisi azalıyor. Size sadece bir bilgilendirme görüşmesi için 10 dakika ayırabilir miyim?

S: "Fiyatımdan inmem"
C: Tabii ki son karar sizin. Ancak aynı mahallede son 3 ayda kapanan benzer evlerin fiyatlarını incelediğimizde, piyasanın {avg_price} TL/m² civarında olduğunu görüyoruz. Size bu veriyi detaylıca paylaşmak isterim.

[Hedefe bağla: yüz yüze randevu al]
C: Size mahallenizin güncel piyasa raporunu hazırladım. Yarın 10 dakikalığına görüşüp bırakabilir miyim?
""",
    "cold_call_expired": """[Süresi Dolmuş / Silinmiş İlan — Geri Arama]
C: Merhaba, ben {advisor_name}. {listing_district} bölgesindeki ilanınızın kaldırıldığını fark ettik.
C: İlan {dom} gün yayında kaldı. Acaba satıldı mı yoksa satış sürecini durdurmayı mı düşündünüz?

S: "Satılmadı, ilgilenen olmadı"
C: Bu bölgede son dönemde {avg_dom} günde satış gerçekleşiyor. Fiyatlandırma ve pazarlama stratejisiyle bu süreyi kısaltabiliriz. Size piyasa analizimizi gösterebilir miyim?

S: "Fiyatı yükselteceğim"
C: Fiyat artışı alıcı ilgisini daha da düşürebilir. Geçen ay bu mahallede {sold_count} ev satıldı ve ortalama satış fiyatı listeye göre %{discount_pct} iskontoluydu. Size bu veriyi detaylıca göstermek isterim.

[Hedefe bağla: fiyat düşürme + yeniden listeleme]
""",
    "neighbor_radar": """[Komşu Radarı — Fiyat Kırma Bildirimi]
C: Merhaba, ben {advisor_name}. {listing_neighborhood} sitesinde bir gelişme hakkında sizi bilgilendirmek istedim.
C: Komşunuz {neighbor_unit} numaralı dairedeki ilanın fiyatını {price_drop_pct}% düşürdü.

C: Bu durum sizin ilanınızın rekabet gücünü etkileyebilir. Piyasa dinamiklerini birlikte değerlendirelim mi?

S: "Ben fiyatımı düşürmeyeceğim"
C: Anlıyorum. Ancak alıcılar genellikle aynı sitedeki en uygun fiyatlı seçeneğe yöneliyor. Sizin evinizin farkını — örneğin {listing_advantages} — öne çıkararak farklı bir pazarlama stratejisi geliştirebiliriz.

[Hedefe bağla: rekabetçi fiyatlandırma veya farklılaşma stratejisi]
""",
    "follow_up": """[Müşteri Takip Araması]
C: Merhaba {customer_name}, ben {advisor_name}. Geçen görüşmemizde {preferred_rooms} daire aradığınızı belirtmiştiniz.
C: {listing_district} bölgesinde tam kriterlerinize uygun yeni bir ilan girdi. {listing_title}.
C: Fiyatı {listing_price} TL ve {area_m2} m². Size gösterim ayarlayabilir miyim?

S: "Bütçem değişti"
C: Anlıyorum. Yeni bütçe aralığınızı öğrenebilir miyim? Sistemimdeki tüm ilanları buna göre filtreleyip en uygun seçenekleri sunayım.

[Hedefe bağla: gösterim randevusu]
""",
}


def generate_script(task_type: str, context: dict) -> str:
    """Görev tipine ve ilan/müşteri verisine göre konuşma senaryosu üret."""
    template_key = task_type
    if task_type == "cold_call" and context.get("is_fsbo"):
        template_key = "cold_call_fsbo"
    elif task_type == "cold_call" and context.get("dom", 0) > 60:
        template_key = "cold_call_expired"

    template = SCRIPTS.get(template_key, SCRIPTS.get("follow_up", ""))

    # Placeholder'ları doldur
    try:
        return template.format(**{
            "advisor_name": context.get("advisor_name", "Danışman"),
            "listing_district": context.get("district", ""),
            "listing_neighborhood": context.get("neighborhood", ""),
            "room_count": context.get("room_count", ""),
            "dom": context.get("dom", 0),
            "avg_price": context.get("avg_price", ""),
            "avg_dom": context.get("avg_dom", ""),
            "sold_count": context.get("sold_count", ""),
            "discount_pct": context.get("discount_pct", ""),
            "customer_name": context.get("customer_name", ""),
            "preferred_rooms": context.get("preferred_rooms", ""),
            "listing_title": context.get("listing_title", ""),
            "listing_price": context.get("listing_price", ""),
            "area_m2": context.get("area_m2", ""),
            "neighbor_unit": context.get("neighbor_unit", ""),
            "price_drop_pct": context.get("price_drop_pct", ""),
            "listing_advantages": context.get("listing_advantages", "konum ve manzara"),
        })
    except KeyError:
        return template
