"""
قائمة دول العالم وعملاتها
===========================
كل الدول مع البحث بالعربي والإنجليزي
"""

# كل دول العالم (الأساسية) مع عملاتها
ALL_COUNTRIES = [
    # ── الدول العربية (أولاً) ──
    {"name_ar": "مصر", "name_en": "Egypt", "code": "EG", "currency": "EGP", "currency_name": "جنيه مصري", "flag": "🇪🇬"},
    {"name_ar": "السعودية", "name_en": "Saudi Arabia", "code": "SA", "currency": "SAR", "currency_name": "ريال سعودي", "flag": "🇸🇦"},
    {"name_ar": "الإمارات", "name_en": "UAE", "code": "AE", "currency": "AED", "currency_name": "درهم إماراتي", "flag": "🇦🇪"},
    {"name_ar": "الكويت", "name_en": "Kuwait", "code": "KW", "currency": "KWD", "currency_name": "دينار كويتي", "flag": "🇰🇼"},
    {"name_ar": "قطر", "name_en": "Qatar", "code": "QA", "currency": "QAR", "currency_name": "ريال قطري", "flag": "🇶🇦"},
    {"name_ar": "البحرين", "name_en": "Bahrain", "code": "BH", "currency": "BHD", "currency_name": "دينار بحريني", "flag": "🇧🇭"},
    {"name_ar": "عُمان", "name_en": "Oman", "code": "OM", "currency": "OMR", "currency_name": "ريال عماني", "flag": "🇴🇲"},
    {"name_ar": "الأردن", "name_en": "Jordan", "code": "JO", "currency": "JOD", "currency_name": "دينار أردني", "flag": "🇯🇴"},
    {"name_ar": "العراق", "name_en": "Iraq", "code": "IQ", "currency": "IQD", "currency_name": "دينار عراقي", "flag": "🇮🇶"},
    {"name_ar": "لبنان", "name_en": "Lebanon", "code": "LB", "currency": "LBP", "currency_name": "ليرة لبنانية", "flag": "🇱🇧"},
    {"name_ar": "سوريا", "name_en": "Syria", "code": "SY", "currency": "SYP", "currency_name": "ليرة سورية", "flag": "🇸🇾"},
    {"name_ar": "فلسطين", "name_en": "Palestine", "code": "PS", "currency": "ILS", "currency_name": "شيكل", "flag": "🇵🇸"},
    {"name_ar": "اليمن", "name_en": "Yemen", "code": "YE", "currency": "YER", "currency_name": "ريال يمني", "flag": "🇾🇪"},
    {"name_ar": "المغرب", "name_en": "Morocco", "code": "MA", "currency": "MAD", "currency_name": "درهم مغربي", "flag": "🇲🇦"},
    {"name_ar": "تونس", "name_en": "Tunisia", "code": "TN", "currency": "TND", "currency_name": "دينار تونسي", "flag": "🇹🇳"},
    {"name_ar": "الجزائر", "name_en": "Algeria", "code": "DZ", "currency": "DZD", "currency_name": "دينار جزائري", "flag": "🇩🇿"},
    {"name_ar": "ليبيا", "name_en": "Libya", "code": "LY", "currency": "LYD", "currency_name": "دينار ليبي", "flag": "🇱🇾"},
    {"name_ar": "السودان", "name_en": "Sudan", "code": "SD", "currency": "SDG", "currency_name": "جنيه سوداني", "flag": "🇸🇩"},
    {"name_ar": "موريتانيا", "name_en": "Mauritania", "code": "MR", "currency": "MRU", "currency_name": "أوقية", "flag": "🇲🇷"},
    {"name_ar": "الصومال", "name_en": "Somalia", "code": "SO", "currency": "SOS", "currency_name": "شلن صومالي", "flag": "🇸🇴"},
    {"name_ar": "جيبوتي", "name_en": "Djibouti", "code": "DJ", "currency": "DJF", "currency_name": "فرنك جيبوتي", "flag": "🇩🇯"},
    {"name_ar": "جزر القمر", "name_en": "Comoros", "code": "KM", "currency": "KMF", "currency_name": "فرنك قمري", "flag": "🇰🇲"},

    # ── أوروبا ──
    {"name_ar": "بريطانيا", "name_en": "United Kingdom", "code": "GB", "currency": "GBP", "currency_name": "جنيه إسترليني", "flag": "🇬🇧"},
    {"name_ar": "ألمانيا", "name_en": "Germany", "code": "DE", "currency": "EUR", "currency_name": "يورو", "flag": "🇩🇪"},
    {"name_ar": "فرنسا", "name_en": "France", "code": "FR", "currency": "EUR", "currency_name": "يورو", "flag": "🇫🇷"},
    {"name_ar": "إيطاليا", "name_en": "Italy", "code": "IT", "currency": "EUR", "currency_name": "يورو", "flag": "🇮🇹"},
    {"name_ar": "إسبانيا", "name_en": "Spain", "code": "ES", "currency": "EUR", "currency_name": "يورو", "flag": "🇪🇸"},
    {"name_ar": "هولندا", "name_en": "Netherlands", "code": "NL", "currency": "EUR", "currency_name": "يورو", "flag": "🇳🇱"},
    {"name_ar": "بلجيكا", "name_en": "Belgium", "code": "BE", "currency": "EUR", "currency_name": "يورو", "flag": "🇧🇪"},
    {"name_ar": "السويد", "name_en": "Sweden", "code": "SE", "currency": "SEK", "currency_name": "كرونة سويدية", "flag": "🇸🇪"},
    {"name_ar": "النرويج", "name_en": "Norway", "code": "NO", "currency": "NOK", "currency_name": "كرونة نرويجية", "flag": "🇳🇴"},
    {"name_ar": "الدنمارك", "name_en": "Denmark", "code": "DK", "currency": "DKK", "currency_name": "كرونة دنماركية", "flag": "🇩🇰"},
    {"name_ar": "سويسرا", "name_en": "Switzerland", "code": "CH", "currency": "CHF", "currency_name": "فرنك سويسري", "flag": "🇨🇭"},
    {"name_ar": "النمسا", "name_en": "Austria", "code": "AT", "currency": "EUR", "currency_name": "يورو", "flag": "🇦🇹"},
    {"name_ar": "بولندا", "name_en": "Poland", "code": "PL", "currency": "PLN", "currency_name": "زلوتي", "flag": "🇵🇱"},
    {"name_ar": "رومانيا", "name_en": "Romania", "code": "RO", "currency": "RON", "currency_name": "ليو روماني", "flag": "🇷🇴"},
    {"name_ar": "اليونان", "name_en": "Greece", "code": "GR", "currency": "EUR", "currency_name": "يورو", "flag": "🇬🇷"},
    {"name_ar": "البرتغال", "name_en": "Portugal", "code": "PT", "currency": "EUR", "currency_name": "يورو", "flag": "🇵🇹"},
    {"name_ar": "أيرلندا", "name_en": "Ireland", "code": "IE", "currency": "EUR", "currency_name": "يورو", "flag": "🇮🇪"},
    {"name_ar": "التشيك", "name_en": "Czech Republic", "code": "CZ", "currency": "CZK", "currency_name": "كرونة تشيكية", "flag": "🇨🇿"},
    {"name_ar": "المجر", "name_en": "Hungary", "code": "HU", "currency": "HUF", "currency_name": "فورنت", "flag": "🇭🇺"},
    {"name_ar": "أوكرانيا", "name_en": "Ukraine", "code": "UA", "currency": "UAH", "currency_name": "هريفنا", "flag": "🇺🇦"},
    {"name_ar": "روسيا", "name_en": "Russia", "code": "RU", "currency": "RUB", "currency_name": "روبل روسي", "flag": "🇷🇺"},

    # ── أمريكا ──
    {"name_ar": "أمريكا", "name_en": "United States", "code": "US", "currency": "USD", "currency_name": "دولار أمريكي", "flag": "🇺🇸"},
    {"name_ar": "كندا", "name_en": "Canada", "code": "CA", "currency": "CAD", "currency_name": "دولار كندي", "flag": "🇨🇦"},
    {"name_ar": "المكسيك", "name_en": "Mexico", "code": "MX", "currency": "MXN", "currency_name": "بيزو مكسيكي", "flag": "🇲🇽"},
    {"name_ar": "البرازيل", "name_en": "Brazil", "code": "BR", "currency": "BRL", "currency_name": "ريال برازيلي", "flag": "🇧🇷"},
    {"name_ar": "الأرجنتين", "name_en": "Argentina", "code": "AR", "currency": "ARS", "currency_name": "بيزو أرجنتيني", "flag": "🇦🇷"},
    {"name_ar": "كولومبيا", "name_en": "Colombia", "code": "CO", "currency": "COP", "currency_name": "بيزو كولومبي", "flag": "🇨🇴"},
    {"name_ar": "تشيلي", "name_en": "Chile", "code": "CL", "currency": "CLP", "currency_name": "بيزو تشيلي", "flag": "🇨🇱"},

    # ── آسيا ──
    {"name_ar": "تركيا", "name_en": "Turkey", "code": "TR", "currency": "TRY", "currency_name": "ليرة تركية", "flag": "🇹🇷"},
    {"name_ar": "إيران", "name_en": "Iran", "code": "IR", "currency": "IRR", "currency_name": "ريال إيراني", "flag": "🇮🇷"},
    {"name_ar": "الهند", "name_en": "India", "code": "IN", "currency": "INR", "currency_name": "روبية هندية", "flag": "🇮🇳"},
    {"name_ar": "باكستان", "name_en": "Pakistan", "code": "PK", "currency": "PKR", "currency_name": "روبية باكستانية", "flag": "🇵🇰"},
    {"name_ar": "بنجلاديش", "name_en": "Bangladesh", "code": "BD", "currency": "BDT", "currency_name": "تاكا", "flag": "🇧🇩"},
    {"name_ar": "الصين", "name_en": "China", "code": "CN", "currency": "CNY", "currency_name": "يوان صيني", "flag": "🇨🇳"},
    {"name_ar": "اليابان", "name_en": "Japan", "code": "JP", "currency": "JPY", "currency_name": "ين ياباني", "flag": "🇯🇵"},
    {"name_ar": "كوريا الجنوبية", "name_en": "South Korea", "code": "KR", "currency": "KRW", "currency_name": "وون كوري", "flag": "🇰🇷"},
    {"name_ar": "إندونيسيا", "name_en": "Indonesia", "code": "ID", "currency": "IDR", "currency_name": "روبية إندونيسية", "flag": "🇮🇩"},
    {"name_ar": "ماليزيا", "name_en": "Malaysia", "code": "MY", "currency": "MYR", "currency_name": "رينغيت", "flag": "🇲🇾"},
    {"name_ar": "تايلاند", "name_en": "Thailand", "code": "TH", "currency": "THB", "currency_name": "بات تايلندي", "flag": "🇹🇭"},
    {"name_ar": "فيتنام", "name_en": "Vietnam", "code": "VN", "currency": "VND", "currency_name": "دونغ", "flag": "🇻🇳"},
    {"name_ar": "الفلبين", "name_en": "Philippines", "code": "PH", "currency": "PHP", "currency_name": "بيزو فلبيني", "flag": "🇵🇭"},
    {"name_ar": "سنغافورة", "name_en": "Singapore", "code": "SG", "currency": "SGD", "currency_name": "دولار سنغافوري", "flag": "🇸🇬"},
    {"name_ar": "هونغ كونغ", "name_en": "Hong Kong", "code": "HK", "currency": "HKD", "currency_name": "دولار هونغ كونغ", "flag": "🇭🇰"},

    # ── أفريقيا ──
    {"name_ar": "نيجيريا", "name_en": "Nigeria", "code": "NG", "currency": "NGN", "currency_name": "نايرا", "flag": "🇳🇬"},
    {"name_ar": "جنوب أفريقيا", "name_en": "South Africa", "code": "ZA", "currency": "ZAR", "currency_name": "راند", "flag": "🇿🇦"},
    {"name_ar": "كينيا", "name_en": "Kenya", "code": "KE", "currency": "KES", "currency_name": "شلن كيني", "flag": "🇰🇪"},
    {"name_ar": "غانا", "name_en": "Ghana", "code": "GH", "currency": "GHS", "currency_name": "سيدي", "flag": "🇬🇭"},
    {"name_ar": "إثيوبيا", "name_en": "Ethiopia", "code": "ET", "currency": "ETB", "currency_name": "بر إثيوبي", "flag": "🇪🇹"},
    {"name_ar": "تنزانيا", "name_en": "Tanzania", "code": "TZ", "currency": "TZS", "currency_name": "شلن تنزاني", "flag": "🇹🇿"},

    # ── أوقيانوسيا ──
    {"name_ar": "أستراليا", "name_en": "Australia", "code": "AU", "currency": "AUD", "currency_name": "دولار أسترالي", "flag": "🇦🇺"},
    {"name_ar": "نيوزيلندا", "name_en": "New Zealand", "code": "NZ", "currency": "NZD", "currency_name": "دولار نيوزيلندي", "flag": "🇳🇿"},
]


def search_countries(query: str, limit: int = 6) -> list:
    """
    البحث عن دولة بالعربي أو الإنجليزي أو كود العملة
    يرجع أول (limit) نتيجة مطابقة
    """
    query = query.strip().lower()
    if not query:
        return []

    results = []
    for c in ALL_COUNTRIES:
        if (query in c["name_ar"]
            or query in c["name_en"].lower()
            or query == c["code"].lower()
            or query == c["currency"].lower()):
            results.append(c)
            if len(results) >= limit:
                break
    return results


def get_country_by_code(code: str) -> dict | None:
    """جلب دولة بالكود"""
    for c in ALL_COUNTRIES:
        if c["code"] == code:
            return c
    return None


def get_countries_page(page: int, per_page: int = 8) -> tuple[list, bool, bool]:
    """
    صفحة من الدول (للسكرول في تليجرام)
    يرجع: (قائمة_الدول, فيه_سابق, فيه_تالي)
    """
    start = page * per_page
    end = start + per_page
    countries = ALL_COUNTRIES[start:end]
    has_prev = page > 0
    has_next = end < len(ALL_COUNTRIES)
    return countries, has_prev, has_next
