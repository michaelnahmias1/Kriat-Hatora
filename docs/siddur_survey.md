# סקר הסידור ב-Sefaria (משימה 0.1)

> נוצר אוטומטית ע״י `tools/survey_siddur.py` ב-2026-10-19T19:46:42+00:00 מול `https://www.sefaria.org`. פרמטרים: `{'limit': None, 'nusach': None, 'samples': 5, 'max_versions': 3}`.
> סיווג הנוסח והסוג הוא היוריסטיקה לפי הכותר — לאימות אנושי.
> ההכרעה אילו נוסחים ומחזורים נכנסים לשלבים 2 ו-4 — של בעל הפרויקט (סעיף "הכרעות" בסוף, ריק בכוונה).

## סיכום

- אינדקסים שנמצאו בעץ התוכן לפי מילות חיפוש: 115
- אינדקסים שנסקרו: 115
- שגיאות רשת/API: 68

## זרעי חיפוש (שמות מהתכנון — ⚠️ לא מאומתים מראש)

| זרע | נמצא כאינדקס? | השלמות מ-/api/name |
|---|---|---|
| Siddur Ashkenaz | כן | Siddur Ashkenaz, Siddur Ashkenaz, Kaddish, Siddur Ashkenaz, Shabbat, Siddur Ashkenaz, Weekday, Siddur Ashkenaz, Berachot |
| Siddur Sefard | כן | Siddur Sefard, Siddur Sefard, Musaf, Siddur Sefard, Purim, Siddur Sefard, Nissan, Siddur Sefard, Sukkot |
| Siddur Edot HaMizrach | כן | Siddur Edot HaMizrach, Siddur Edot HaMizrach, Purim, Siddur Edot HaMizrach, Nissan, Siddur Edot HaMizrach, Hanukkah, Siddur Edot HaMizrach, Havdalah |
| Machzor Rosh Hashanah | לא | Machzor Rosh Hashanah Sefard, Machzor Rosh Hashanah Ashkenaz, Machzor Rosh Hashanah Sefard, Musaf, Machzor Rosh Hashanah Edot HaMizrach, Machzor Rosh Hashanah Sefard, Maariv |
| Machzor Yom Kippur | לא | Machzor Yom Kippur Sefard, Machzor Yom Kippur Ashkenaz, Machzor Yom Kippur Edot HaMizrach, Machzor Yom Kippur Ashkenaz Linear, Machzor Yom Kippur Ashkenaz, Mincha |
| Selichot | לא | Selichot Nusach Polin, Selichot Edot HaMizrach, Selichot Nusach Lita Linear, Selichot, Selichot Nusach Ashkenaz Lita |
| Kinot | לא | Kinot for Tisha B'Av, Kinot for Tisha B'Av, Kinot for Tisha B'Av Day, Kinot for Tisha B'Av, Kinot for Tisha B'Av Night |
| Pesach Haggadah | כן | Pesach Haggadah, Pesach Haggadah, Magid, Pesach Haggadah, Maror, Pesach Haggadah, Barech, Pesach Haggadah, Hallel |
| Zemirot Shabbat | לא | Shabbat, Mishnah Shabbat, Kabbalat Shabbat, Shabbat HaGadol, Siddur Ashkenaz, Shabbat, Shabbat Evening, Zemirot for Shabbat Evening |

## נוסח: אשכנז

| אינדקס | כותר עברי | סוג | קטגוריות | צמתים/עלים | עומק | גרסאות עבריות | רישיונות | ניקוד | טעמים | שם ה׳ | `<small>` | סוגריים |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kinnot for Tisha B'Av (Ashkenaz) | קינות לתשעה באב (אשכנז) | קינות | Liturgy / Other Liturgy Works | 3/2 | 1 | 2 | CC-BY-SA, unknown | 98% | 0% | יי×51, יהוה×37, אדני×3 | 50 | 28 |
| Machzor Rosh Hashanah Ashkenaz | מחזור אשכנז לראש השנה | מחזור | Liturgy / High Holidays | 109/98 | 3 | 1 | CC-BY | 99% | 0% | יהוה×56, אדני×2 | 2 | 2 |
| Machzor Rosh Hashanah Ashkenaz Linear | מחזור לראש השנה - אשכנז | מחזור | Liturgy / High Holidays | 109/98 | 3 | 1 | CC-BY | 99% | 0% | יהוה×56, אדני×2 | 2 | 2 |
| Machzor Yom Kippur Ashkenaz | מחזור אשכנז ליום כיפור | מחזור | Liturgy / High Holidays | 89/81 | 2 | 1 | unknown | 98% | 0% | יהוה×152, אדני×7, ידוד×1 | 105 | 2 |
| Machzor Yom Kippur Ashkenaz Linear | מחזור ליום כיפור - אשכנז | מחזור | Liturgy / High Holidays | 89/81 | 2 | 1 | CC-BY | 98% | 0% | יהוה×151, אדני×7, ידוד×1 | 117 | 2 |
| Selichot Nusach Ashkenaz Lita | סליחות נוסח אשכנז ליטא | סליחות | Liturgy / High Holidays | 15/14 | 1 | 2 | CC-BY-SA | 98% | 0% | יהוה×998, אדני×139, יי×7 | 107 | 7 |
| Siddur Ashkenaz | סידור אשכנז | סידור | Liturgy / Siddur | 533/456 | 7 | 8 | CC-BY, Public Domain, unknown | 90% | 0% | יהוה×2 | 1 | 1 |
| The Koren Rosh HaShana Mahzor; Ashkenaz | מחזור קורן לראש השנה; אשכנז | מחזור | Liturgy / High Holidays | 71/66 | 3 | 1 | CC-BY-NC | 95% | 0% | יהוה×4 | 14 | 7 |
| The Koren Shalem Siddur; Ashkenaz | סידור קורן השלם; אשכנז | סידור | Liturgy / Siddur | 143/135 | 2 | 1 | CC-BY-NC | 96% | 0% | יהוה×12, יי×1 | 0 | 8 |
| The Koren Yom Kippur Mahzor; Ashkenaz | מחזור קורן ליום הכיפורים; אשכנז | מחזור | Liturgy / High Holidays | 75/67 | 3 | 1 | CC-BY-NC | 99% | 5% | יהוה×33, ה׳ (קיצור)×5 | 0 | 2 |

### Kinnot for Tisha B'Av (Ashkenaz) — קינות לתשעה באב (אשכנז)

- דוגמת ref לעלה: `Kinnot for Tisha B'Av (Ashkenaz), Kinot for Tisha B'Av Night`
- עומק טקסט בעלים: {'2': 2}; sectionNames: Chapter / Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kinot for Tisha B'Av Night (קינות לליל תשעה באב); Kinot for Tisha B'Av Day (קינות ליום תשעה באב)
- דגימה: 1090 מחרוזות, 14582 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×5, מתג ×16
- שם ה׳: יי×51, יהוה×37, אדני×3
- תגיות HTML: b×395, small×50
- דוגמאות `<small>`: «קינה לליל תשעה באב שחל במוצאי שבת» · «בליל זה:» · «בליל זה:» · «בליל זה:» · «בליל זה:»
- דוגמאות בסוגריים: «נ"א:  חָלְיֵיךְ» · «נ"א  עוֹכְרַי» · «רַע» · «שמסודרים לפי א"ב בהקדמת פ' ל-ע'» · «דברי הימים ב לה כה»
- מילות הוראה: אומר×9, אומרים×4, הקהל×1, בתענית×1
- פיסוק: נקודתיים×859, נקודה×814, פסיק×296, מרכאות (")×53, סימן קריאה×22, סימן שאלה×7, מקף לטיני (-)×7, קו מפריד (–)×6
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 1/4
  - דגימה `Kinnot for Tisha B'Av (Ashkenaz), Kinot for Tisha B'Av Night` [Kinnot for Tisha B'Av -- Wikisource]: HTTP 200, קינון 2, 93 מחרוזות
  - דגימה `Kinnot for Tisha B'Av (Ashkenaz), Kinot for Tisha B'Av Day` [Kinnot for Tisha B'Av -- Wikisource]: HTTP 200, קינון 2, 972 מחרוזות
  - דגימה `Kinnot for Tisha B'Av (Ashkenaz), Kinot for Tisha B'Av Night` [Zikhru Na, Rabbi Shlomo Halberstam, Bobover Rav]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Kinnot for Tisha B'Av (Ashkenaz), Kinot for Tisha B'Av Day` [Zikhru Na, Rabbi Shlomo Halberstam, Bobover Rav]: HTTP 200, קינון 2, 25 מחרוזות

### Machzor Rosh Hashanah Ashkenaz — מחזור אשכנז לראש השנה

- דוגמת ref לעלה: `Machzor Rosh Hashanah Ashkenaz, Annullment of Vows`
- עומק טקסט בעלים: {'1': 98}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Annullment of Vows (התרת נדרים); Eiruv Tavshilin (עירוב תבשילין); Lighting the Candles (הדלקת הנרות); Mincha for Erev Rosh Hashana (תפילת מנחה לערב ראש השנה); Maariv (תפילת ערבית); Kiddush (קידוש); The Morning Prayers (תפילת שחרית); Reading of the Torah (קריאת התורה); Sounding of the Shofar (תקיעת שופר); Musaf (תפילת מוסף); Mincha (תפילת מנחה); Tashlich (סדר תשליך)
- דגימה: 47 מחרוזות, 1700 מילים; ניקוד 99%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×214
- שם ה׳: יהוה×56, אדני×2
- תגיות HTML: b×10, small×2
- דוגמאות `<small>`: «חזן:» · «חזן:»
- דוגמאות בסוגריים: «וַאֲפִלּוּ נְזִּירוּת שִׁמְשׁוֹן» · «כָּל»
- מילות הוראה: כאן×2
- פיסוק: נקודתיים×110, פסיק×103, נקודה×64, מקף (־)×29, מרכאות (")×4, גרש לטיני (')×1
  - דגימה `Machzor Rosh Hashanah Ashkenaz, Annullment of Vows` [The Metsudah Machzor. Metsudah Publications, New York -- he (paragraph ed.)]: HTTP 200, קינון 1, 8 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz, The Morning Prayers, Morning Blessings` [The Metsudah Machzor. Metsudah Publications, New York -- he (paragraph ed.)]: HTTP 200, קינון 1, 18 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz, The Morning Prayers, Second Day of Rosh Hashana, The King` [The Metsudah Machzor. Metsudah Publications, New York -- he (paragraph ed.)]: HTTP 200, קינון 1, 4 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz, Musaf, First Day of Rosh Hashana, Shofarot` [The Metsudah Machzor. Metsudah Publications, New York -- he (paragraph ed.)]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz, Tashlich` [The Metsudah Machzor. Metsudah Publications, New York -- he (paragraph ed.)]: HTTP 200, קינון 1, 10 מחרוזות

### Machzor Rosh Hashanah Ashkenaz Linear — מחזור לראש השנה - אשכנז

- דוגמת ref לעלה: `Machzor Rosh Hashanah Ashkenaz Linear, Annullment of Vows`
- עומק טקסט בעלים: {'1': 98}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Annullment of Vows (התרת נדרים); Eiruv Tavshilin (עירוב תבשילין); Lighting the Candles (הדלקת הנרות); Mincha for Erev Rosh Hashana (תפילת מנחה לערב ראש השנה); Maariv (תפילת ערבית); Kiddush (קידוש); The Morning Prayers (תפילת שחרית); Reading of the Torah (קריאת התורה); Sounding of the Shofar (תקיעת שופר); Musaf (תפילת מוסף); Mincha (תפילת מנחה); Tashlich (סדר תשליך)
- דגימה: 560 מחרוזות, 1700 מילים; ניקוד 99%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×214
- שם ה׳: יהוה×56, אדני×2
- תגיות HTML: b×10, small×2
- דוגמאות `<small>`: «חזן:» · «חזן:»
- דוגמאות בסוגריים: «וַאֲפִלּוּ נְזִּירוּת שִׁמְשׁוֹן» · «כָּל»
- מילות הוראה: כאן×3
- פיסוק: נקודתיים×110, פסיק×103, נקודה×64, מקף (־)×29, מרכאות (")×4, גרש לטיני (')×1
  - דגימה `Machzor Rosh Hashanah Ashkenaz Linear, Annullment of Vows` [The Metsudah Machzor. Metsudah Publications, New York -- he]: HTTP 200, קינון 1, 135 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz Linear, The Morning Prayers, Morning Blessings` [The Metsudah Machzor. Metsudah Publications, New York -- he]: HTTP 200, קינון 1, 91 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz Linear, The Morning Prayers, Second Day of Rosh Hashana, The King` [The Metsudah Machzor. Metsudah Publications, New York -- he]: HTTP 200, קינון 1, 33 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz Linear, Musaf, First Day of Rosh Hashana, Shofarot` [The Metsudah Machzor. Metsudah Publications, New York -- he]: HTTP 200, קינון 1, 155 מחרוזות
  - דגימה `Machzor Rosh Hashanah Ashkenaz Linear, Tashlich` [The Metsudah Machzor. Metsudah Publications, New York -- he]: HTTP 200, קינון 1, 146 מחרוזות

### Machzor Yom Kippur Ashkenaz — מחזור אשכנז ליום כיפור

- דוגמת ref לעלה: `Machzor Yom Kippur Ashkenaz, Kaporos`
- עומק טקסט בעלים: {'1': 81}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kaporos (כפרות); Mincha Service for Erev Yom Kippur (תפלת מנחה לערב יום כפור ); Blessing the Children (ברכת הבנים); Candle Lighting (הדלקת הנרות); Kol Nidrei (כל נדרי); Maariv Service for Yom Kippur Eve (תפלת ערבית לליל יום כפור); Customs of Yom Kippur Night (מנהגי ליל יום כפור); The Morning Prayers (תפלת שחרית); Reading of the Torah (קריאת התורה); Memorial Services (סדר הזכרת נשמות); Musaf for Yom Kippur (תפלת מוסף); Mincha (תפלת מנחה); Neilah; Concluding Service (תפלת נעילה); Motzei Yom Kippur (סדר מוצאי יום כפור)
- דגימה: 308 מחרוזות, 6476 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×1138
- שם ה׳: יהוה×152, אדני×7, ידוד×1
- תגיות HTML: small×105, b×31
- דוגמאות `<small>`: «חזן:» · «סלח:» · «חטאנו:» · «סלח:» · «חטאנו:»
- דוגמאות בסוגריים: «בֵּית» · «שֶׁהֵם מִשְׁתַּחֲוִים לְהֶֽבֶל וָרִיק וּמִתְפַּלְלִים אֶל אֵל לֹא יוֹשִֽׁיעַ:»
- מילות הוראה: אומר×15, אומרים×14, בשבת×7, כאן×2, בחול×1
- פיסוק: נקודה×735, נקודתיים×631, מקף (־)×90, פסיק×49, מרכאות (")×6, גרש לטיני (')×1
  - דגימה `Machzor Yom Kippur Ashkenaz, Kaporos` [The Metsudah Machzor. Metsudah Publications, New York - Heb (paragraph ed.)]: HTTP 200, קינון 1, 16 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz, The Morning Prayers, Ma Tovu` [The Metsudah Machzor. Metsudah Publications, New York - Heb (paragraph ed.)]: HTTP 200, קינון 1, 2 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz, The Morning Prayers, Yishtabach` [The Metsudah Machzor. Metsudah Publications, New York - Heb (paragraph ed.)]: HTTP 200, קינון 1, 29 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz, Musaf for Yom Kippur, Reader's Repetition of the Amidah` [The Metsudah Machzor. Metsudah Publications, New York - Heb (paragraph ed.)]: HTTP 200, קינון 1, 189 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz, Motzei Yom Kippur` [The Metsudah Machzor. Metsudah Publications, New York - Heb (paragraph ed.)]: HTTP 200, קינון 1, 72 מחרוזות

### Machzor Yom Kippur Ashkenaz Linear — מחזור ליום כיפור - אשכנז

- דוגמת ref לעלה: `Machzor Yom Kippur Ashkenaz Linear, Kaporos`
- עומק טקסט בעלים: {'1': 81}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kaporos (כפרות); Mincha Service for Erev Yom Kippur (תפלת מנחה לערב יום כפור ); Blessing the Children (ברכת הבנים); Candle Lighting (הדלקת הנרות); Kol Nidrei (כל נדרי); Maariv Service for Yom Kippur Eve (תפלת ערבית לליל יום כפור); Customs of Yom Kippur Night (מנהגי ליל יום כפור); The Morning Prayers (תפלת שחרית); Reading of the Torah (קריאת התורה); Memorial Services (סדר הזכרת נשמות); Musaf for Yom Kippur (תפלת מוסף); Mincha (תפלת מנחה); Neilah; Concluding Service (תפלת נעילה); Motzei Yom Kippur (סדר מוצאי יום כפור)
- דגימה: 769 מחרוזות, 6480 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×1143
- שם ה׳: יהוה×151, אדני×7, ידוד×1
- תגיות HTML: small×117, b×31
- דוגמאות `<small>`: «חזן:» · «סלח:» · «חטאנו:» · «סלח:» · «חטאנו:»
- דוגמאות בסוגריים: «בֵּית» · «שֶׁהֵם מִשְׁתַּחֲוִים לְהֶֽבֶל וָרִיק וּמִתְפַּלְלִים אֶל אֵל לֹא יוֹשִֽׁיעַ:»
- מילות הוראה: בשבת×7, אומר×7, אומרים×6, כאן×2, בחול×1
- פיסוק: נקודה×735, נקודתיים×630, מקף (־)×90, פסיק×49, מרכאות (")×6, גרש לטיני (')×1
  - דגימה `Machzor Yom Kippur Ashkenaz Linear, Kaporos` [The Metsudah Machzor. Metsudah Publications, New York]: HTTP 200, קינון 1, 71 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz Linear, The Morning Prayers, Ma Tovu` [The Metsudah Machzor. Metsudah Publications, New York]: HTTP 200, קינון 1, 16 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz Linear, The Morning Prayers, Yishtabach` [The Metsudah Machzor. Metsudah Publications, New York]: HTTP 200, קינון 1, 177 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz Linear, Musaf for Yom Kippur, Reader's Repetition of the Amidah` [The Metsudah Machzor. Metsudah Publications, New York]: HTTP 200, קינון 1, 431 מחרוזות
  - דגימה `Machzor Yom Kippur Ashkenaz Linear, Motzei Yom Kippur` [The Metsudah Machzor. Metsudah Publications, New York]: HTTP 200, קינון 1, 74 מחרוזות

### Selichot Nusach Ashkenaz Lita — סליחות נוסח אשכנז ליטא

- דוגמת ref לעלה: `Selichot Nusach Ashkenaz Lita, First Day`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Chapter / Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: First Day (ליום ראשון); Second Day (ליום שני); Third Day (ליום שלישי); Fourth Day (ליום רביעי); Fifth Day (ליום חמישי); Sixth Day (ליום שישי); Seventh Day (ליום שביעי); Erev Rosh Hashana (לערב ראש השנה); Fast of Gedaliah (לצום גדליה); Second Day of the Ten Days of Penitence (ליום שני דעשי"ת); Third Day of the Ten Days of Penitence (ליום שלישי דעשי"ת); Fourth Day of the Ten Days of Penitence (ליום רביעי דעשי"ת); Fifth Day of the Ten Days of Penitence (ליום חמישי דעשי"ת); Yom Kippur Eve (לערב יום כיפור)
- דגימה: 993 מחרוזות, 32221 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×2, מתג ×5932
- שם ה׳: יהוה×998, אדני×139, יי×7
- תגיות HTML: br×906, b×252, small×107
- דוגמאות `<small>`: «הש"ץ אומר חצי קדיש:» · «פתיחה. מיוסד על פי א"ב. חתום בנימין.» · «חיבר רב סעדיה גאון» · «קהל וחזן:» · «קהל ואח"כ חזן:»
- דוגמאות בסוגריים: «בֵּית» · «מאור הגולה» · «בֵּית» · «בֵּית» · «בֵּית»
- מילות הוראה: ש"ץ×24, אומר×23, אומרים×5, הקהל×4
- פיסוק: נקודה×2904, נקודתיים×2586, פסיק×1265, מקף (־)×1087, מרכאות (")×67, סוף פסוק (׃)×32, מקף לטיני (-)×1
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 2/10
  - דגימה `Selichot Nusach Ashkenaz Lita, First Day` [Selichot Nusach Lita -- Wikisource]: HTTP 200, קינון 2, 132 מחרוזות
  - דגימה `Selichot Nusach Ashkenaz Lita, Fourth Day` [Selichot Nusach Lita -- Wikisource]: HTTP 200, קינון 2, 110 מחרוזות
  - דגימה `Selichot Nusach Ashkenaz Lita, Seventh Day` [Selichot Nusach Lita -- Wikisource]: HTTP 200, קינון 2, 114 מחרוזות
  - דגימה `Selichot Nusach Ashkenaz Lita, Third Day of the Ten Days of Penitence` [Selichot Nusach Lita -- Wikisource]: HTTP 200, קינון 2, 214 מחרוזות
  - דגימה `Selichot Nusach Ashkenaz Lita, Yom Kippur Eve` [Selichot Nusach Lita -- Wikisource]: HTTP 200, קינון 2, 78 מחרוזות
  - דגימה `Selichot Nusach Ashkenaz Lita, First Day` [Nusach Chabad -- Based on text from Wikisource]: HTTP 200, קינון 2, 131 מחרוזות

### Siddur Ashkenaz — סידור אשכנז

- דוגמת ref לעלה: `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani`
- עומק טקסט בעלים: {'1': 456}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Weekday (ימי חול); Shabbat (שבת); Festivals (חגים); Berachot (ברכות); Kaddish (קדיש)
- דגימה: 4 מחרוזות, 53 מילים; ניקוד 90%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×13
- שם ה׳: יהוה×2
- תגיות HTML: b×4, small×1
- דוגמאות `<small>`: «(בתענית ציבור אומר כאן הש"ץ עֲנֵֽנוּ)»
- דוגמאות בסוגריים: «בתענית ציבור אומר כאן הש"ץ  עֲנֵֽנוּ»
- מילות הוראה: אומר×1, ש"ץ×1, בתענית×1, כאן×1
- פיסוק: נקודתיים×5, פסיק×3, מקף (־)×1, מרכאות (")×1
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 13/15
  - דגימה `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Ashkenaz, Weekday, Minchah, Amida, Redemption` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Ashkenaz, Shabbat, Shacharit, Preparatory Prayers, Elokai Neshama` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Ashkenaz, Shabbat, Daytime Meal, Zemirot for Second Meal, Baruch Kel Elyon` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Ashkenaz, Kaddish, Kaddish achar Hashlamat Meschet` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani` [The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

### The Koren Rosh HaShana Mahzor; Ashkenaz — מחזור קורן לראש השנה; אשכנז

- דוגמת ref לעלה: `The Koren Rosh HaShana Mahzor; Ashkenaz`
- עומק טקסט בעלים: {'1': 65, '2': 1}; sectionNames: Chapter / Mishnah, Paragraph; צמתים בלי heTitle: 6
- צמתים ברמה הראשונה:  (); Annulment of Vows (התרת נדרים); Prozbul (פרוזבול); Eiruvin (עירובין);  (); Minha for Erev Rosh HaShana (מנחה לערב ראש השנה); Ahot Ketana (אחות קטנה);  (); Ma'ariv for Rosh HaShana (מעריב לראש השנה); Blessing the Children (ברכת הבנים); Kiddush for Rosh HaShana Evening (קידוש לליל ראש השנה); Simanim (סימנים); Grace After Meals (ברכת המזון); Massekhet Rosh HaShana (מסכת ראש השנה); Shaharit (שחרית); First Day (סדר ליום א'); Second Day (סדר ליום ב'); Minha (מנחה); Tashlikh (תשליך); Ma'ariv for Motza'ei Rosh HaShana (מעריב למוצאי ראש השנה); Brit Mila (סדר ברית מילה); Additional Piyutim for First Day (פיוטים נוספים ליום א'); Additional Piyutim for Second Day (פיוטים נוספים ליום ב'); Halakha Guide (הלכות תפילה);  () …
- דגימה: 79 מחרוזות, 717 מילים; ניקוד 95%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×210
- שם ה׳: יהוה×4
- תגיות HTML: br×19, small×14, i×10, b×1
- דוגמאות `<small>`: «לְשֵׁם יִחוּד קֻדְשָׁא בְּרִיךְ הוּא וּשְׁכִינְתֵּהּ בִּדְחִילוּ וּרְחִימוּ, לְי» · «א» · «ב» · «ג» · «ד»
- דוגמאות בסוגריים: «קהל:  אָמֵן» · «קהל:  אָמֵן» · «קהל:  בְּרִיךְ הוּא» · «קהל:  אָמֵן» · «קהל:  אָמֵן»
- מילות הוראה: ש״ץ×3, אומר×1
- פיסוק: פסיק×79, נקודה×59, נקודתיים×12, גרשיים (״)×9, מקף (־)×6, סוף פסוק (׃)×6
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 1/5
  - דגימה `The Koren Rosh HaShana Mahzor; Ashkenaz` [Hebrew Edition; Koren Publishers Jerusalem, 2019]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'The Koren Rosh HaShana Mahzor; Ashkenaz', please pass a more specific ref for this book, and try again. 'The Koren Rosh HaShana Mahzor; Ashkenaz' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure 
  - דגימה `The Koren Rosh HaShana Mahzor; Ashkenaz, Shaharit, Tallit` [Hebrew Edition; Koren Publishers Jerusalem, 2019]: HTTP 200, קינון 1, 8 מחרוזות
  - דגימה `The Koren Rosh HaShana Mahzor; Ashkenaz, Shaharit, The Interpretive Principles of Rabbi Yishmael` [Hebrew Edition; Koren Publishers Jerusalem, 2019]: HTTP 200, קינון 1, 15 מחרוזות
  - דגימה `The Koren Rosh HaShana Mahzor; Ashkenaz, Second Day, Avinu Malkenu` [Hebrew Edition; Koren Publishers Jerusalem, 2019]: HTTP 200, קינון 1, 56 מחרוזות
  - דגימה `The Koren Rosh HaShana Mahzor; Ashkenaz, Mourner's Kaddish Transliterated` [Hebrew Edition; Koren Publishers Jerusalem, 2019]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

### The Koren Shalem Siddur; Ashkenaz — סידור קורן השלם; אשכנז

- דוגמת ref לעלה: `The Koren Shalem Siddur; Ashkenaz`
- עומק טקסט בעלים: {'1': 134, '2': 1}; sectionNames: Chapter / Paragraph, Paragraph; צמתים בלי heTitle: 11
- צמתים ברמה הראשונה:  (); Foreword (הקדמה); Understanding Jewish Prayer (הבנת התפילה); Guide to the Reader (מדריך למתפלל); Weekdays (ימי החול);  (); Festivals (חגים ומועדים); Giving Thanks (ברכות); The Cycle of Life (מעגל החיים); Torah Readings (קריאת התורה); Gates to Prayer (הלכות תפילה)
- דגימה: 44 מחרוזות, 924 מילים; ניקוד 96%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×135
- שם ה׳: יהוה×12, יי×1
- תגיות HTML: br×20, i×19, b×1
- דוגמאות בסוגריים: «פלוני  בֶּן  פלוני» · «פלונית  בַּת  פלוני» · «פלוני  בֶּן  פלוני / פלונית  בַּת  פלוני» · «פלוני  בֶּן  פלוני» · «פלונית  בַּת  פלוני»
- מילות הוראה: שליח ציבור×1, אומר×1
- פיסוק: פסיק×133, מקף (־)×34, סוף פסוק (׃)×31, נקודה×24, נקודתיים×9
  - דגימה `The Koren Shalem Siddur; Ashkenaz` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'The Koren Shalem Siddur; Ashkenaz', please pass a more specific ref for this book, and try again. 'The Koren Shalem Siddur; Ashkenaz' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on
  - דגימה `The Koren Shalem Siddur; Ashkenaz, Ma'ariv for Shabbat and Yom Tov` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'The Koren Shalem Siddur; Ashkenaz', please pass a more specific ref for this book, and try again. 'The Koren Shalem Siddur; Ashkenaz' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on
  - דגימה `The Koren Shalem Siddur; Ashkenaz, Festivals, Yizkor` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 200, קינון 1, 28 מחרוזות
  - דגימה `The Koren Shalem Siddur; Ashkenaz, The Cycle of Life, Zeved HaBat` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 200, קינון 1, 16 מחרוזות
  - דגימה `The Koren Shalem Siddur; Ashkenaz, Gates to Prayer, Mourner's Kaddish Transliterated` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for The Koren Shalem Siddur; Ashkenaz, Gates to Prayer, Mourner's Kaddish Transliterated.

### The Koren Yom Kippur Mahzor; Ashkenaz — מחזור קורן ליום הכיפורים; אשכנז

- דוגמת ref לעלה: `The Koren Yom Kippur Mahzor; Ashkenaz`
- עומק טקסט בעלים: {'1': 65, '2': 2}; sectionNames: Chapter / Mishnah, Chapter / Paragraph, Paragraph; צמתים בלי heTitle: 8
- צמתים ברמה הראשונה:  (); Yom Kippur Eve (ערב יום הכיפורים); Yom Kippur Evening (ליל יום הכיפורים); Shaharit (שחרית); Musaf (מוסף);  (); Ne'ila (נעילה); Ma'ariv for Motza'ei Yom Kippur (מעריב למוצאי יום הכיפורים); Kiddush Levana (קידוש לבנה); Havdala (הבדלה); Birkat Kohanim In Israel (ברכת כהנים בארץ ישראל); Seder HaAvoda Nusah Sepharad (סדר העבודה נוסח ספרד); Additional Piyutim (פיוטים נוספים); Halakha Guide (הלכות תפילה); Annotated Viduy (ביאור לוידוי);  (); Rabbis' Kaddish Transliterated (קדיש דרבנן באותיות לועזיות); Mourner's Kaddish Transliterated (קדיש יתום באותיות לועזיות)
- דגימה: 134 מחרוזות, 4115 מילים; ניקוד 99%, טעמים 5%, קמץ קטן (U+05C7) ×0, מתג ×263
- שם ה׳: יהוה×33, ה׳ (קיצור)×5
- תגיות HTML: br×836, i×3, b×2
- דוגמאות בסוגריים: «עוֹמֵד, וְקוֹרֵא» · «וְעַל יְרוּשָׁלִַם בִּפְנֵי עַצְמָהּ»
- מילות הוראה: אומר×32, אומרים×10, בשבת×4, כאן×2, ש״ץ×2
- פיסוק: נקודה×258, פסיק×156, נקודתיים×92, מקף (־)×47, גרש (׳)×36, סוף פסוק (׃)×28, קו מפריד (–)×21, נקודה-פסיק×21
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 1/5
  - דגימה `The Koren Yom Kippur Mahzor; Ashkenaz` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'The Koren Yom Kippur Mahzor; Ashkenaz', please pass a more specific ref for this book, and try again. 'The Koren Yom Kippur Mahzor; Ashkenaz' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a
  - דגימה `The Koren Yom Kippur Mahzor; Ashkenaz, Yom Kippur Evening, Massekhet Yoma` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 200, קינון 2, 61 מחרוזות
  - דגימה `The Koren Yom Kippur Mahzor; Ashkenaz, Shaharit, Blessings of the Shema` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 200, קינון 1, 73 מחרוזות
  - דגימה `The Koren Yom Kippur Mahzor; Ashkenaz, Leader's Repetition for Mincha` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'The Koren Yom Kippur Mahzor; Ashkenaz', please pass a more specific ref for this book, and try again. 'The Koren Yom Kippur Mahzor; Ashkenaz' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a
  - דגימה `The Koren Yom Kippur Mahzor; Ashkenaz, Mourner's Kaddish Transliterated` [Hebrew Edition; Koren Publishers Jerusalem, 2017]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

## נוסח: חב״ד / האר״י

| אינדקס | כותר עברי | סוג | קטגוריות | צמתים/עלים | עומק | גרסאות עבריות | רישיונות | ניקוד | טעמים | שם ה׳ | `<small>` | סוגריים |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ma'aneh Lashon Chabad | מענה לשון חב"ד | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | Public Domain | 98% | 0% | יי×186, אדני×10 | 42 | 7 |
| Weekday Siddur Chabad | סידור חב"ד לימות החול | סידור | Liturgy / Siddur | 51/47 | 2 | 1 | unknown | 78% | 0% | יי×3 | 35 | 5 |

### Ma'aneh Lashon Chabad — מענה לשון חב"ד

- דוגמת ref לעלה: `Ma'aneh Lashon Chabad`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Part / Paragraph; צמתים בלי heTitle: 0
- דגימה: 61 מחרוזות, 6871 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×83
- שם ה׳: יי×186, אדני×10
- תגיות HTML: small×42, big×1, b×1, br×1
- דוגמאות `<small>`: «לאמר על קברי הצדיקיםכפי שהנהיג כ״ק אדמו״ר ר׳ דוב בער נ״ע לאמר בהאדיץ על קבר אדמו» · «אח״כ יאמר זה:» · «הנוסח מה שאומרים בעת הדלקת הלאמפין:» · «מענה לשון סימן ג׳» · «וישא עיניו אל כפים אל אל בשמים ויאמר»
- דוגמאות בסוגריים: «פב״פ» · «עִילָאָה» · «וְלָא אִשְׁתְּצֵי» · «ס״א  קיטרא» · «דְפַּלְחֵי כּוֹכְבַיָא»
- מילות הוראה: אומר×3, כאן×3, אומרים×2, בשבת×1, בתענית×1
- פיסוק: סוף פסוק (׃)×478, מקף (־)×448, נקודה×267, נקודתיים×47, גרשיים (״)×17, גרש (׳)×12
  - דגימה `Ma'aneh Lashon Chabad` [Warsaw, 1869]: HTTP 200, קינון 2, 61 מחרוזות

### Weekday Siddur Chabad — סידור חב"ד לימות החול

- דוגמת ref לעלה: `Weekday Siddur Chabad, Upon Arising`
- עומק טקסט בעלים: {'1': 47}; sectionNames: Paragraph; צמתים בלי heTitle: 14
- צמתים ברמה הראשונה:  ();  ();  (); Maariv (ערבית); Sefirat HaOmer (סדר ספירת העומר); Bedtime Shema (סדר קריאת שמע על המיטה); Kiddush Levanah (סדר קידוש לבנה);  (); Hallel (סדר הלל);  (); Musaf for Festivals (מוסף לשלש רגלים); Annulment of Vows (סדר התרת נדרים); Kapparot (סדר כפרות);  ();  (); Reading of the Nassi (פרשת הנשיאים לחודש ניסן); Blessings of Marriage Ceremony (ברכות אירוסין ונשואין); Order of a Circumcision (סדר המילה); Pidyon HaBen (סדר פדיון הבן); Mishnayot for a Mourner (סדר הלימוד לאבל)
- דגימה: 35 מחרוזות, 1224 מילים; ניקוד 78%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×51
- שם ה׳: יי×3
- תגיות HTML: small×35, b×9
- דוגמאות `<small>`: «סדר הלימוד על אביו ועל אמו כל י״ב חודש וביום שמת בו אביו או אמו שקורין יארצייט מ» · «א» · «ב» · «ג» · «ד»
- דוגמאות בסוגריים: «ע״ד איה מקום כבודו ור״ת של תיבת אי״ה. הארת יסוד אבא. כ״ה בספר קהלת יעקב» · «וע״ש בספר מעשה אורג שהאריך שם ע״ד הקבלה» · «בעשי״ת  הַשָּׁלֽוֹם» · «פלוני בן פלוני» · «פלונית בת פלוני»
- מילות הוראה: אומר×6, בעשי״ת×1
- פיסוק: פסיק×162, נקודה×111, נקודתיים×35, גרשיים (״)×26, מקף (־)×11, גרש (׳)×7
  - דגימה `Weekday Siddur Chabad, Upon Arising` [Wikisource]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Weekday Siddur Chabad', please pass a more specific ref for this book, and try again. 'Weekday Siddur Chabad' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://d
  - דגימה `Weekday Siddur Chabad, Ashrei Uva LeZion` [Wikisource]: HTTP 404, קינון —, — מחרוזות — שגיאה: 'Ref' object has no attribute '_lang'
  - דגימה `Weekday Siddur Chabad, Birkat HaMazon for Circumcision` [Wikisource]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Weekday Siddur Chabad', please pass a more specific ref for this book, and try again. 'Weekday Siddur Chabad' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://d
  - דגימה `Weekday Siddur Chabad` [Wikisource]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Weekday Siddur Chabad', please pass a more specific ref for this book, and try again. 'Weekday Siddur Chabad' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://d
  - דגימה `Weekday Siddur Chabad, Mishnayot for a Mourner` [Wikisource]: HTTP 200, קינון 1, 35 מחרוזות

## נוסח: לא מסווג

| אינדקס | כותר עברי | סוג | קטגוריות | צמתים/עלים | עומק | גרסאות עבריות | רישיונות | ניקוד | טעמים | שם ה׳ | `<small>` | סוגריים |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Akdamut Milin | אַקְדָּמוּת מִלִּין | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 100% | 0% | — | 0 | 0 |
| Annotations of Maharatz Chajes on Mishneh Torah, Prayer and the Priestly Blessing | חידושים ומקורים מהר"ץ חיות על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Annotations of Maharatz Chajes / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×1 | 0 | 0 |
| Annotations of Minchat Chinukh on Mishneh Torah, Prayer and the Priestly Blessing | חידושים ומקורים מבעל מנחת חינוך על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Annotations of Minchat Chinukh / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×1 | 0 | 0 |
| Annotations of R' Yeshaya Berlin on Mishneh Torah, Prayer and the Priestly Blessing | חידושים והגהות הגרי"ב על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Annotations of R' Yeshaya Berlin / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×6 | 0 | 0 |
| Azharot of Solomon ibn Gabirol | אזהרות לרבי שלמה אבן גבירול | פיוטים | Liturgy / Piyutim | 5/4 | 1 | 1 | Public Domain | 100% | 0% | יי×3 | 0 | 0 |
| Barukh SheAmar on Pesach Haggadah | ברוך שאמר על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | unknown | 0% | 0% | — | 0 | 10 |
| Batei HaNefesh on Pesach Haggadah | בתי הנפש על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 18/14 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×50, אדני×2 | 0 | 1 |
| Ben Aryeh on Mishneh Torah, Prayer and the Priestly Blessing | בן אריה על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Ben Aryeh / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×1 | 0 | 1 |
| Benei Binyamin on Mishneh Torah, Prayer and the Priestly Blessing | בני בנימין על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Benei Binyamin / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 0 | 1 |
| Birkat Avraham on Mishneh Torah, Prayer and the Priestly Blessing | ברכת אברהם על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Birkat Avraham / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 0 |
| Birkat Hamazon | ברכת המזון | אחר | Liturgy / Other Liturgy Works | 12/10 | 2 | 6 | Public Domain, unknown | 96% | 0% | יי×18, יהוה×9 | 10 | 1 |
| Chiddushei Rabbi Akiva Eiger on Mishneh Torah, Prayer and the Priestly Blessing | חידושי רבי עקיבא איגר על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Chiddushei Rabbi Akiva Eiger / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 4 |
| Commentary of Ritva on Pesach Haggadah | ביאור הריטב"א על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 18/15 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×18 | 3 | 33 |
| Divrei Negidim on Pesach Haggadah | דברי נגידים על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×25, אדני×1 | 0 | 1 |
| Divrei Yirmiyahu on Mishneh Torah, Prayer and the Priestly Blessing | דברי ירמיהו על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Divrei Yirmiyahu / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×124 | 0 | 24 |
| Ephod Bad on Pesach Haggadah | אפוד בד על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×27 | 0 | 9 |
| Even Ha'azel on Mishneh Torah, Prayer and the Priestly Blessing | אבן האזל על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Even Ha'azel / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 0 | 0 |
| Geulat Olam on Pesach Haggadah | גאולת עולם על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 19/15 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×50, אדני×1 | 1 | 2 |
| Hadran | הדרן | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 97% | 0% | יי×7 | 7 | 7 |
| Hadran for Tanakh | הדרן לספרי התנ"ך | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×8 | 0 | 0 |
| Hallel | הלל | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 97% | 0% | יהוה×66 | 2 | 0 |
| Hasagot HaRa'avad on Mishneh Torah, Prayer and the Priestly Blessing | השגות הראב"ד על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Hasagot HaRa'avad / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 0 |
| Kabbalat Shabbat | קבלת שבת | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 96% | 76% | יהוה×49 | 0 | 0 |
| Kessef Mishneh on Mishneh Torah, Prayer and the Priestly Blessing | כסף משנה על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Kessef Mishneh / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×36 | 15 | 336 |
| Keter Malkhut | כתר מלכות | פיוטים | Liturgy / Piyutim | 1/1 | 0 | 2 | ?, Public Domain | 100% | 0% | יי×35, אדני×2, ה׳ (קיצור)×1 | 4 | 0 |
| Ketubah Text | נוסח הכתובה | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 0% | 0% | — | 0 | 1 |
| Kimcha Davshuna on Pesach Haggadah | קמחא דאבישונא על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×7 | 0 | 0 |
| Kiryat Sefer on Mishneh Torah, Prayer and the Priestly Blessing | קרית ספר על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Kiryat Sefer / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×16 | 0 | 2 |
| Kos Eliyahu on Pesach Haggadah | כוס אליהו על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | — | — | — | — | — |
| Kovetz Al Yad HaChazakah on Mishneh Torah, Prayer and the Priestly Blessing | קובץ על היד החזקה על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Kovetz Al Yad HaChazakah / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×6 | 0 | 1 |
| Lechem Mishneh on Mishneh Torah, Prayer and the Priestly Blessing | לחם משנה על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Lechem Mishneh / Sefer Ahavah | 1/1 | 0 | 2 | Public Domain, unknown | 0% | 0% | ה׳ (קיצור)×7 | 0 | 141 |
| Lekha Dodi | לְכָה דוֹדִי | פיוטים | Liturgy / Piyutim | 1/1 | 0 | 1 | CC-BY-SA | 98% | 0% | ה׳ (קיצור)×3 | 0 | 0 |
| Leshon Chakhamim | לשון חכמים | אחר | Liturgy / Other Liturgy Works | 7/4 | 2 | 1 | CC-BY-SA | 40% | 16% | יהוה×3636, ה׳ (קיצור)×620, אדני×310, יי×8 | 2086 | 1204 |
| Lev Shalem on Mishneh Torah, Prayer and the Priestly Blessing | לב שלם על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Lev Shalem / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×21 | 0 | 0 |
| Ma'avar Yabbok | מעבר יבק | אחר | Liturgy / Other Liturgy Works | 11/10 | 1 | 1 | Public Domain | 27% | 0% | יי×1023, ה׳ (קיצור)×428, יהוה×276, אדני×96 | 326 | 190 |
| Maaseh Nissim on Pesach Haggadah | מעשה ניסים על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 0 | 3 |
| Maaseh Rokeach on Prayer and the Priestly Blessing | מעשה רקח על הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Maaseh Rokeach / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×95, אדני×1, יי×1 | 0 | 96 |
| Machzor Vitry | מחזור ויטרי | מחזור | Halakhah / Rishonim | 58/57 | 1 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×19, יי×5, אדני×4, יהוה×1 | 7 | 472 |
| Machzor Yom Ha'atzmaut & Yom Yerushalyim | מחזור ליום העצמאות ויום ירושלים | מחזור | Liturgy / Other Liturgy Works | —/— | — | 0 | — | — | — | — | — | — |
| Maharam of Padua on Mishneh Torah, Prayer and the Priestly Blessing | הגהות מהר"ם פדווא על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Maharam of Padua / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 0 |
| Marbeh Lesaper on Pesach Haggadah | מרבה לספר על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 44/39 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×44, אדני×3, יי×2 | 0 | 30 |
| Mekorei HaRambam LeRashash on Mishneh Torah, Prayer and the Priestly Blessing | מקורי הרמב"ם לרש"ש על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Mekorei HaRambam LeRashash / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 0 | 1 |
| Melekhet Shelomoh on Mishneh Torah, Prayer and the Priestly Blessing | מלאכת שלמה על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Melekhet Shelomoh / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 2 |
| Midrash BeChiddush on Pesach Haggadah | מדרש בחדוש על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 17/14 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×21 | 2 | 0 |
| Migdal Oz on Mishneh Torah, Prayer and the Priestly Blessing | מגדל עוז על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Migdal Oz / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×6 | 202 | 202 |
| Minchat Ani on Pesach Haggadah | מנחת עני על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 18/14 | 2 | 0 | — | — | — | — | 7 | 79 |
| Mishneh LaMelech on Mishneh Torah, Prayer and the Priestly Blessing | משנה למלך על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Mishneh LaMelech / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 4 |
| Mishneh Torah, Prayer and the Priestly Blessing | משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Sefer Ahavah | 1/1 | 0 | 5 | CC-BY-SA, Public Domain, unknown | 90% | 0% | ה׳ (קיצור)×2 | 162 | 168 |
| Mishneh Torah, The Order of Prayer | משנה תורה, סדר התפילה | סידור | Halakhah / Mishneh Torah / Sefer Ahavah | 1/1 | 0 | 2 | CC-BY-SA, unknown | 50% | 0% | יי×8, אדני×4, ה׳ (קיצור)×1 | 3 | 56 |
| Nachal Eitan on Mishneh Torah, Prayer and the Priestly Blessing | נחל איתן על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Nachal Eitan / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×7 | 0 | 6 |
| Naftali Seva Ratzon on Pesach Haggadah | נפתלי שבע רצון על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×8 | 0 | 0 |
| Ohr Sameach on Mishneh Torah, Prayer and the Priestly Blessing | אור שמח על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Ohr Sameach / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 0 | 6 |
| On the Prayers and Curses Uttered by Noah when he Became Sober | על הפיכחות | סידור | Second Temple / Philo | 4/3 | 1 | 0 | — | — | — | — | 0 | 51 |
| Peh Echad on Pesach Haggadah | פה אחד על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 18/14 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×54, אדני×2 | 1 | 2 |
| Peirush Hafla'ah on Pesach Haggadah | פירוש הפלאה על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×5 | 0 | 0 |
| Peninei Halakhah, Prayer | פניני הלכה, תפילה | סידור | Halakhah / Modern / Peninei Halakhah | 3/2 | 1 | 1 | CC-BY-NC | 1% | 0% | ה׳ (קיצור)×564 | 0 | 2966 |
| Peninei Halakhah, Women's Prayer | פניני הלכה, תפילת נשים | סידור | Halakhah / Modern / Peninei Halakhah | 3/2 | 1 | 1 | CC-BY-NC | 1% | 0% | ה׳ (קיצור)×488 | 0 | 2142 |
| Perek Shirah | פרק שירה | אחר | Liturgy / Other Liturgy Works | 4/3 | 1 | 2 | Public Domain, unknown | 83% | 0% | יי×54, אדני×1, יהוה×1 | 92 | 99 |
| Pesach Haggadah | הגדה של פסח | הגדה | Liturgy / Haggadah | 43/38 | 2 | 1 | Public Domain | 90% | 0% | יי×15 | 14 | 6 |
| Piskei HaSiddur | פסקי הסידור | סידור | Halakhah / Shulchan Arukh HaRav | 59/58 | 1 | 1 | unknown | 97% | 0% | ה׳ (קיצור)×17 | 0 | 12 |
| Prayer of Manasseh | תְּפִלַּת מְנַשֶׁה | סידור | Second Temple / Apocrypha | 1/1 | 0 | 1 | unknown | 96% | 84% | יהוה×9 | 0 | 0 |
| Rabbi Sacks on Rosh HaShana Mahzor | פירוש הרב זקס על מחזור ראש השנה | מחזור | Liturgy / High Holidays | 53/48 | 3 | 0 | — | 100% | 0% | — | 6 | 48 |
| Rabbi Sacks on Siddur | פירוש הרב זקס על הסידור | סידור | Liturgy / Siddur | 97/90 | 2 | 0 | — | 96% | 0% | — | 8 | 14 |
| Rabbi Sacks on Yom Kippur Mahzor | פירוש הרב זקס על מחזור ליום הכיפורים | מחזור | Liturgy / High Holidays | 51/43 | 3 | 0 | — | 99% | 0% | יהוה×1 | 8 | 113 |
| Safa Echat on Pesach Haggadah | שפה אחת על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 18/14 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×80, אדני×3 | 1 | 1 |
| Seder Ma'amadot | סדר מעמדות | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | Public Domain | 91% | 22% | יהוה×291, אדני×13, ה׳ (קיצור)×1 | 0 | 555 |
| Selichot Nusach Lita Linear | סליחות נוסח ליטא עברי אנגלי | סליחות | Liturgy / High Holidays | 15/14 | 1 | 1 | CC-BY | 98% | 0% | יהוה×615, אדני×92, יי×4 | 77 | 6 |
| Selichot Nusach Polin | סליחות נוסח פולין | סליחות | Liturgy / High Holidays | 15/14 | 1 | 1 | CC-BY-SA | 98% | 0% | יהוה×597, אדני×54, יי×10 | 87 | 17 |
| Sha'ar HaMelekh on Mishneh Torah, Prayer and the Priestly Blessing | שער המלך על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Sha'ar HaMelekh / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 0 |
| Shalom Aleichem | שלום עליכם | פיוטים | Liturgy / Piyutim | 1/1 | 0 | 1 | CC-BY-SA | 100% | 0% | — | 0 | 0 |
| Shibolei HaLeket on Pesach Haggadah | שבלי הלקט על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×1 | 0 | 6 |
| Shir HaKavod | שיר הכבוד | פיוטים | Liturgy / Piyutim | 1/1 | 0 | 1 | unknown | 100% | 0% | יי×4 | 0 | 0 |
| Shorshei HaYam on Mishneh Torah, Prayer and the Priestly Blessing | שורשי הים על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Shorshei HaYam / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×8 | 0 | 1 |
| Siddur Rashi | סידור רש"י | סידור | Halakhah / Rishonim | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×361, אדני×1, יי×1 | 0 | 1000 |
| Sidduro Shel Shabbat | סדורו של שבת | סידור | Chasidut / Other Chasidut Works | 23/20 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×350, אדני×1 | 3 | 181 |
| Simchat HaRegel on Pesach Haggadah | שמחת הרגל על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 34/30 | 2 | 1 | unknown | 5% | 0% | ה׳ (קיצור)×151, יהוה×24 | 2 | 19 |
| Steinsaltz on Mishneh Torah, Prayer and the Priestly Blessing | ביאור שטיינזלץ על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Steinsaltz / Sefer Ahavah | 1/1 | 0 | 1 | Copyright: Steinsaltz Center | 30% | 0% | ה׳ (קיצור)×57, יי×6, אדני×1 | 0 | 388 |
| Steinsaltz on Mishneh Torah, The Order of Prayer | ביאור שטיינזלץ על משנה תורה, סדר התפילה | סידור | Halakhah / Mishneh Torah / Commentary / Steinsaltz / Sefer Ahavah | 1/1 | 0 | 1 | Copyright: Steinsaltz Center | 21% | 0% | ה׳ (קיצור)×31, יי×7 | 0 | 54 |
| Tevele Bondi on Pesach Haggadah | טעבעלה באנדי על הגדה של פסח  | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 0 | 2 |
| The Jonathan Sacks Haggadah | הגדת הרב יונתן זקס | הגדה | Liturgy / Haggadah / Commentary | 34/30 | 2 | 0 | — | — | — | — | 17 | 24 |
| The Jonathan Sacks Haggadah; Essays | פסח על שום מה? הגדת הרב יונתן זקס; מאמרים | הגדה | Jewish Thought / Modern / Rabbi Lord Jonathan Sacks | 22/21 | 1 | 0 | — | — | — | — | 5 | 120 |
| Tikkun HaKlali | תיקון הכללי | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 98% | 27% | יהוה×65, אדני×8 | 3 | 6 |
| Tzafnat Pa'neach on Mishneh Torah, Prayer and the Priestly Blessing | צפנת פענח על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Tzafnat Pa'neach / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×12 | 2 | 2 |
| Tziunei Maharan on Mishneh Torah, Prayer and the Priestly Blessing | ציוני מהר"ן על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Tziunei Maharan / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×2 | 2 | 0 |
| Unetaneh Tokef | ונתנה תוקף | אחר | Liturgy / High Holidays | 1/1 | 0 | 2 | unknown | 100% | 0% | — | 0 | 2 |
| Yad Eitan on Mishneh Torah, Prayer and the Priestly Blessing | יד איתן על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Yad Eitan / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | — | 0 | 2 |
| Yedid Nefesh | ידיד נפש | פיוטים | Liturgy / Piyutim | 1/1 | 0 | 4 | CC-BY-SA, unknown | 68% | 2% | — | 0 | 0 |
| Yismach Yisrael on Pesach Haggadah | ישמח ישראל על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 43/38 | 2 | 0 | — | — | — | — | 0 | 0 |
| Yitzchak Yeranen on Mishneh Torah, Prayer and the Priestly Blessing | יצחק ירנן על משנה תורה, הלכות תפילה וברכת כהנים | סידור | Halakhah / Mishneh Torah / Commentary / Yitzchak Yeranen / Sefer Ahavah | 1/1 | 0 | 1 | Public Domain | 0% | 0% | ה׳ (קיצור)×5 | 0 | 12 |
| Yizkor | יזכור | אחר | Liturgy / Other Liturgy Works | 1/1 | 0 | 1 | unknown | 92% | 0% | יי×2, ה׳ (קיצור)×2 | 0 | 7 |
| Zeroa Yamin on Pesach Haggadah | זרוע ימין על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 18/14 | 2 | 1 | unknown | 0% | 0% | ה׳ (קיצור)×80, אדני×2 | 1 | 3 |
| Zevach Pesach on Pesach Haggadah | זבח פסח על הגדה של פסח | הגדה | Liturgy / Haggadah / Commentary | 45/40 | 2 | 2 | Public Domain, unknown | 1% | 0% | ה׳ (קיצור)×52 | 3 | 26 |

### Akdamut Milin — אַקְדָּמוּת מִלִּין

- דוגמת ref לעלה: `Akdamut Milin`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Piyyut / Verse; צמתים בלי heTitle: 0
- דגימה: 90 מחרוזות, 463 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: —
  - דגימה `Akdamut Milin` [According to the NLI Piyyut database]: HTTP 200, קינון 2, 90 מחרוזות

### Annotations of Maharatz Chajes on Mishneh Torah, Prayer and the Priestly Blessing — חידושים ומקורים מהר"ץ חיות על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Annotations of Maharatz Chajes on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 1 מחרוזות, 78 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×1
- תגיות HTML: b×1
- מילות הוראה: כאן×1
- פיסוק: מרכאות (")×12, פסיק×5, גרש לטיני (')×4, נקודה×2, נקודתיים×1
  - דגימה `Annotations of Maharatz Chajes on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 1 מחרוזות

### Annotations of Minchat Chinukh on Mishneh Torah, Prayer and the Priestly Blessing — חידושים ומקורים מבעל מנחת חינוך על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Annotations of Minchat Chinukh on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 2 מחרוזות, 90 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×1
- תגיות HTML: b×2
- מילות הוראה: אומרים×1, אומר×1, בשבת×1
- פיסוק: מרכאות (")×23, גרש לטיני (')×6, נקודה×4, נקודתיים×2, פסיק×1
  - דגימה `Annotations of Minchat Chinukh on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 2 מחרוזות

### Annotations of R' Yeshaya Berlin on Mishneh Torah, Prayer and the Priestly Blessing — חידושים והגהות הגרי"ב על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Annotations of R' Yeshaya Berlin on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 1 מחרוזות, 189 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×6
- תגיות HTML: b×2
- מילות הוראה: אומר×1, בתענית×1
- פיסוק: גרש לטיני (')×19, מרכאות (")×18, נקודה×8, פסיק×2, נקודתיים×1
  - דגימה `Annotations of R' Yeshaya Berlin on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 1 מחרוזות

### Azharot of Solomon ibn Gabirol — אזהרות לרבי שלמה אבן גבירול

- דוגמת ref לעלה: `Azharot of Solomon ibn Gabirol, Prelude`
- עומק טקסט בעלים: {'1': 4}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Prelude (רשות); Positive Commandments (מצוות עשה); Negative Commandments (מצוות לא תעשה); Postscript (חתימה)
- דגימה: 275 מחרוזות, 2777 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×3
- תגיות HTML: b×11
- מילות הוראה: בשבת×2, הקהל×1
- פיסוק: נקודה×824, נקודתיים×275
  - דגימה `Azharot of Solomon ibn Gabirol, Prelude` [Vilna, 1879 -- vocalized]: HTTP 200, קינון 1, 20 מחרוזות
  - דגימה `Azharot of Solomon ibn Gabirol, Positive Commandments` [Vilna, 1879 -- vocalized]: HTTP 200, קינון 1, 91 מחרוזות
  - דגימה `Azharot of Solomon ibn Gabirol, Negative Commandments` [Vilna, 1879 -- vocalized]: HTTP 200, קינון 1, 156 מחרוזות
  - דגימה `Azharot of Solomon ibn Gabirol, Postscript` [Vilna, 1879 -- vocalized]: HTTP 200, קינון 1, 8 מחרוזות

### Barukh SheAmar on Pesach Haggadah — ברוך שאמר על הגדה של פסח

- דוגמת ref לעלה: `Barukh SheAmar on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 3 מחרוזות, 541 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×3, sup×1, i×1
- דוגמאות בסוגריים: «י״ב ב׳» · «כ״ט א׳» · «למשה ולאהרן» · «כ׳» · «סוטה ל״ח א׳»
- מילות הוראה: בר״ח×1, כאן×1, אומר×1
- פיסוק: פסיק×57, גרשיים (״)×33, נקודה×23, גרש (׳)×15, קו ארוך (—)×6
  - דגימה `Barukh SheAmar on Pesach Haggadah, Kadesh` [Barukh Sheamar on Haggadah, Tel Aviv 1968]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Barukh SheAmar on Pesach Haggadah, Kadesh.
  - דגימה `Barukh SheAmar on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Barukh Sheamar on Haggadah, Tel Aviv 1968]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Barukh SheAmar on Pesach Haggadah, Motzi Matzah` [Barukh Sheamar on Haggadah, Tel Aviv 1968]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Barukh SheAmar on Pesach Haggadah, Motzi Matzah.
  - דגימה `Barukh SheAmar on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Barukh Sheamar on Haggadah, Tel Aviv 1968]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Barukh SheAmar on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Barukh SheAmar on Pesach Haggadah, Nirtzah, Chad Gadya` [Barukh Sheamar on Haggadah, Tel Aviv 1968]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Barukh SheAmar on Pesach Haggadah, Nirtzah, Chad Gadya.

### Batei HaNefesh on Pesach Haggadah — בתי הנפש על הגדה של פסח

- דוגמת ref לעלה: `Batei HaNefesh on Pesach Haggadah, Magid, Ha Lachma Anya`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Magid (מגיד); Barech (ברך); Hallel (הלל)
- דגימה: 32 מחרוזות, 6483 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×50, אדני×2
- תגיות HTML: b×58, br×26
- דוגמאות בסוגריים: «כאלו כתיב מלא עד"ש רבינו האר"י זצ"ל בתיב' צפנה»
- מילות הוראה: כאן×5, אומר×3, בשבת×2, בחול×2, אומרים×1, עד כאן×1
- פיסוק: מרכאות (")×597, גרש לטיני (')×287, נקודה×284, נקודתיים×49, פסיק×5
  - דגימה `Batei HaNefesh on Pesach Haggadah, Magid, Ha Lachma Anya` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Batei HaNefesh on Pesach Haggadah, Magid, Story of the Five Rabbis` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 5 מחרוזות
  - דגימה `Batei HaNefesh on Pesach Haggadah, Magid, First Fruits Declaration` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 16 מחרוזות
  - דגימה `Batei HaNefesh on Pesach Haggadah, Magid, First Half of Hallel` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Batei HaNefesh on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 7 מחרוזות

### Ben Aryeh on Mishneh Torah, Prayer and the Priestly Blessing — בן אריה על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Ben Aryeh on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 13 מחרוזות, 355 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×1
- תגיות HTML: b×13
- דוגמאות בסוגריים: «ולא כתב מקורו»
- מילות הוראה: ש"ץ×1, כאן×1
- פיסוק: מרכאות (")×77, גרש לטיני (')×39, נקודה×20, נקודתיים×17
  - דגימה `Ben Aryeh on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 13 מחרוזות

### Benei Binyamin on Mishneh Torah, Prayer and the Priestly Blessing — בני בנימין על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Benei Binyamin on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 45 מחרוזות, 2004 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×79
- דוגמאות בסוגריים: «וע' בבאורו סי' צ"ט סק"י»
- מילות הוראה: כאן×3, בחול×2, אומר×1, בשבת×1, ש"ץ×1
- פיסוק: מרכאות (")×566, נקודה×216, גרש לטיני (')×186, נקודתיים×46, פסיק×2
  - דגימה `Benei Binyamin on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 45 מחרוזות

### Birkat Avraham on Mishneh Torah, Prayer and the Priestly Blessing — ברכת אברהם על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Birkat Avraham on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 2 מחרוזות, 647 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×6, br×2
- מילות הוראה: אומר×1, כאן×1
- פיסוק: גרש לטיני (')×30, מרכאות (")×7, נקודה×5
  - דגימה `Birkat Avraham on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 2 מחרוזות

### Birkat Hamazon — ברכת המזון

- דוגמת ref לעלה: `Birkat Hamazon, Preliminary Psalms`
- עומק טקסט בעלים: {'1': 10}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Preliminary Psalms (לפני ברכת המזון); Zimmun (זימון); Blessing on the Food (ברכת הזן); Blessing on the Land (ברכת הארץ); Blessing on Jerusalem (ברכת בונה ירושלים); Hatov Vehametiv (ברכת הטוב והמטיב); Blessings After Other Foods (ברכה אחרונה); HaRachaman of Brit Milah (הרחמן לברית מילה); Sheva Brachot (שבע ברכות)
- דגימה: 23 מחרוזות, 575 מילים; ניקוד 96%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×18, יהוה×9
- תגיות HTML: small×10, br×4, b×2
- דוגמאות `<small>`: «ביום שאומרים בו תחנון:» · «ביום שאין אומרים בו תחנון:» · «בשבת» · «בראש-חודש ובמועדים» · «בראש חודש—»
- דוגמאות בסוגריים: «תָּמִיד»
- מילות הוראה: אומרים×2, אומר×2, בשבת×1, בראש חודש×1
- פיסוק: פסיק×48, נקודה×41, קו ארוך (—)×6, מקף לטיני (-)×3, נקודתיים×2, מקף (־)×2, נקודה-פסיק×1
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 10/15
  - דגימה `Birkat Hamazon, Preliminary Psalms` [Birkat Hamazon -- Ashkenaz]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Birkat Hamazon, Blessing on the Food` [Birkat Hamazon -- Ashkenaz]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Birkat Hamazon, Blessing on Jerusalem` [Birkat Hamazon -- Ashkenaz]: HTTP 200, קינון 1, 11 מחרוזות
  - דגימה `Birkat Hamazon, Blessings After Other Foods, Bore Nefashot` [Birkat Hamazon -- Ashkenaz]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Birkat Hamazon, Sheva Brachot` [Birkat Hamazon -- Ashkenaz]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Birkat Hamazon, Preliminary Psalms` [Brit Mila Additions ]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

### Chiddushei Rabbi Akiva Eiger on Mishneh Torah, Prayer and the Priestly Blessing — חידושי רבי עקיבא איגר על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Chiddushei Rabbi Akiva Eiger on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 167 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×3
- דוגמאות בסוגריים: «נעה"ג» · «וכתב הר' מנוח וכו'» · «נעה"ג» · «נעה"ג»
- מילות הוראה: —
- פיסוק: מרכאות (")×27, גרש לטיני (')×14, נקודה×3
  - דגימה `Chiddushei Rabbi Akiva Eiger on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 3 מחרוזות

### Commentary of Ritva on Pesach Haggadah — ביאור הריטב"א על הגדה של פסח

- דוגמת ref לעלה: `Commentary of Ritva on Pesach Haggadah, Magid, Ha Lachma Anya`
- עומק טקסט בעלים: {'2': 15}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Magid (מגיד); Maror (מרור); Tzafun (צפון); Barech (ברך)
- דגימה: 28 מחרוזות, 2587 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×18
- תגיות HTML: b×21, small×3, br×3
- דוגמאות `<small>`: «]א"ה, נראה שחסר כאן, שלא נתפרש ענין הבנים שלאחר זמן, וכן במש"כ רבינו להלן הם ג"כ» · «בגליון הכת"י כתוב» · «עכ"ל»
- דוגמאות בסוגריים: «פסחים מ"ח א'» · «עירובין פ"ג ב'» · «פסחים צ"ט ב' ק"ז ב'» · «פסחים קי"ב א'» · «שמות ג׳:י״ב»
- מילות הוראה: אומר×17, אומרים×11, יש אומרים×5, כאן×4, נוהגים×1
- פיסוק: פסיק×180, נקודה×85, גרש לטיני (')×72, מרכאות (")×65, נקודתיים×18, גרש (׳)×17, גרשיים (״)×16, מקף לטיני (-)×1
  - דגימה `Commentary of Ritva on Pesach Haggadah, Magid, Ha Lachma Anya` [Ritva's Commentary -- Wikisource]: HTTP 200, קינון 2, 7 מחרוזות
  - דגימה `Commentary of Ritva on Pesach Haggadah, Magid, The Four Sons` [Ritva's Commentary -- Wikisource]: HTTP 200, קינון 2, 12 מחרוזות
  - דגימה `Commentary of Ritva on Pesach Haggadah, Magid, The Ten Plagues` [Ritva's Commentary -- Wikisource]: HTTP 200, קינון 2, 4 מחרוזות
  - דגימה `Commentary of Ritva on Pesach Haggadah, Magid, First Half of Hallel` [Ritva's Commentary -- Wikisource]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Commentary of Ritva on Pesach Haggadah, Barech, Third Cup of Wine` [Ritva's Commentary -- Wikisource]: HTTP 200, קינון 2, 2 מחרוזות

### Divrei Negidim on Pesach Haggadah — דברי נגידים על הגדה של פסח

- דוגמת ref לעלה: `Divrei Negidim on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 7 מחרוזות, 2887 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×25, אדני×1
- תגיות HTML: br×8, b×6
- דוגמאות בסוגריים: «משלי ח׳»
- מילות הוראה: נוהגים×3, בשבת×1, כאן×1, עד כאן×1, אומרים×1, אומר×1, יש אומרים×1
- פיסוק: נקודה×208, גרשיים (״)×75, גרש (׳)×65, נקודתיים×9, פסיק×1
  - דגימה `Divrei Negidim on Pesach Haggadah, Kadesh` [Haggadah shel Pesach LaMaharal, London, 1960]: HTTP 200, קינון 2, 5 מחרוזות
  - דגימה `Divrei Negidim on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Haggadah shel Pesach LaMaharal, London, 1960]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Divrei Negidim on Pesach Haggadah, Motzi Matzah` [Haggadah shel Pesach LaMaharal, London, 1960]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Divrei Negidim on Pesach Haggadah, Motzi Matzah.
  - דגימה `Divrei Negidim on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Haggadah shel Pesach LaMaharal, London, 1960]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Divrei Negidim on Pesach Haggadah, Nirtzah, Chad Gadya` [Haggadah shel Pesach LaMaharal, London, 1960]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Divrei Negidim on Pesach Haggadah, Nirtzah, Chad Gadya.

### Divrei Yirmiyahu on Mishneh Torah, Prayer and the Priestly Blessing — דברי ירמיהו על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Divrei Yirmiyahu on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 146 מחרוזות, 38393 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×124
- תגיות HTML: b×342, br×196
- דוגמאות בסוגריים: «תהילים קי״ט:נ״ז» · «ועיין בתוספות מגילה י"ז ע"ב בד"ה הסדיר נפק"מ לדינא בהסדר בטעה עיי"ש» · «מנחות דף מ"ב ע"ב» · «השנה» · «קי"ג»
- מילות הוראה: אומר×41, כאן×27, בשבת×16, ש"ץ×12, אומרים×11, בר"ח×6, בחנוכה×4, בתענית×4
- פיסוק: מרכאות (")×4993, גרש לטיני (')×2106, נקודה×1203, נקודתיים×338, גרשיים (״)×2, פסיק×2
  - דגימה `Divrei Yirmiyahu on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 146 מחרוזות

### Ephod Bad on Pesach Haggadah — אפוד בד על הגדה של פסח

- דוגמת ref לעלה: `Ephod Bad on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 11 מחרוזות, 1375 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×27
- תגיות HTML: b×16
- דוגמאות בסוגריים: «הוריות» · «עיין זוה"ק פ' ויקהל» · «מדרש איכה» · «נחמיה ט׳:ד׳-ה׳» · «סוכה נ"ב ע"א»
- מילות הוראה: אומרים×2, אומר×2
- פיסוק: פסיק×102, מרכאות (")×95, נקודה×55, גרש לטיני (')×42, גרש (׳)×3, נקודתיים×2, מקף לטיני (-)×1
  - דגימה `Ephod Bad on Pesach Haggadah, Kadesh` [Haggadah Ephod Bad, Warsaw, 1872]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Ephod Bad on Pesach Haggadah, Kadesh.
  - דגימה `Ephod Bad on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Haggadah Ephod Bad, Warsaw, 1872]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Ephod Bad on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh.
  - דגימה `Ephod Bad on Pesach Haggadah, Motzi Matzah` [Haggadah Ephod Bad, Warsaw, 1872]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Ephod Bad on Pesach Haggadah, Motzi Matzah.
  - דגימה `Ephod Bad on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Haggadah Ephod Bad, Warsaw, 1872]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Ephod Bad on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Ephod Bad on Pesach Haggadah, Nirtzah, Chad Gadya` [Haggadah Ephod Bad, Warsaw, 1872]: HTTP 200, קינון 2, 11 מחרוזות

### Even Ha'azel on Mishneh Torah, Prayer and the Priestly Blessing — אבן האזל על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Even Ha'azel on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 4 מחרוזות, 1780 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×15, br×11
- מילות הוראה: אומר×2, בשבת×1, בחנוכה×1, בפורים×1, אומרים×1, ש"ץ×1, כאן×1
- פיסוק: מרכאות (")×153, פסיק×80, גרש לטיני (')×47, נקודה×16
  - דגימה `Even Ha'azel on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 4 מחרוזות

### Geulat Olam on Pesach Haggadah — גאולת עולם על הגדה של פסח

- דוגמת ref לעלה: `Geulat Olam on Pesach Haggadah, Magid, Ha Lachma Anya`
- עומק טקסט בעלים: {'2': 15}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Magid (מגיד); Barech (ברך); Hallel (הלל)
- דגימה: 27 מחרוזות, 5838 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×50, אדני×1
- תגיות HTML: b×48, br×21, small×1
- דוגמאות `<small>`: «בע״ט חי"ה הרומז״ת משיב אמרים, קצת פירוש ההגדה שנים שלשה גרגירים, שלמי חגיגה זובח»
- דוגמאות בסוגריים: «פסחים דף מ'» · «פסחים דף מ'»
- מילות הוראה: אומר×11, כאן×3, בר"ח×1, עד כאן×1, בשבת×1
- פיסוק: מרכאות (")×474, גרש לטיני (')×233, פסיק×139, נקודה×90, גרשיים (״)×4, נקודתיים×1
  - דגימה `Geulat Olam on Pesach Haggadah, Magid, Ha Lachma Anya` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Geulat Olam on Pesach Haggadah, Magid, The Four Sons` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 6 מחרוזות
  - דגימה `Geulat Olam on Pesach Haggadah, Magid, First Fruits Declaration` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 10 מחרוזות
  - דגימה `Geulat Olam on Pesach Haggadah, Magid, Rabban Gamliel's Three Things` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Geulat Olam on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 7 מחרוזות

### Hadran — הדרן

- דוגמת ref לעלה: `Hadran`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Hadran; צמתים בלי heTitle: 0
- דגימה: 6 מחרוזות, 443 מילים; ניקוד 97%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×7
- תגיות HTML: small×7
- דוגמאות `<small>`: «(יאמר שם המסכת)» · «(יאמר שם המסכת)» · «(יאמר שם המסכת)» · «(יאמר שם המסכת)» · «בעשי"ת»
- דוגמאות בסוגריים: «יאמר שם המסכת» · «יאמר שם המסכת» · «יאמר שם המסכת» · «יאמר שם המסכת» · «בעשי"ת  לְעֵלָּא לְעֵלָּא מִכָּל»
- מילות הוראה: בעשי"ת×1
- פיסוק: נקודה×37, פסיק×21, נקודתיים×11, מרכאות (")×3
  - דגימה `Hadran` [Wikipedia Hadran]: HTTP 200, קינון 1, 6 מחרוזות

### Hadran for Tanakh — הדרן לספרי התנ"ך

- דוגמת ref לעלה: `Hadran for Tanakh`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 363 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×8
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: פסיק×19, נקודה×17, מרכאות (")×8, גרש לטיני (')×8, מקף לטיני (-)×1
  - דגימה `Hadran for Tanakh` [Rav Yona Reiss's version]: HTTP 200, קינון 1, 3 מחרוזות

### Hallel — הלל

- דוגמת ref לעלה: `Hallel`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- דגימה: 15 מחרוזות, 737 מילים; ניקוד 97%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יהוה×66
- תגיות HTML: small×2
- דוגמאות `<small>`: «בר"ח ובחוה"מ פסח גם שני הימים האחרונים של פסח מדלגין זה:» · «בר"ח ובחוה"מ פסח גם שני הימים האחרונים של פסח מדלגין זה:»
- מילות הוראה: בר"ח×2
- פיסוק: נקודתיים×94, נקודה×81, פסיק×31, מרכאות (")×4, מקף לטיני (-)×4
  - דגימה `Hallel` [Public Domain]: HTTP 200, קינון 1, 15 מחרוזות

### Hasagot HaRa'avad on Mishneh Torah, Prayer and the Priestly Blessing — השגות הראב"ד על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Hasagot HaRa'avad on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 13 מחרוזות, 499 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×13
- מילות הוראה: אומר×5, אומרים×2, בשבת×1, כאן×1, החזן×1
- פיסוק: מרכאות (")×40, נקודה×14, נקודתיים×13, גרש לטיני (')×12, פסיק×4
  - דגימה `Hasagot HaRa'avad on Mishneh Torah, Prayer and the Priestly Blessing` [ToratEmet]: HTTP 200, קינון 3, 13 מחרוזות

### Kabbalat Shabbat — קבלת שבת

- דוגמת ref לעלה: `Kabbalat Shabbat`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Psalm; צמתים בלי heTitle: 0
- דגימה: 6 מחרוזות, 550 מילים; ניקוד 96%, טעמים 76%, קמץ קטן (U+05C7) ×0, מתג ×153
- שם ה׳: יהוה×49
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: נקודה×65, מקף (־)×62, פסק (׀)×13, פסיק×2
  - דגימה `Kabbalat Shabbat` [Siddur Sefas Yisroel- Kabbolas Shabbos]: HTTP 200, קינון 1, 6 מחרוזות

### Kessef Mishneh on Mishneh Torah, Prayer and the Priestly Blessing — כסף משנה על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Kessef Mishneh on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 504 מחרוזות, 27201 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×36
- תגיות HTML: b×504, small×15, i×1
- דוגמאות `<small>`: «(ד-ה)» · «(יא-יב)» · «(ב-ג)» · «(ד-ה)» · «(ח-ט)»
- דוגמאות בסוגריים: «דף ב' ע"א» · «דף כ"א ע"א» · «יבמות דף פ"ט.» · «ברכות דף כ':» · «ברכות דף ל״ב.»
- מילות הוראה: אומר×74, כאן×27, בשבת×24, אומרים×19, שליח ציבור×16, נוהגים×8, בחול×7, ביום טוב×6
- פיסוק: מרכאות (")×1499, נקודה×970, גרש לטיני (')×753, נקודתיים×587, גרשיים (״)×294, פסיק×38, מקף לטיני (-)×15
  - דגימה `Kessef Mishneh on Mishneh Torah, Prayer and the Priestly Blessing` [Torat Emet 363]: HTTP 200, קינון 3, 504 מחרוזות

### Keter Malkhut — כתר מלכות

- דוגמת ref לעלה: `Keter Malkhut`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Chapter / Paragraph; צמתים בלי heTitle: 0
- דגימה: 486 מחרוזות, 7300 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×35, אדני×2, ה׳ (קיצור)×1
- תגיות HTML: b×36, small×4, big×1, strong×1, sup×1, i×1
- דוגמאות `<small>`: «וְהִיא תְּהִלָּה וְוִדּוּי וּתְפִלָּה אֲשֶׁר נָהֲגוּ הַיְרֵאִים וְאַנְשֵׁי מַעֲש» · «בִּתְפִלָּתִי יִסְכָּן־גָּבֶר. כִּי בָהּ יִלְמַד יֹשֶׁר וּזְכוּת:» · «סִפַּרְתִּי בָהּ פִּלְאֵי אֵל חַי בִּקְצָרָה אַךְ לֹא בַאֲרִיכוּת:» · «שַׂמְתִּיהָ עַל רֹאשׁ מַהֲלָלַי. וּקְרָאתִיהָ כֶּתֶר מַלְכוּת:»
- מילות הוראה: אומרים×2, אומר×2, בחול×2, כאן×1
- פיסוק: נקודה×1161, נקודתיים×480, גרש לטיני (')×2, מרכאות (")×2, מקף (־)×1
  - דגימה `Keter Malkhut` [Tikkun Midot HaNefesh, Jerusalem 1996]: HTTP 200, קינון 1, 39 מחרוזות
  - דגימה `Keter Malkhut` [Mahberet miShire Kodesh, I. Davidson. JPS, Philadelphia, 1923]: HTTP 200, קינון 2, 447 מחרוזות

### Ketubah Text — נוסח הכתובה

- דוגמת ref לעלה: `Ketubah Text`
- עומק טקסט בעלים: {'1': 1}; sectionNames: section; צמתים בלי heTitle: 0
- דגימה: 8 מחרוזות, 1239 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: —
- דוגמאות בסוגריים: «התנאים שהתנו ביניהם שרירין וקיימין כתנאי  בני גד ובני ראובן ואלו הן: מעשה ידיה ל»
- מילות הוראה: בשבת×4, כאן×4
- פיסוק: נקודה×95, פסיק×17, מרכאות (")×7, נקודתיים×1
  - דגימה `Ketubah Text` [RCA Ketubah Text]: HTTP 200, קינון 1, 8 מחרוזות

### Kimcha Davshuna on Pesach Haggadah — קמחא דאבישונא על הגדה של פסח

- דוגמת ref לעלה: `Kimcha Davshuna on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 8 מחרוזות, 1776 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×7
- תגיות HTML: b×7
- מילות הוראה: בשבת×3, אומר×3, כאן×1, ביום טוב×1, אומרים×1
- פיסוק: נקודה×136, גרש לטיני (')×111, מרכאות (")×33
  - דגימה `Kimcha Davshuna on Pesach Haggadah, Kadesh` [Mahzor Roma, Bologna 1540]: HTTP 200, קינון 2, 5 מחרוזות
  - דגימה `Kimcha Davshuna on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Mahzor Roma, Bologna 1540]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Kimcha Davshuna on Pesach Haggadah, Motzi Matzah` [Mahzor Roma, Bologna 1540]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kimcha Davshuna on Pesach Haggadah, Motzi Matzah.
  - דגימה `Kimcha Davshuna on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Mahzor Roma, Bologna 1540]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Kimcha Davshuna on Pesach Haggadah, Nirtzah, Chad Gadya` [Mahzor Roma, Bologna 1540]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kimcha Davshuna on Pesach Haggadah, Nirtzah, Chad Gadya.

### Kiryat Sefer on Mishneh Torah, Prayer and the Priestly Blessing — קרית ספר על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Kiryat Sefer on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 24 מחרוזות, 2469 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×16
- תגיות HTML: b×24
- דוגמאות בסוגריים: «ע» · «הוא חסר»
- מילות הוראה: אומר×5, כאן×4, שליח ציבור×1, בר"ח×1, אומרים×1
- פיסוק: גרש לטיני (')×57, נקודה×51, מרכאות (")×44, נקודתיים×10
  - דגימה `Kiryat Sefer on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 24 מחרוזות

### Kos Eliyahu on Pesach Haggadah — כוס אליהו על הגדה של פסח

- דוגמת ref לעלה: `Kos Eliyahu on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
  - דגימה `Kos Eliyahu on Pesach Haggadah, Kadesh` [Haggadah Kos Eliyahu. Djerba, 1938]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kos Eliyahu on Pesach Haggadah, Kadesh.
  - דגימה `Kos Eliyahu on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Haggadah Kos Eliyahu. Djerba, 1938]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kos Eliyahu on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh.
  - דגימה `Kos Eliyahu on Pesach Haggadah, Motzi Matzah` [Haggadah Kos Eliyahu. Djerba, 1938]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kos Eliyahu on Pesach Haggadah, Motzi Matzah.
  - דגימה `Kos Eliyahu on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Haggadah Kos Eliyahu. Djerba, 1938]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kos Eliyahu on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Kos Eliyahu on Pesach Haggadah, Nirtzah, Chad Gadya` [Haggadah Kos Eliyahu. Djerba, 1938]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Kos Eliyahu on Pesach Haggadah, Nirtzah, Chad Gadya.

### Kovetz Al Yad HaChazakah on Mishneh Torah, Prayer and the Priestly Blessing — קובץ על היד החזקה על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Kovetz Al Yad HaChazakah on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 39 מחרוזות, 4698 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×6
- תגיות HTML: b×45, br×6
- דוגמאות בסוגריים: «פירוש שצריכין לכנוס לסעודה גדולה»
- מילות הוראה: אומר×7, כאן×4, אומרים×2, ש"ץ×2, בשבת×1, בר"ח×1
- פיסוק: מרכאות (")×755, גרש לטיני (')×242, נקודה×72, נקודתיים×45, פסיק×3
  - דגימה `Kovetz Al Yad HaChazakah on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 39 מחרוזות

### Lechem Mishneh on Mishneh Torah, Prayer and the Priestly Blessing — לחם משנה על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Lechem Mishneh on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 172 מחרוזות, 10536 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×7
- תגיות HTML: b×171, br×2
- דוגמאות בסוגריים: «ברכות דף כ':» · «ברכות דף ל"ב» · «ברכות דף כ"ו ע"ב» · «ברכות דף כ"ז ע"ב» · «ברכות דף כ"א.»
- מילות הוראה: אומר×32, כאן×18, בשבת×6, אומרים×5, עד כאן×4, ביום טוב×1, בחול×1, נוהגים×1
- פיסוק: גרש לטיני (')×493, מרכאות (")×464, נקודה×335, גרשיים (״)×244, נקודתיים×222, פסיק×13, מקף לטיני (-)×4, נקודה-פסיק×4
  - דגימה `Lechem Mishneh on Mishneh Torah, Prayer and the Priestly Blessing` [ToratEmet]: HTTP 200, קינון 3, 171 מחרוזות
  - דגימה `Lechem Mishneh on Mishneh Torah, Prayer and the Priestly Blessing` [Rambam]: HTTP 200, קינון 3, 1 מחרוזות

### Lekha Dodi — לְכָה דוֹדִי

- דוגמת ref לעלה: `Lekha Dodi`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Section / Paragraph; צמתים בלי heTitle: 0
- דגימה: 38 מחרוזות, 142 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×3
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: גרש לטיני (')×3
  - דגימה `Lekha Dodi` [Wikisource]: HTTP 200, קינון 2, 38 מחרוזות

### Leshon Chakhamim — לשון חכמים

- דוגמת ref לעלה: `Leshon Chakhamim, Part I`
- עומק טקסט בעלים: {'1': 2, '2': 2}; sectionNames: Paragraph, Siman / Paragraph; צמתים בלי heTitle: 4
- צמתים ברמה הראשונה: Part I (חלק ראשון); Part II (חלק שני)
- דגימה: 8558 מחרוזות, 268590 מילים; ניקוד 40%, טעמים 16%, קמץ קטן (U+05C7) ×1142, מתג ×18778
- שם ה׳: יהוה×3636, ה׳ (קיצור)×620, אדני×310, יי×8
- תגיות HTML: b×7354, small×2100, big×378, strong×378, br×4
- דוגמאות `<small>`: «יתחכמו החכמים ויתבוננו הנבונים. הלא זאת מודעת היא ששלימות נפש האדם בעוה״ז היא תל» · «ושני מיני עמל אלו הם בפה, כי הפה משמש שני מלאכות אחת של הכנסה שהוא אכילה ושתיה, » · «והנה עמל תורה שהוא רוחני וקדוש מוכח מתוכו שמלאכתו היא מלאכת הקודש יען כי הוא נגד» · «ובראשית מאמר אגישה לפני הקוראים הנאמנים ענין הנוגע לאכילה שהוא מלאכה גדולה במלאכ» · «יאמר קודם נטילת ידים»
- דוגמאות בסוגריים: «בקהלת ו׳:ז׳» · «במשלי ט״ו:ב׳» · «יהו״ה» · «יו״ד ה״י ד״ו ה״י» · «יו״ד ה״י וי״ו ה״י»
- מילות הוראה: אומר×146, כאן×108, בתענית×106, בשבת×68, אומרים×52, בחול×14, ביום טוב×8, הקהל×8
- פיסוק: גרשיים (״)×11762, נקודה×11138, פסיק×8604, מקף (־)×7512, סוף פסוק (׃)×4408, נקודתיים×2920, גרש (׳)×2756, פסק (׀)×1180
  - דגימה `Leshon Chakhamim, Part I` [Bakhshi Edition, 2021]: HTTP 200, קינון 2, 2759 מחרוזות
  - דגימה `Leshon Chakhamim, Part I` [Bakhshi Edition, 2021]: HTTP 200, קינון 2, 2759 מחרוזות
  - דגימה `Leshon Chakhamim, Part II` [Bakhshi Edition, 2021]: HTTP 200, קינון 2, 1520 מחרוזות
  - דגימה `Leshon Chakhamim, Part II` [Bakhshi Edition, 2021]: HTTP 200, קינון 2, 1520 מחרוזות

### Lev Shalem on Mishneh Torah, Prayer and the Priestly Blessing — לב שלם על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Lev Shalem on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 2794 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×21
- תגיות HTML: b×28, br×25
- מילות הוראה: כאן×2, עד כאן×2, אומר×1
- פיסוק: מרכאות (")×294, גרש לטיני (')×111, נקודה×84
  - דגימה `Lev Shalem on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 3 מחרוזות

### Ma'avar Yabbok — מעבר יבק

- דוגמת ref לעלה: `Ma'avar Yabbok`
- עומק טקסט בעלים: {'1': 2, '2': 8}; sectionNames: Chapter / Paragraph, Paragraph, Section / Paragraph; צמתים בלי heTitle: 2
- צמתים ברמה הראשונה:  (); Author's Introduction (הקדמת המחבר); Siftei Tzedek (שפתי צדק);  (); Siftei Renanot (שפתי רננות); Atar Anan HaKetoret (עתר ענן הקטורת); Korban Ta'anit (קרבן תענית); Minchat Aharon (מנחת אהרן); Imrei Noam (אמרי נעם); Epilogue (חתימת הספר)
- דגימה: 618 מחרוזות, 106846 מילים; ניקוד 27%, טעמים 0%, קמץ קטן (U+05C7) ×175, מתג ×9
- שם ה׳: יי×1023, ה׳ (קיצור)×428, יהוה×276, אדני×96
- תגיות HTML: small×326, b×296, br×6
- דוגמאות `<small>`: «יהא רעוא. דאימא מלתא. דתתקבל ברעוא. קדם מלכא רמא. וקדם צדקיא:» · «ובו שמונה סדרים» · «קודם שיתחיל כל סדר יאמר זה» · «ג"פ» · «יאמר מזמור סימן י"ג או ט"ו או ט"ז או י"ז.»
- דוגמאות בסוגריים: «תהלים יג» · «תהלים טו» · «תהלים טז» · «תהלים יז» · «תורה»
- מילות הוראה: אומר×80, בשבת×37, אומרים×36, כאן×30, בחול×8, הקהל×7, נוהגים×7, עד כאן×4
- פיסוק: מרכאות (")×3490, נקודה×2952, נקודתיים×2323, גרש לטיני (')×2000, מקף (־)×989, סוף פסוק (׃)×925, פסיק×29, פסק (׀)×14
  - דגימה `Ma'avar Yabbok` [Vilna, 1860]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Ma'avar Yabbok', please pass a more specific ref for this book, and try again. 'Ma'avar Yabbok' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://developers.sefa
  - דגימה `Ma'avar Yabbok, Siftei Tzedek` [Vilna, 1860]: HTTP 200, קינון 2, 420 מחרוזות
  - דגימה `Ma'avar Yabbok, Siftei Renanot` [Vilna, 1860]: HTTP 200, קינון 2, 49 מחרוזות
  - דגימה `Ma'avar Yabbok, Minchat Aharon` [Vilna, 1860]: HTTP 200, קינון 2, 147 מחרוזות
  - דגימה `Ma'avar Yabbok, Epilogue` [Vilna, 1860]: HTTP 200, קינון 1, 2 מחרוזות

### Maaseh Nissim on Pesach Haggadah — מעשה ניסים על הגדה של פסח

- דוגמת ref לעלה: `Maaseh Nissim on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 15 מחרוזות, 1050 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×12, br×1
- דוגמאות בסוגריים: «דביום ההוא» · «יכול מבעוד יום» · «דבעבור זה»
- מילות הוראה: אומר×2, אומרים×1, בחנוכה×1
- פיסוק: נקודה×89, מרכאות (")×42, גרש לטיני (')×20, גרשיים (״)×6, גרש (׳)×3, נקודתיים×1
  - דגימה `Maaseh Nissim on Pesach Haggadah, Kadesh` [Haggada Maaseh Nissim, Warsaw 1895]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Maaseh Nissim on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Haggada Maaseh Nissim, Warsaw 1895]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Maaseh Nissim on Pesach Haggadah, Motzi Matzah` [Haggada Maaseh Nissim, Warsaw 1895]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Maaseh Nissim on Pesach Haggadah, Motzi Matzah.
  - דגימה `Maaseh Nissim on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Haggada Maaseh Nissim, Warsaw 1895]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Maaseh Nissim on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Maaseh Nissim on Pesach Haggadah, Nirtzah, Chad Gadya` [Haggada Maaseh Nissim, Warsaw 1895]: HTTP 200, קינון 2, 12 מחרוזות

### Maaseh Rokeach on Prayer and the Priestly Blessing — מעשה רקח על הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Maaseh Rokeach on Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halacha / Comment; צמתים בלי heTitle: 0
- דגימה: 501 מחרוזות, 62331 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×95, אדני×1, יי×1
- תגיות HTML: b×578, br×75
- דוגמאות בסוגריים: «לברכות» · «פשיטא» · «ברכות דף ל"ב» · «ברכות דף כ"א א» · «ופשיטא דלא עדיפא מי"ח גופא»
- מילות הוראה: אומר×101, כאן×78, אומרים×36, נוהגים×36, בשבת×27, שליח ציבור×10, עד כאן×8, החזן×7
- פיסוק: מרכאות (")×5528, גרש לטיני (')×1865, נקודה×1427, פסיק×6
  - דגימה `Maaseh Rokeach on Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 501 מחרוזות

### Machzor Vitry — מחזור ויטרי

- דוגמת ref לעלה: `Machzor Vitry, Laws of Shacharit`
- עומק טקסט בעלים: {'2': 55, '3': 2}; sectionNames: Chapter / Mishnah / Paragraph, Chapter / Paragraph, Siman / Chapter / Paragraph, Siman / Paragraph; צמתים בלי heTitle: 1
- צמתים ברמה הראשונה: Laws of Shacharit (הלכות שחרית); Laws of the Meal (הלכות סעודה); Laws of Mincha and Maariv (הלכות מנחה וערבית); Pitum HaKetoret (פיטום הקטרת); Seder Kriat Shema Al HaMitah (סדר קריאת שמע על המיטה); Hatavat Chalom (הטבת חלום); Order of the Meal (סדר סעודה); Meaning of the Kaddish (פירוש הקדיש); Order of Shacharit (סדר שחרית); Order of Mincha (סדר מנחה); Order of Maariv (סדר ערבית); Laws of Shabbat (הלכות שבת); Laws of Shabbat from Sefer HaTerumah (הלכות שבת מספר התרומה); Order of Shabbat (סדר שבת); Order of Motza'ei Shabbat (סדר מוצאי שבת); Laws of Rosh Chodesh (הלכות ראש חדש); Order of Chanukah (סדר חנוכה); The Four Torah Portions (ד' פרשיות); Order of Purim (סדר פורים); Laws of Purim (הלכות פורים); Tammuz and Av (תמוז ואב); Laws of Tisha B'Av (הלכות תשעה באב); Laws of Fast Days (הלכות תענית); Laws of Mourning (הלכות אבל); Laws of Eiruvin (הלכות עירובין) …
- דגימה: 217 מחרוזות, 35091 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×19, יי×5, אדני×4, יהוה×1
- תגיות HTML: b×267, big×126, strong×126, br×126, small×7, sup×4, i×4
- דוגמאות `<small>`: «סליקו ההבדלות:» · «סליקו הילכות ראש השנה:» · «סליקו הילכות תפילין.» · «כך נזרקה מפי רבינו יצחק הלוי:» · «עד כאן העתקתי מכתיבת יד החבר ר' משה מברינא:»
- דוגמאות בסוגריים: «אני» · «ללת"ם» · «שמואל ב כג» · «עמוס ד׳:י״ב» · «תשר»
- מילות הוראה: אומר×43, כאן×27, בשבת×18, שליח ציבור×16, אומרים×9, הקהל×7, עד כאן×6, החזן×3
- פיסוק: נקודה×4171, גרש לטיני (')×1525, נקודתיים×1144, מרכאות (")×830, גרשיים (״)×197, גרש (׳)×134, פסיק×81, מקף לטיני (-)×7
  - דגימה `Machzor Vitry, Laws of Shacharit` [Machzor Vitry, Berlin, 1893-97]: HTTP 200, קינון 2, 40 מחרוזות
  - דגימה `Machzor Vitry, Order of Motza'ei Shabbat` [Machzor Vitry, Berlin, 1893-97]: HTTP 200, קינון 2, 37 מחרוזות
  - דגימה `Machzor Vitry, Laws of Rosh HaShanah` [Machzor Vitry, Berlin, 1893-97]: HTTP 200, קינון 2, 56 מחרוזות
  - דגימה `Machzor Vitry, Laws of Tefillin from Sefer HaTerumah` [Machzor Vitry, Berlin, 1893-97]: HTTP 200, קינון 2, 12 מחרוזות
  - דגימה `Machzor Vitry, Laws of Chalitza` [Machzor Vitry, Berlin, 1893-97]: HTTP 200, קינון 2, 72 מחרוזות

### Machzor Yom Ha'atzmaut & Yom Yerushalyim — מחזור ליום העצמאות ויום ירושלים

- דוגמת ref לעלה: `—`
- עומק טקסט בעלים: {}; sectionNames: —; צמתים בלי heTitle: —
  - דגימה `Machzor Yom Ha'atzmaut & Yom Yerushalyim` [(ברירת מחדל)]: HTTP 404, קינון —, — מחרוזות — שגיאה: Could not find title in reference: Machzor Yom Ha'atzmaut & Yom Yerushalyim

### Maharam of Padua on Mishneh Torah, Prayer and the Priestly Blessing — הגהות מהר"ם פדווא על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Maharam of Padua on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 1 מחרוזות, 66 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×1
- מילות הוראה: נוהגים×1
- פיסוק: מרכאות (")×6, פסיק×2, נקודה×1, נקודתיים×1
  - דגימה `Maharam of Padua on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 1 מחרוזות

### Marbeh Lesaper on Pesach Haggadah — מרבה לספר על הגדה של פסח

- דוגמת ref לעלה: `Marbeh Lesaper on Pesach Haggadah, The Simanim`
- עומק טקסט בעלים: {'1': 1, '2': 38}; sectionNames: Paragraph, Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: The Simanim (סימני הסדר); Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 75 מחרוזות, 8333 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×44, אדני×3, יי×2
- תגיות HTML: b×109, br×30
- דוגמאות בסוגריים: «ועיין ט"ז סי' תע"ה סק"א» · «אלו הפרתמים» · «ונלע"ד רמז ופרוס גמט' חל"ק רוח» · «ובפיוט סדר קדושה דר"ה צריכין להגיה במעלות הנשמה. נפש רוח נשמה חיה יחידה כי לאו כ» · «ואפשר עפ"י דארז"ל דאין בן דוד בא עד שיכלה כל הנשמות מחדר הנקרא אוצר הגוף. או דרו»
- מילות הוראה: כאן×9, אומר×7, בשבת×6, אומרים×4, בתענית×1
- פיסוק: גרש לטיני (')×572, מרכאות (")×514, נקודה×404, נקודתיים×109, גרשיים (״)×5, גרש (׳)×3
  - דגימה `Marbeh Lesaper on Pesach Haggadah, The Simanim` [Marbeh Lesaper, Karlsruhe 1791]: HTTP 200, קינון 1, 11 מחרוזות
  - דגימה `Marbeh Lesaper on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Marbeh Lesaper, Karlsruhe 1791]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Marbeh Lesaper on Pesach Haggadah, Motzi Matzah` [Marbeh Lesaper, Karlsruhe 1791]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Marbeh Lesaper on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Marbeh Lesaper, Karlsruhe 1791]: HTTP 200, קינון 2, 49 מחרוזות
  - דגימה `Marbeh Lesaper on Pesach Haggadah, Nirtzah, Chad Gadya` [Marbeh Lesaper, Karlsruhe 1791]: HTTP 200, קינון 2, 13 מחרוזות

### Mekorei HaRambam LeRashash on Mishneh Torah, Prayer and the Priestly Blessing — מקורי הרמב"ם לרש"ש על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Mekorei HaRambam LeRashash on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 45 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×3
- דוגמאות בסוגריים: «ט"ז:»
- מילות הוראה: ש"ץ×1
- פיסוק: גרש לטיני (')×9, מרכאות (")×9, נקודה×4, נקודתיים×4
  - דגימה `Mekorei HaRambam LeRashash on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 3 מחרוזות

### Melekhet Shelomoh on Mishneh Torah, Prayer and the Priestly Blessing — מלאכת שלמה על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Melekhet Shelomoh on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 1 מחרוזות, 256 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×2, br×1
- דוגמאות בסוגריים: «א"ה ס"ט הוא מאן ניהו רבה מורינו הרב הגדול רבין חסידא בעל פני מבין» · «א"ה ס"ט עיין בס' לב מבין בפירקין»
- מילות הוראה: אומר×1, כאן×1
- פיסוק: מרכאות (")×43, גרש לטיני (')×14, נקודה×5
  - דגימה `Melekhet Shelomoh on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 1 מחרוזות

### Midrash BeChiddush on Pesach Haggadah — מדרש בחדוש על הגדה של פסח

- דוגמת ref לעלה: `Midrash BeChiddush on Pesach Haggadah`
- עומק טקסט בעלים: {'1': 1, '2': 13}; sectionNames: Paragraph, Paragraph / Comment; צמתים בלי heTitle: 1
- צמתים ברמה הראשונה:  (); Magid (מגיד); Hallel (הלל)
- דגימה: 36 מחרוזות, 4677 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×21
- תגיות HTML: b×49, br×23, small×2
- דוגמאות `<small>`: «ולפי שלא זכיתי לחדש דבר על הסדר שלאחר הסעודה אלא על מזמור הנקרא הלל הגדול הייתי » · «תם ונשלם:»
- מילות הוראה: אומר×6, כאן×4, אומרים×2, עד כאן×1
- פיסוק: נקודה×375, גרש לטיני (')×234, מרכאות (")×127, נקודתיים×17, פסיק×3, סימן שאלה×1
  - דגימה `Midrash BeChiddush on Pesach Haggadah` [Przemyśl, 1891]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Midrash BeChiddush on Pesach Haggadah', please pass a more specific ref for this book, and try again. 'Midrash BeChiddush on Pesach Haggadah' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a
  - דגימה `Midrash BeChiddush on Pesach Haggadah, Magid, We Were Slaves in Egypt` [Przemyśl, 1891]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Midrash BeChiddush on Pesach Haggadah, Magid, In the Beginning Our Fathers Were Idol Worshipers` [Przemyśl, 1891]: HTTP 200, קינון 2, 5 מחרוזות
  - דגימה `Midrash BeChiddush on Pesach Haggadah, Magid, Rabban Gamliel's Three Things` [Przemyśl, 1891]: HTTP 200, קינון 2, 5 מחרוזות
  - דגימה `Midrash BeChiddush on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Przemyśl, 1891]: HTTP 200, קינון 2, 24 מחרוזות

### Migdal Oz on Mishneh Torah, Prayer and the Priestly Blessing — מגדל עוז על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Migdal Oz on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 223 מחרוזות, 5238 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×6
- תגיות HTML: b×252, small×202, br×14
- דוגמאות `<small>`: «(דף כ"א)» · «(דף ל"ב)» · «(ל"ג)» · «(דף י"ז)» · «(דף כ"ו)»
- דוגמאות בסוגריים: «דף כ"א» · «דף ל"ב» · «ל"ג» · «דף י"ז» · «דף כ"ו»
- מילות הוראה: אומר×21, שליח ציבור×7, כאן×5, בשבת×3, אומרים×3, בחול×2, ש"ץ×2, ואין אומרים×2
- פיסוק: מרכאות (")×440, גרש לטיני (')×318, נקודתיים×252, נקודה×243, פסיק×2
  - דגימה `Migdal Oz on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 223 מחרוזות

### Minchat Ani on Pesach Haggadah — מנחת עני על הגדה של פסח

- דוגמת ref לעלה: `Minchat Ani on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Magid (מגיד); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 54 מחרוזות, 8304 מילים; ניקוד —, טעמים —, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: i×231, br×30, sup×27, b×22, small×7
- דוגמאות `<small>`: «Many people begin the Seder by chanting the “order” of the “Seder:” Kadesh, urec» · «The Talmud suggests two ways of telling the story of the Exodus: “We were slaves» · «This is another question which the sages contemplate: exactly how long were the » · «For Rabbi Ettlinger, the Passover Seder is all about thanksgiving. He connects t» · «The Talmud and Midrash imply different reasons for the bitterness of slavery in »
- דוגמאות בסוגריים: «repentance» · «prayer» · «righteous giving» · «former» · «from idolatry»
- מילות הוראה: —
- פיסוק: נקודה×374, פסיק×325, נקודתיים×135, סימן שאלה×38, מרכאות (")×36, נקודה-פסיק×30, גרש לטיני (')×21, קו מפריד (–)×19
  - דגימה `Minchat Ani on Pesach Haggadah, Kadesh` [(ברירת מחדל)]: HTTP 200, קינון 2, 16 מחרוזות
  - דגימה `Minchat Ani on Pesach Haggadah, Magid, We Were Slaves in Egypt` [(ברירת מחדל)]: HTTP 200, קינון 2, 6 מחרוזות
  - דגימה `Minchat Ani on Pesach Haggadah, Magid, In the Beginning Our Fathers Were Idol Worshipers` [(ברירת מחדל)]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Minchat Ani on Pesach Haggadah, Magid, Rabban Gamliel's Three Things` [(ברירת מחדל)]: HTTP 200, קינון 2, 27 מחרוזות
  - דגימה `Minchat Ani on Pesach Haggadah, Nirtzah, Chad Gadya` [(ברירת מחדל)]: HTTP 200, קינון 2, 3 מחרוזות

### Mishneh LaMelech on Mishneh Torah, Prayer and the Priestly Blessing — משנה למלך על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Mishneh LaMelech on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Paragraph; צמתים בלי heTitle: 0
- דגימה: 1 מחרוזות, 719 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×1
- דוגמאות בסוגריים: «דף ל"ח» · «י"ח.» · «סוטה ל"ח.» · «י"ח.»
- מילות הוראה: אומר×1, כאן×1
- פיסוק: מרכאות (")×52, נקודה×20, גרש לטיני (')×10, פסיק×1, נקודתיים×1
  - דגימה `Mishneh LaMelech on Mishneh Torah, Prayer and the Priestly Blessing` [Warsaw, 1881]: HTTP 200, קינון 3, 1 מחרוזות

### Mishneh Torah, Prayer and the Priestly Blessing — משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Chapter / Halakhah; צמתים בלי heTitle: 0
- דגימה: 256 מחרוזות, 13914 מילים; ניקוד 90%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: small×162, br×1
- דוגמאות `<small>`: «(שמות כג כה)» · «(דברים יא יג)» · «(נחמיה יג כד)» · «(נחמיה יג כד)» · «(ויקרא ו ב)»
- דוגמאות בסוגריים: «שמות כג כה» · «דברים יא יג» · «נחמיה יג כד» · «נחמיה יג כד» · «ויקרא ו ב»
- מילות הוראה: אומר×42, בשבת×26, אומרים×10, ביום טוב×7, בפורים×6, ש״ץ×4, שליח ציבור×4, ואין אומרים×2
- פיסוק: נקודה×821, גרשיים (״)×345, נקודתיים×239, גרש (׳)×100, פסיק×29, מרכאות (")×13, גרש לטיני (')×7
  - דגימה `Mishneh Torah, Prayer and the Priestly Blessing` [Torat Emet 370]: HTTP 200, קינון 2, 240 מחרוזות
  - דגימה `Mishneh Torah, Prayer and the Priestly Blessing` [Wikisource]: HTTP 200, קינון 2, 14 מחרוזות
  - דגימה `Mishneh Torah, Prayer and the Priestly Blessing` [just the first two halachot]: HTTP 200, קינון 2, 2 מחרוזות

### Mishneh Torah, The Order of Prayer — משנה תורה, סדר התפילה

- דוגמת ref לעלה: `Mishneh Torah, The Order of Prayer`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Chapter / Halakhah; צמתים בלי heTitle: 0
- דגימה: 136 מחרוזות, 13204 מילים; ניקוד 50%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×8, אדני×4, ה׳ (קיצור)×1
- תגיות HTML: b×37, small×3
- דוגמאות `<small>`: «בְּרִיךְ רַחֲמָנָא דְּסַיְּעָן - נִגְמַר סֵפֶר שֵׁנִי סֵפֶר אַהֲבָה בְּסִיעַתָּא» · «הִלְכוֹתָיו שֵׁשׁ. וּמִנְיַן פְּרָקָיו שִׁשָׁה וְאַרְבָּעים. וְאֵלוּ הֵן:» · «הִלְכוֹת קְרִיאַת שְׁמַע ד׳‎ פְּרָקִים: הִלְכוֹת צִיצִית ג׳‎ פְּרָקִים: הִלְכוֹת»
- דוגמאות בסוגריים: «א» · «ב» · «מוֹרִיד הַטָּל» · «מַשִּׁיב הָרוּחַ וּמוֹרִיד הַגָּשֶׁם» · «ג»
- מילות הוראה: אומר×30, בשבת×8, אומרים×6, שליח ציבור×4, הקהל×2, בפורים×2, ביום טוב×2, בחול×2
- פיסוק: נקודה×428, גרש (׳)×323, גרש לטיני (')×315, נקודתיים×124, מרכאות (")×88, גרשיים (״)×8, מקף לטיני (-)×1
  - דגימה `Mishneh Torah, The Order of Prayer` [Torat Emet 370]: HTTP 200, קינון 2, 68 מחרוזות
  - דגימה `Mishneh Torah, The Order of Prayer` [Wikisource Mishneh Torah]: HTTP 200, קינון 2, 68 מחרוזות

### Nachal Eitan on Mishneh Torah, Prayer and the Priestly Blessing — נחל איתן על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Nachal Eitan on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 10 מחרוזות, 2323 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×7
- תגיות HTML: b×13, br×3
- דוגמאות בסוגריים: «דף כ"ח ע"א» · «דף ס"ה» · «דף מ' ע"ב» · «דף ל"ח» · «דף ל"ח»
- מילות הוראה: כאן×5, אומר×3, בר"ח×1, אומרים×1, בתענית×1, עד כאן×1
- פיסוק: מרכאות (")×260, נקודה×102, גרש לטיני (')×77
  - דגימה `Nachal Eitan on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 10 מחרוזות

### Naftali Seva Ratzon on Pesach Haggadah — נפתלי שבע רצון על הגדה של פסח

- דוגמת ref לעלה: `Naftali Seva Ratzon on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 6 מחרוזות, 2509 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×8
- תגיות HTML: b×11, br×8
- מילות הוראה: אומרים×2, אומר×2, כאן×1, בר"ח×1
- פיסוק: מרכאות (")×183, גרש לטיני (')×90, גרשיים (״)×41, נקודתיים×40, נקודה×25, גרש (׳)×10
  - דגימה `Naftali Seva Ratzon on Pesach Haggadah, Kadesh` [Naftali Seva Ratzon, Furth, 1727]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Naftali Seva Ratzon on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Naftali Seva Ratzon, Furth, 1727]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Naftali Seva Ratzon on Pesach Haggadah, Motzi Matzah` [Naftali Seva Ratzon, Furth, 1727]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Naftali Seva Ratzon on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Naftali Seva Ratzon, Furth, 1727]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Naftali Seva Ratzon on Pesach Haggadah, Nirtzah, Chad Gadya` [Naftali Seva Ratzon, Furth, 1727]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Naftali Seva Ratzon on Pesach Haggadah, Nirtzah, Chad Gadya.

### Ohr Sameach on Mishneh Torah, Prayer and the Priestly Blessing — אור שמח על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Ohr Sameach on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 44 מחרוזות, 5131 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×99, br×55
- דוגמאות בסוגריים: «פאה פרק ד'» · «עירובין פ"ד» · «מעילה ט"ז ע"ב» · «או אולי כמו שכתוב במג"א דאומר ש"ץ בלחש» · «דלא כהפרישה שחשיב בתרתי דלא משמע כן דהו"ל למימר ואחריו כל העם»
- מילות הוראה: בשבת×9, כאן×7, אומר×5, ש"ץ×4, בר"ח×3, בחול×2, בתענית×1, החזן×1
- פיסוק: מרכאות (")×411, גרש לטיני (')×213, נקודה×160, פסיק×154, נקודתיים×6, מקף לטיני (-)×4
  - דגימה `Ohr Sameach on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 44 מחרוזות

### On the Prayers and Curses Uttered by Noah when he Became Sober — על הפיכחות

- דוגמת ref לעלה: `On the Prayers and Curses Uttered by Noah when he Became Sober`
- עומק טקסט בעלים: {'1': 2, '2': 1}; sectionNames: Chapter / Paragraph, Paragraph; צמתים בלי heTitle: 2
- צמתים ברמה הראשונה:  ();  (); Appendix (הערות)
- דגימה: 157 מחרוזות, 12645 מילים; ניקוד —, טעמים —, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: i×37
- דוגמאות בסוגריים: «Gen. 9:24» · «Gen. 21:14–16» · «Deut. 32:4–6» · «Gen. 37:2» · «Gen. 49:22»
- מילות הוראה: —
- פיסוק: פסיק×857, נקודה×475, מקף לטיני (-)×60, סימן שאלה×41, נקודתיים×38, קו ארוך (—)×32, נקודה-פסיק×30, קו מפריד (–)×6
  - דגימה `On the Prayers and Curses Uttered by Noah when he Became Sober` [(ברירת מחדל)]: HTTP 200, קינון 2, 72 מחרוזות
  - דגימה `On the Prayers and Curses Uttered by Noah when he Became Sober` [(ברירת מחדל)]: HTTP 200, קינון 2, 72 מחרוזות
  - דגימה `On the Prayers and Curses Uttered by Noah when he Became Sober, Appendix` [(ברירת מחדל)]: HTTP 200, קינון 1, 13 מחרוזות

### Peh Echad on Pesach Haggadah — פה אחד על הגדה של פסח

- דוגמת ref לעלה: `Peh Echad on Pesach Haggadah, Magid, Ha Lachma Anya`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Magid (מגיד); Barech (ברך); Hallel (הלל)
- דגימה: 22 מחרוזות, 5161 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×54, אדני×2
- תגיות HTML: b×45, br×22, small×1
- דוגמאות `<small>`: «קונטריס קטן זה שמו פה אחד פ״ה ר״ת פירוש הגדה ושמי וכינויי מטמין ברמ״ז והוא באח״ד»
- דוגמאות בסוגריים: «הוא מהר"ש בן אלקבץ הלוי זלה"ה» · «מותי»
- מילות הוראה: אומר×7, כאן×2, אומרים×1, בחול×1, הקהל×1
- פיסוק: מרכאות (")×479, גרש לטיני (')×302, נקודה×134, נקודתיים×55, גרשיים (״)×8, פסיק×1
  - דגימה `Peh Echad on Pesach Haggadah, Magid, Ha Lachma Anya` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Peh Echad on Pesach Haggadah, Magid, Story of the Five Rabbis` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Peh Echad on Pesach Haggadah, Magid, First Fruits Declaration` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 6 מחרוזות
  - דגימה `Peh Echad on Pesach Haggadah, Magid, First Half of Hallel` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Peh Echad on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 8 מחרוזות

### Peirush Hafla'ah on Pesach Haggadah — פירוש הפלאה על הגדה של פסח

- דוגמת ref לעלה: `Peirush Hafla'ah on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 1 מחרוזות, 409 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×5
- תגיות HTML: b×1
- מילות הוראה: —
- פיסוק: גרשיים (״)×16, גרש (׳)×14, נקודה×1, נקודתיים×1
  - דגימה `Peirush Hafla'ah on Pesach Haggadah, Kadesh` [L'viv, 1860]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Peirush Hafla'ah on Pesach Haggadah, Kadesh.
  - דגימה `Peirush Hafla'ah on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [L'viv, 1860]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Peirush Hafla'ah on Pesach Haggadah, Motzi Matzah` [L'viv, 1860]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Peirush Hafla'ah on Pesach Haggadah, Motzi Matzah.
  - דגימה `Peirush Hafla'ah on Pesach Haggadah, Hallel, Fourth Cup of Wine` [L'viv, 1860]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Peirush Hafla'ah on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Peirush Hafla'ah on Pesach Haggadah, Nirtzah, Chad Gadya` [L'viv, 1860]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Peirush Hafla'ah on Pesach Haggadah, Nirtzah, Chad Gadya.

### Peninei Halakhah, Prayer — פניני הלכה, תפילה

- דוגמת ref לעלה: `Peninei Halakhah, Prayer`
- עומק טקסט בעלים: {'1': 1, '3': 1}; sectionNames: Chapter / Section / Paragraph, Paragraph; צמתים בלי heTitle: 2
- צמתים ברמה הראשונה:  ();  ()
- דגימה: 2594 מחרוזות, 193516 מילים; ניקוד 1%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×564
- תגיות HTML: strong×506, sup×462, i×462, br×308, img×6
- דוגמאות בסוגריים: «בראשית יח» · «בראשית כה» · «בראשית ל״ב:י״ב» · «שמות ל״ב:י״ד» · «במדבר י״ב:י״ג»
- מילות הוראה: אומר×552, אומרים×372, נוהגים×298, החזן×230, ש"ץ×142, יש אומרים×134, בשבת×66, הקהל×58
- פיסוק: פסיק×22548, נקודה×10518, מרכאות (")×10202, גרש לטיני (')×5556, מקף לטיני (-)×974, נקודה-פסיק×766, נקודתיים×718, קו מפריד (–)×710
  - דגימה `Peninei Halakhah, Prayer` [Peninei Halakhah, Yeshivat Har Bracha]: HTTP 200, קינון 3, 1297 מחרוזות
  - דגימה `Peninei Halakhah, Prayer` [Peninei Halakhah, Yeshivat Har Bracha]: HTTP 200, קינון 3, 1297 מחרוזות

### Peninei Halakhah, Women's Prayer — פניני הלכה, תפילת נשים

- דוגמת ref לעלה: `Peninei Halakhah, Women's Prayer`
- עומק טקסט בעלים: {'1': 1, '3': 1}; sectionNames: Chapter / Section / Paragraph, Paragraph; צמתים בלי heTitle: 2
- צמתים ברמה הראשונה:  ();  ()
- דגימה: 2170 מחרוזות, 136134 מילים; ניקוד 1%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×488
- תגיות HTML: strong×410, sup×216, i×216, br×116, img×6
- דוגמאות בסוגריים: «בראשית יח» · «בראשית כה» · «בראשית ל״ב:י״ב» · «שמות ל״ב:י״ד» · «במדבר י״ב:י״ג»
- מילות הוראה: אומר×390, אומרים×274, יש אומרים×126, נוהגים×118, בשבת×96, החזן×56, כאן×46, ש"ץ×42
- פיסוק: פסיק×16108, נקודה×7058, מרכאות (")×6324, גרש לטיני (')×2022, נקודתיים×608, מקף לטיני (-)×550, נקודה-פסיק×480, קו מפריד (–)×430
  - דגימה `Peninei Halakhah, Women's Prayer` [Peninei Halakhah, Yeshivat Har Bracha]: HTTP 200, קינון 3, 1085 מחרוזות
  - דגימה `Peninei Halakhah, Women's Prayer` [Peninei Halakhah, Yeshivat Har Bracha]: HTTP 200, קינון 3, 1085 מחרוזות

### Perek Shirah — פרק שירה

- דוגמת ref לעלה: `Perek Shirah, Introductory Text`
- עומק טקסט בעלים: {'1': 2, '2': 1}; sectionNames: Chapter / Line, Paragraph; צמתים בלי heTitle: 1
- צמתים ברמה הראשונה: Introductory Text (הקדמה);  (); Concluding Prayer (תפילה לאחר פרק שירה)
- דגימה: 103 מחרוזות, 1992 מילים; ניקוד 83%, טעמים 0%, קמץ קטן (U+05C7) ×1, מתג ×3
- שם ה׳: יי×54, אדני×1, יהוה×1
- תגיות HTML: small×92, b×87, big×1
- דוגמאות `<small>`: «(תהילים יט ב)» · «(תהילים כד א)» · «(ישעיהו כד טז)» · «(שיר השירים ד טז)» · «(תהילים קז ט)»
- דוגמאות בסוגריים: «תהילים יט ב» · «תהילים כד א» · «ישעיהו כד טז» · «שיר השירים ד טז» · «תהילים קז ט»
- מילות הוראה: אומר×97, אומרים×22, כאן×1
- פיסוק: נקודה×110, נקודתיים×96, פסיק×35, גרשיים (״)×14, מקף (־)×12, סוף פסוק (׃)×8, מקף לטיני (-)×5, מרכאות (")×3
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 2/6
  - דגימה `Perek Shirah, Introductory Text` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Perek Shirah` [Torat Emet 357]: HTTP 200, קינון 2, 97 מחרוזות
  - דגימה `Perek Shirah, Concluding Prayer` [Torat Emet 357]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Perek Shirah, Introductory Text` [ Perek Shirah]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Perek Shirah` [ Perek Shirah]: HTTP 200, קינון 1, 0 מחרוזות
  - דגימה `Perek Shirah, Concluding Prayer` [ Perek Shirah]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

### Pesach Haggadah — הגדה של פסח

- דוגמת ref לעלה: `Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'1': 38}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 32 מחרוזות, 618 מילים; ניקוד 90%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×15
- תגיות HTML: small×14, b×2
- דוגמאות `<small>`: «מוזגים כוס ראשון. המצות מכוסות.» · «בשבת מתחילין:» · «בחול מתחילין:» · «לשבת:» · «לשבת:»
- דוגמאות בסוגריים: «לשבת:  שַׁבָּתוֹת לִמְנוּחָה וּ» · «לשבת:  אֶת יוֹם הַשַּׁבָּת הַזֶּה וְ» · «לשבת:  בְּאַהֲבָה» · «לשבת:  וְשַׁבָּת» · «לשבת:  בְּאַהֲבָה וּבְרָצוֹן»
- מילות הוראה: בשבת×2, בחול×1
- פיסוק: פסיק×94, נקודה×48, נקודתיים×11, מקף (־)×10, מרכאות (")×4, סימן שאלה×2, קו מפריד (–)×1
  - דגימה `Pesach Haggadah, Kadesh` [Pesach Haggadah]: HTTP 200, קינון 1, 13 מחרוזות
  - דגימה `Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Pesach Haggadah]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Pesach Haggadah, Motzi Matzah` [Pesach Haggadah]: HTTP 200, קינון 1, 4 מחרוזות
  - דגימה `Pesach Haggadah, Hallel, Fourth Cup of Wine` [Pesach Haggadah]: HTTP 200, קינון 1, 4 מחרוזות
  - דגימה `Pesach Haggadah, Nirtzah, Chad Gadya` [Pesach Haggadah]: HTTP 200, קינון 1, 10 מחרוזות

### Piskei HaSiddur — פסקי הסידור

- דוגמת ref לעלה: `Piskei HaSiddur, Rising In The Morning`
- עומק טקסט בעלים: {'1': 58}; sectionNames: Paragraph; צמתים בלי heTitle: 13
- צמתים ברמה הראשונה: Rising In The Morning (השכמת הבקר); Washing the Hands (הלכות נטילה שחרית); Order of Washing (סדר הנטילה); Conduct in Lavatory (הנהגות בית הכסא); Morning Blessings (ברכות השחר);  ();  ();  (); Recitation Of The Shema (הלכות קריאת שמע); Priestly Blessing (ברכת כהנים); The Supplications that Follow the Morning Prayer (סיום תפלת שחרית); Prayers of Travelers (תפלת הדרך);  (); Pidyon HaBen (דיני פדיון הבן); Birkat HaMazon (ברכת המזון); Blessings of Marriage Ceremony (ברכת אירוסין ונשואין); Bedtime Shema (סדר קריאת שמע על המטה); Tikkun Chatzot (סדר תיקון חצות); Seder Hakhnasat Shabbat (סדר הכנסת שבת); Hilkheta Rabbta LeShabbta (הלכתא רבתא לשבתא); Minchah of Erev Shabbat (סדר מנחת ערב שבת);  (); Arvit (תפלת ערבית); Shacharit for Shabbat (שחרית לשבת); Mussaf for Shabbat (מוסף לשבת) …
- דגימה: 40 מחרוזות, 807 מילים; ניקוד 97%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×17
- תגיות HTML: i×42, b×5
- דוגמאות בסוגריים: «אוֹ בִּלְשׁוֹן אִידִישׁ: "רַבּוֹתַי מִיר ווֶעלִין בֶּענְטשִׁין"» · «בְּשַׁבָּת: "רוֹעֵנוּ"» · «פְּלוֹנִי» · «פְּלוֹנִי» · «וְאֵינוֹ חוֹתֵם»
- מילות הוראה: אומר×14, בשבת×5, אומרים×4, כאן×1, ביום טוב×1, ואין אומרים×1
- פיסוק: מרכאות (")×100, פסיק×57, נקודתיים×43, נקודה×38, גרש לטיני (')×31, קו ארוך (—)×15, מקף (־)×2, סימן שאלה×1
  - דגימה `Piskei HaSiddur, Rising In The Morning` [Vocalized Edition - Kehot Publication Society]: HTTP 200, קינון 1, 4 מחרוזות
  - דגימה `Piskei HaSiddur, Birkat HaMazon` [Vocalized Edition - Kehot Publication Society]: HTTP 200, קינון 1, 28 מחרוזות
  - דגימה `Piskei HaSiddur, Arvit` [Vocalized Edition - Kehot Publication Society]: HTTP 200, קינון 1, 5 מחרוזות
  - דגימה `Piskei HaSiddur, Kiddush of Rosh Hashanah` [Vocalized Edition - Kehot Publication Society]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Piskei HaSiddur` [Vocalized Edition - Kehot Publication Society]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Piskei HaSiddur', please pass a more specific ref for this book, and try again. 'Piskei HaSiddur' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://developers.se

### Prayer of Manasseh — תְּפִלַּת מְנַשֶׁה

- דוגמת ref לעלה: `Prayer of Manasseh`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Chapter / Verse; צמתים בלי heTitle: 0
- דגימה: 15 מחרוזות, 245 מילים; ניקוד 96%, טעמים 84%, קמץ קטן (U+05C7) ×3, מתג ×14
- שם ה׳: יהוה×9
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: מקף (־)×28, סוף פסוק (׃)×15, פסק (׀)×7
  - דגימה `Prayer of Manasseh` [Avraham Kahana 1937 - with ta'am added]: HTTP 200, קינון 2, 15 מחרוזות

### Rabbi Sacks on Rosh HaShana Mahzor — פירוש הרב זקס על מחזור ראש השנה

- דוגמת ref לעלה: `Rabbi Sacks on Rosh HaShana Mahzor, Annulment of Vows`
- עומק טקסט בעלים: {'1': 47, '2': 1}; sectionNames: Chapter / Mishnah, Paragraph; צמתים בלי heTitle: 2
- צמתים ברמה הראשונה: Annulment of Vows (התרת נדרים); Prozbul (פרוזבול); Eiruvin (עירובין);  (); Minha for Erev Rosh HaShana (מנחה לערב ראש השנה); Ahot Ketana (אחות קטנה); Ma'ariv for Rosh HaShana (מעריב לראש השנה); Kiddush for Rosh HaShana Evening (קידוש לליל ראש השנה); Simanim (סימנים); Massekhet Rosh HaShana (מסכת ראש השנה); Shaharit (שחרית); First Day (סדר ליום א'); Second Day (סדר ליום ב'); Minha (מנחה); Tashlikh (תשליך); Brit Mila (סדר ברית מילה)
- דגימה: 44 מחרוזות, 3920 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×2
- שם ה׳: —
- תגיות HTML: i×64, br×37, small×6
- דוגמאות `<small>`: «ANNULMENT OF VOWS» · «SHIR HAYIḤUD – SONGS OF GOD’S ONENESS» · «THE INTERPRETIVE PRINCIPLES OF RABBI YISHMA’EL» · «THE SHOFAR» · «SERVICE AT A CIRCUMCISION»
- דוגמאות בסוגריים: «Num. 30:3» · «Deut. 23:23» · «Eccl. 5:4» · «Num. 6:1–21» · «an idea incompatible with Jewish monotheism»
- מילות הוראה: —
- פיסוק: פסיק×247, נקודה×206, נקודתיים×61, קו מפריד (–)×17, נקודה-פסיק×8, סימן שאלה×6, מקף לטיני (-)×5, מקף (־)×1
  - דגימה `Rabbi Sacks on Rosh HaShana Mahzor, Annulment of Vows` [(ברירת מחדל)]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Rabbi Sacks on Rosh HaShana Mahzor, Shaharit, Shir HaYihud, Sunday` [(ברירת מחדל)]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Rabbi Sacks on Rosh HaShana Mahzor, Shaharit, The Interpretive Principles of Rabbi Yishmael` [(ברירת מחדל)]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Rabbi Sacks on Rosh HaShana Mahzor, First Day, The Blowing of the Shofar` [(ברירת מחדל)]: HTTP 200, קינון 1, 14 מחרוזות
  - דגימה `Rabbi Sacks on Rosh HaShana Mahzor, Brit Mila` [(ברירת מחדל)]: HTTP 200, קינון 1, 27 מחרוזות

### Rabbi Sacks on Siddur — פירוש הרב זקס על הסידור

- דוגמת ref לעלה: `Rabbi Sacks on Siddur, Weekdays, On Waking`
- עומק טקסט בעלים: {'1': 89, '2': 1}; sectionNames: Chapter / Paragraph, Paragraph; צמתים בלי heTitle: 6
- צמתים ברמה הראשונה: Weekdays (ימי החול);  (); Festivals (חגים ומועדים); Giving Thanks (ברכות); The Cycle of Life (מעגל החיים); Torah Readings (קריאת התורה)
- דגימה: 26 מחרוזות, 2459 מילים; ניקוד 96%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×2
- שם ה׳: —
- תגיות HTML: i×31, br×23, small×8
- דוגמאות `<small>`: «MEDITATION AND BLESSING ON TAKING THE LULAV» · «BLESSINGS ON MITZVOT» · «RESHUT FOR THE ḤATAN TORAH» · «THE DEATH OF MOSES» · «TORAH READING FOR ḤATAN BERESHIT»
- דוגמאות בסוגריים: «Berakhot 57b» · «Psalm 104:24» · «as when a  mohel  circumcises a child on behalf of its parents» · «often legally constituted» · «Avot  2:21»
- מילות הוראה: —
- פיסוק: פסיק×201, נקודה×113, נקודתיים×27, מקף לטיני (-)×14, קו מפריד (–)×14, מקף (־)×5, נקודה-פסיק×2, סימן שאלה×1
  - דגימה `Rabbi Sacks on Siddur, Weekdays, On Waking` [(ברירת מחדל)]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Rabbi Sacks on Siddur` [(ברירת מחדל)]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Rabbi Sacks on Siddur', please pass a more specific ref for this book, and try again. 'Rabbi Sacks on Siddur' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://d
  - דגימה `Rabbi Sacks on Siddur, Festivals, Blessing on Taking the Lulav` [(ברירת מחדל)]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Rabbi Sacks on Siddur, Giving Thanks, Blessings on Mitzvot` [(ברירת מחדל)]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Rabbi Sacks on Siddur, Torah Readings, Hatan Torah and Hatan Bereshit` [(ברירת מחדל)]: HTTP 200, קינון 1, 17 מחרוזות

### Rabbi Sacks on Yom Kippur Mahzor — פירוש הרב זקס על מחזור ליום הכיפורים

- דוגמת ref לעלה: `Rabbi Sacks on Yom Kippur Mahzor, Yom Kippur Eve, Kaparot`
- עומק טקסט בעלים: {'1': 42, '2': 1}; sectionNames: Chapter / Mishnah, Paragraph; צמתים בלי heTitle: 5
- צמתים ברמה הראשונה: Yom Kippur Eve (ערב יום הכיפורים); Yom Kippur Evening (ליל יום הכיפורים); Shaharit (שחרית); Musaf (מוסף);  (); Ne'ila (נעילה); Annotated Viduy (ביאור לוידוי)
- דגימה: 468 מחרוזות, 12837 מילים; ניקוד 99%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×22
- שם ה׳: יהוה×1
- תגיות HTML: i×112, br×80, small×8, b×4
- דוגמאות `<small>`: «THE INTERPRETIVE PRINCIPLES OF RABBI YISHMAEL» · «UNTANEH TOKEF – LET US VOICE THE POWER» · «וּתְשׁוּבָה וּתְפִלָּה וּצְדָקָה – REPENTANCE, PRAYER AND CHARITY» · «REPENTANCE» · «PRAYER»
- דוגמאות בסוגריים: «The Guide for the Perplexed  3:46» · «Laws of Repentance 3:4» · «Lev. 16:29, 31; 23:27, 32; Num. 29:7» · «1» · «2»
- מילות הוראה: —
- פיסוק: פסיק×851, נקודה×761, נקודתיים×92, מקף לטיני (-)×56, קו מפריד (–)×38, נקודה-פסיק×36, סימן שאלה×16, סימן קריאה×1
  - דגימה `Rabbi Sacks on Yom Kippur Mahzor, Yom Kippur Eve, Kaparot` [(ברירת מחדל)]: HTTP 200, קינון 1, 2 מחרוזות
  - דגימה `Rabbi Sacks on Yom Kippur Mahzor, Yom Kippur Evening, Viduy` [(ברירת מחדל)]: HTTP 200, קינון 1, 75 מחרוזות
  - דגימה `Rabbi Sacks on Yom Kippur Mahzor, Shaharit, The Interpretive Principles of Rabbi Yishmael` [(ברירת מחדל)]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Rabbi Sacks on Yom Kippur Mahzor, Musaf, Leader's Repetition for Musaf` [(ברירת מחדל)]: HTTP 200, קינון 1, 287 מחרוזות
  - דגימה `Rabbi Sacks on Yom Kippur Mahzor, Annotated Viduy` [(ברירת מחדל)]: HTTP 200, קינון 1, 103 מחרוזות

### Safa Echat on Pesach Haggadah — שפה אחת על הגדה של פסח

- דוגמת ref לעלה: `Safa Echat on Pesach Haggadah, Magid, Ha Lachma Anya`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Magid (מגיד); Barech (ברך); Hallel (הלל)
- דגימה: 27 מחרוזות, 7952 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×80, אדני×3
- תגיות HTML: b×60, br×32, small×1
- דוגמאות `<small>`: «א"ה כדי שלא להניח הנייר חלק אמר לבי אפיק שפ״ה אחת ר״ת שפה הגדה של פסח והיא קונטר»
- דוגמאות בסוגריים: «במבול»
- מילות הוראה: אומר×9, אומרים×5, בשבת×2, כאן×2, הקהל×1, בחול×1
- פיסוק: מרכאות (")×673, גרש לטיני (')×286, נקודה×267, נקודתיים×36, פסיק×4, גרשיים (״)×3
  - דגימה `Safa Echat on Pesach Haggadah, Magid, Ha Lachma Anya` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Safa Echat on Pesach Haggadah, Magid, Story of the Five Rabbis` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Safa Echat on Pesach Haggadah, Magid, First Fruits Declaration` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 9 מחרוזות
  - דגימה `Safa Echat on Pesach Haggadah, Magid, First Half of Hallel` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Safa Echat on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 11 מחרוזות

### Seder Ma'amadot — סדר מעמדות

- דוגמת ref לעלה: `Seder Ma'amadot`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Day of Week / Section; צמתים בלי heTitle: 0
- דגימה: 369 מחרוזות, 18554 מילים; ניקוד 91%, טעמים 22%, קמץ קטן (U+05C7) ×0, מתג ×770
- שם ה׳: יהוה×291, אדני×13, ה׳ (קיצור)×1
- תגיות HTML: —
- דוגמאות בסוגריים: «בראשית א» · «א» · «ב» · «ג» · «ד»
- מילות הוראה: אומר×78, אומרים×30, בשבת×13, כאן×7, עד כאן×2, הקהל×1, נוהגים×1, יש אומרים×1
- פיסוק: נקודה×1163, נקודתיים×783, מקף לטיני (-)×668, גרש לטיני (')×278, פסיק×1
  - דגימה `Seder Ma'amadot` [סדר מעמדות]: HTTP 200, קינון 2, 369 מחרוזות

### Selichot Nusach Lita Linear — סליחות נוסח ליטא עברי אנגלי

- דוגמת ref לעלה: `Selichot Nusach Lita Linear, First Day`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Chapter / Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: First Day (ליום ראשון); Second Day (ליום שני); Third Day (ליום שלישי); Fourth Day (ליום רביעי); Fifth Day (ליום חמישי); Sixth Day (ליום שישי); Seventh Day (ליום שביעי); Erev Rosh Hashana (לערב ראש השנה); Fast of Gedaliah (לצום גדליה); Second Day of the Ten Days of Penitence (ליום שני דעשי"ת); Third Day of the Ten Days of Penitence (ליום שלישי דעשי"ת); Fourth Day of the Ten Days of Penitence (ליום רביעי דעשי"ת); Fifth Day of the Ten Days of Penitence (ליום חמישי דעשי"ת); Yom Kippur Eve (לערב יום כיפור)
- דגימה: 5912 מחרוזות, 20379 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×1, מתג ×3871
- שם ה׳: יהוה×615, אדני×92, יי×4
- תגיות HTML: br×647, b×125, small×77
- דוגמאות `<small>`: «הש"ץ אומר חצי קדיש:» · «פתיחה. מיוסד על פי א"ב. חתום בנימין.» · «חיבר רב סעדיה גאון» · «קהל וחזן:» · «קהל ואח"כ חזן:»
- דוגמאות בסוגריים: «בֵּית» · «מאור הגולה» · «בֵּית» · «בֵּית» · «בֵּית»
- מילות הוראה: אומר×16, ש"ץ×15, אומרים×5, הקהל×4
- פיסוק: נקודה×1940, נקודתיים×1592, פסיק×732, מקף (־)×681, מרכאות (")×46, סוף פסוק (׃)×22, מקף לטיני (-)×1
  - דגימה `Selichot Nusach Lita Linear, First Day` [The Metsudah Selichos: Hebrew text, Metsudah Publications, 1986]: HTTP 200, קינון 2, 1561 מחרוזות
  - דגימה `Selichot Nusach Lita Linear, Fourth Day` [The Metsudah Selichos: Hebrew text, Metsudah Publications, 1986]: HTTP 200, קינון 2, 977 מחרוזות
  - דגימה `Selichot Nusach Lita Linear, Seventh Day` [The Metsudah Selichos: Hebrew text, Metsudah Publications, 1986]: HTTP 200, קינון 2, 1017 מחרוזות
  - דגימה `Selichot Nusach Lita Linear, Third Day of the Ten Days of Penitence` [The Metsudah Selichos: Hebrew text, Metsudah Publications, 1986]: HTTP 200, קינון 2, 1718 מחרוזות
  - דגימה `Selichot Nusach Lita Linear, Yom Kippur Eve` [The Metsudah Selichos: Hebrew text, Metsudah Publications, 1986]: HTTP 200, קינון 2, 639 מחרוזות

### Selichot Nusach Polin — סליחות נוסח פולין

- דוגמת ref לעלה: `Selichot Nusach Polin, First Day`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Chapter / Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: First Day (ליום ראשון); Second Day (ליום שני); Third Day (ליום שלישי); Fourth Day (ליום רביעי); Fifth Day (ליום חמישי); Sixth Day (ליום שישי); Seventh Day (ליום שביעי); Erev Rosh Hashana (לערב ראש השנה); Fast of Gedaliah (לצום גדליה); Second Day of the Ten Days of Penitence (ליום שני דעשי"ת); Third Day of the Ten Days of Penitence (ליום שלישי דעשי"ת); Fourth Day of the Ten Days of Penitence (ליום רביעי דעשי"ת); Fifth Day of the Ten Days of Penitence (ליום חמישי דעשי"ת); Yom Kippur Eve (לערב יום כיפור)
- דגימה: 602 מחרוזות, 18694 מילים; ניקוד 98%, טעמים 0%, קמץ קטן (U+05C7) ×1, מתג ×3130
- שם ה׳: יהוה×597, אדני×54, יי×10
- תגיות HTML: br×548, b×98, small×87
- דוגמאות `<small>`: «הש"ץ אומר חצי קדיש:» · «פתיחה. מיוסד על פי א"ב. חתום בנימין.» · «חיבר רב סעדיה גאון» · «קהל וחזן:» · «קהל ואח"כ חזן:»
- דוגמאות בסוגריים: «קֵץ» · «קֵץ» · «קֵץ» · «מאור הגולה» · «עֶזְרֵנוּ בְּשֵׁם יְהוָה עֹשֵׂה שָׁמַיִם וָאָרֶץ׃»
- מילות הוראה: אומר×17, ש"ץ×15, אומרים×7, הקהל×4
- פיסוק: נקודה×1861, נקודתיים×1541, פסיק×672, מקף (־)×607, מרכאות (")×47, סוף פסוק (׃)×13, מקף לטיני (-)×1
  - דגימה `Selichot Nusach Polin, First Day` [Selichot Nusach Polin -- Wikisource]: HTTP 200, קינון 2, 125 מחרוזות
  - דגימה `Selichot Nusach Polin, Fourth Day` [Selichot Nusach Polin -- Wikisource]: HTTP 200, קינון 2, 106 מחרוזות
  - דגימה `Selichot Nusach Polin, Seventh Day` [Selichot Nusach Polin -- Wikisource]: HTTP 200, קינון 2, 108 מחרוזות
  - דגימה `Selichot Nusach Polin, Third Day of the Ten Days of Penitence` [Selichot Nusach Polin -- Wikisource]: HTTP 200, קינון 2, 191 מחרוזות
  - דגימה `Selichot Nusach Polin, Yom Kippur Eve` [Selichot Nusach Polin -- Wikisource]: HTTP 200, קינון 2, 72 מחרוזות

### Sha'ar HaMelekh on Mishneh Torah, Prayer and the Priestly Blessing — שער המלך על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Sha'ar HaMelekh on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 1 מחרוזות, 1167 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×4, br×2
- מילות הוראה: —
- פיסוק: מרכאות (")×171, גרש לטיני (')×43, נקודה×8, נקודתיים×3
  - דגימה `Sha'ar HaMelekh on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 1 מחרוזות

### Shalom Aleichem — שלום עליכם

- דוגמת ref לעלה: `Shalom Aleichem`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Section / Line; צמתים בלי heTitle: 0
- דגימה: 4 מחרוזות, 48 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×5
- שם ה׳: —
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: פסיק×8, נקודה×4
  - דגימה `Shalom Aleichem` [Shalom Alechem]: HTTP 200, קינון 2, 4 מחרוזות

### Shibolei HaLeket on Pesach Haggadah — שבלי הלקט על הגדה של פסח

- דוגמת ref לעלה: `Shibolei HaLeket on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 8 מחרוזות, 2307 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×1
- תגיות HTML: b×3
- דוגמאות בסוגריים: «הגדול והקדוש» · «סל» · «של» · «פרדס» · «וכתיבתו»
- מילות הוראה: אומר×3, אומרים×2, כאן×2, בחול×1, ביום טוב×1
- פיסוק: מרכאות (")×52, נקודה×44, גרש לטיני (')×43, נקודתיים×8
  - דגימה `Shibolei HaLeket on Pesach Haggadah, Kadesh` [Vilna, 1887]: HTTP 200, קינון 2, 4 מחרוזות
  - דגימה `Shibolei HaLeket on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Vilna, 1887]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Shibolei HaLeket on Pesach Haggadah, Motzi Matzah` [Vilna, 1887]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Shibolei HaLeket on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Vilna, 1887]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Shibolei HaLeket on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Shibolei HaLeket on Pesach Haggadah, Nirtzah, Chad Gadya` [Vilna, 1887]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Shibolei HaLeket on Pesach Haggadah, Nirtzah, Chad Gadya.

### Shir HaKavod — שיר הכבוד

- דוגמת ref לעלה: `Shir HaKavod`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Line / ; צמתים בלי heTitle: 0
- דגימה: 32 מחרוזות, 279 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×45
- שם ה׳: יי×4
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: נקודה×36, פסיק×32
  - דגימה `Shir HaKavod` [Davkawriter]: HTTP 200, קינון 2, 32 מחרוזות

### Shorshei HaYam on Mishneh Torah, Prayer and the Priestly Blessing — שורשי הים על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Shorshei HaYam on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 3991 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×8
- תגיות HTML: b×22, br×18, span×1
- דוגמאות בסוגריים: «נראה לענ"ד דאע"ג דקי"ל דחוזר ומתפלל כוונת הרב להכריח כן מאותו מ"ד בגמרא דאינו חו»
- מילות הוראה: אומרים×1, אומר×1, בעשרת ימי תשובה×1, כאן×1
- פיסוק: מרכאות (")×386, גרש לטיני (')×251, נקודה×30, נקודתיים×1
  - דגימה `Shorshei HaYam on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 3 מחרוזות

### Siddur Rashi — סידור רש"י

- דוגמת ref לעלה: `Siddur Rashi`
- עומק טקסט בעלים: {'2': 1}; sectionNames: Siman / Paragraph; צמתים בלי heTitle: 0
- דגימה: 914 מחרוזות, 82663 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×361, אדני×1, יי×1
- תגיות HTML: —
- דוגמאות בסוגריים: «דברים י' י"ב» · «ש"ב כ"ג א'» · «עמוס ד' י"ב» · «דכמה» · «וכי לימא מר»
- מילות הוראה: אומר×277, בשבת×103, אומרים×94, כאן×93, שליח ציבור×43, בחול×41, ביום טוב×39, החזן×13
- פיסוק: פסיק×8905, גרש לטיני (')×2228, מרכאות (")×1310, נקודה×947, נקודתיים×805, נקודה-פסיק×5
  - דגימה `Siddur Rashi` [Buber Edition, Berlin, 1912]: HTTP 200, קינון 2, 914 מחרוזות

### Sidduro Shel Shabbat — סדורו של שבת

- דוגמת ref לעלה: `Sidduro Shel Shabbat, Volume I`
- עומק טקסט בעלים: {'1': 2, '2': 18}; sectionNames: Chapter / Paragraph, Paragraph; צמתים בלי heTitle: 2
- צמתים ברמה הראשונה: Volume I (חלק א); Volume II (חלק ב)
- דגימה: 126 מחרוזות, 39084 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×350, אדני×1
- תגיות HTML: b×15, small×3
- דוגמאות `<small>`: «יבואר בו ענינים רבים. מהתנהגות האדם בכל תאותיו הגשמיים ובפרט בעת האוכל את לחמו ל» · «יבואר בו שני עקרים גדולים בעבודת ה' מאהבה. האחד שיהא תורת ומצות ה' עיקר בעיניו ל» · «יבואר בו מעלת ארץ ישראל על כל שאר הארצות אשר לגודל הקדוש' הנמצא בה מאת האל אף בד»
- דוגמאות בסוגריים: «בפרדס שער הכנויים בכנוי שבת» · «ת"כ מובא בילקוט תקמ"ז» · «בבא בתרא ע"ד ע"א» · «מנחות נ"ה ע"א» · «ברמב"ם פ"ג מהלכות מעשי הקרבנות הלכה י"ד»
- מילות הוראה: אומר×40, בשבת×20, כאן×11, אומרים×7, בחול×6, עד כאן×3, בתענית×1, יש אומרים×1
- פיסוק: גרש לטיני (')×1723, מרכאות (")×1620, נקודה×1086, נקודתיים×215, גרשיים (״)×12, גרש (׳)×10, פסיק×2, מקף לטיני (-)×2
  - דגימה `Sidduro Shel Shabbat, Volume I` [Warsaw, 1872]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Sidduro Shel Shabbat, Volume I', please pass a more specific ref for this book, and try again. 'Sidduro Shel Shabbat, Volume I' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefar
  - דגימה `Sidduro Shel Shabbat, Volume I, Shoresh V` [Warsaw, 1872]: HTTP 200, קינון 2, 70 מחרוזות
  - דגימה `Sidduro Shel Shabbat, Volume II` [Warsaw, 1872]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Sidduro Shel Shabbat, Volume II', please pass a more specific ref for this book, and try again. 'Sidduro Shel Shabbat, Volume II' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sef
  - דגימה `Sidduro Shel Shabbat, Volume II, Derush IV` [Warsaw, 1872]: HTTP 200, קינון 2, 38 מחרוזות
  - דגימה `Sidduro Shel Shabbat, Volume II, Derush IX` [Warsaw, 1872]: HTTP 200, קינון 2, 18 מחרוזות

### Simchat HaRegel on Pesach Haggadah — שמחת הרגל על הגדה של פסח

- דוגמת ref לעלה: `Simchat HaRegel on Pesach Haggadah, Title`
- עומק טקסט בעלים: {'1': 3, '2': 27}; sectionNames: Paragraph, Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Title (שער); Kol Chamirah (כל חמירא); The Simanim (סימני הסדר); Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל)
- דגימה: 104 מחרוזות, 19117 מילים; ניקוד 5%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×151, יהוה×24
- תגיות HTML: b×135, br×50, small×2
- דוגמאות `<small>`: «[אחורי תרעא: מעשה שראה אור כי יהל ספר המאיר דרך המלך הנדפס מחדש מאור עינינו הרב » · «[אחורי תרעא: מ"ש בשם הרב מהר"ש פרימו עתה ראיתי ברמזיו סוף בלק שכתבו משם הרב מהרי»
- דוגמאות בסוגריים: «ודלא כהרב בית דוד [בספרו הקטן ברכי יוסף סי' תע"ג כתבנו בעניותינו באורך]» · «א» · «ב» · «ג» · «ד»
- מילות הוראה: אומר×31, כאן×15, אומרים×7, יש אומרים×4, בחול×2, עד כאן×1, הקהל×1
- פיסוק: מרכאות (")×1063, גרש לטיני (')×623, נקודה×356, פסיק×133, נקודתיים×125, מקף לטיני (-)×27
  - דגימה `Simchat HaRegel on Pesach Haggadah, Title` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Simchat HaRegel on Pesach Haggadah, Magid, Ha Lachma Anya` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 16 מחרוזות
  - דגימה `Simchat HaRegel on Pesach Haggadah, Magid, First Fruits Declaration` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 69 מחרוזות
  - דגימה `Simchat HaRegel on Pesach Haggadah, Maror` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Simchat HaRegel on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 11 מחרוזות

### Steinsaltz on Mishneh Torah, Prayer and the Priestly Blessing — ביאור שטיינזלץ על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Steinsaltz on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halacha / Paragraph; צמתים בלי heTitle: 0
- דגימה: 1130 מחרוזות, 14579 מילים; ניקוד 30%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×57, יי×6, אדני×1
- תגיות HTML: b×1130
- דוגמאות בסוגריים: «יבואר לקמן             הל' ה-ח» · «ראה לקמן הל' ג-ד» · «הלכות עבודה זרה יב,ג,             וראה גם לקמן ו,י» · «ראה לקמן ה,א, ה,ג» · «ראה הלכות             ברכות א,ה»
- מילות הוראה: אומר×18, בשבת×6, אומרים×5, ביום טוב×5, כאן×4, שליח ציבור×3, הקהל×2, בראש חודש×2
- פיסוק: נקודה×2364, פסיק×864, גרש לטיני (')×268, מרכאות (")×138, מקף לטיני (-)×79, נקודה-פסיק×24, קו ארוך (—)×8, נקודתיים×4
  - דגימה `Steinsaltz on Mishneh Torah, Prayer and the Priestly Blessing` [Mishneh Torah with Commentary by Rabbi Adin Even-Israel Steinsaltz, Koren Publishers]: HTTP 200, קינון 3, 1130 מחרוזות

### Steinsaltz on Mishneh Torah, The Order of Prayer — ביאור שטיינזלץ על משנה תורה, סדר התפילה

- דוגמת ref לעלה: `Steinsaltz on Mishneh Torah, The Order of Prayer`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halacha / Paragraph; צמתים בלי heTitle: 0
- דגימה: 171 מחרוזות, 2628 מילים; ניקוד 21%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×31, יי×7
- תגיות HTML: b×171
- דוגמאות בסוגריים: «במדבר כח,א-ט» · «במדבר ו,כד-כו» · «הלכות מתנות עניים פרקים א-ג» · «הלכות ביכורים פרקים ב-ד» · «הלכות חגיגה פרקים א-ב»
- מילות הוראה: אומר×7, אומרים×6, בשבת×4, בחול×1
- פיסוק: נקודה×394, פסיק×165, גרש לטיני (')×133, מרכאות (")×34, מקף לטיני (-)×22, נקודתיים×6, סימן קריאה×4, קו ארוך (—)×1
  - דגימה `Steinsaltz on Mishneh Torah, The Order of Prayer` [Mishneh Torah with Commentary by Rabbi Adin Even-Israel Steinsaltz, Koren Publishers]: HTTP 200, קינון 3, 171 מחרוזות

### Tevele Bondi on Pesach Haggadah — טעבעלה באנדי על הגדה של פסח 

- דוגמת ref לעלה: `Tevele Bondi on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 13 מחרוזות, 2207 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×13
- דוגמאות בסוגריים: «ישעיהו ל׳:כ״ט» · «פ' נח»
- מילות הוראה: אומרים×1, אומר×1, כאן×1
- פיסוק: מרכאות (")×137, פסיק×106, נקודה×51, גרש לטיני (')×50, סימן שאלה×7, נקודתיים×6, גרש (׳)×1, גרשיים (״)×1
  - דגימה `Tevele Bondi on Pesach Haggadah, Kadesh` [Haggadah shel Pesach im perush Tevele Bondi, Frankfort, 1898]: HTTP 200, קינון 2, 3 מחרוזות
  - דגימה `Tevele Bondi on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [Haggadah shel Pesach im perush Tevele Bondi, Frankfort, 1898]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Tevele Bondi on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh.
  - דגימה `Tevele Bondi on Pesach Haggadah, Motzi Matzah` [Haggadah shel Pesach im perush Tevele Bondi, Frankfort, 1898]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Tevele Bondi on Pesach Haggadah, Motzi Matzah.
  - דגימה `Tevele Bondi on Pesach Haggadah, Hallel, Fourth Cup of Wine` [Haggadah shel Pesach im perush Tevele Bondi, Frankfort, 1898]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Tevele Bondi on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Tevele Bondi on Pesach Haggadah, Nirtzah, Chad Gadya` [Haggadah shel Pesach im perush Tevele Bondi, Frankfort, 1898]: HTTP 200, קינון 2, 10 מחרוזות

### The Jonathan Sacks Haggadah — הגדת הרב יונתן זקס

- דוגמת ref לעלה: `The Jonathan Sacks Haggadah, The Seder`
- עומק טקסט בעלים: {'1': 1, '2': 29}; sectionNames: Paragraph, Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: The Seder (הקדמה); Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Motzi Matzah (מוציא מצה); Korech (כורך); Tzafun (צפון); Barech (ברך); Nirtzah (נרצה)
- דגימה: 48 מחרוזות, 4125 מילים; ניקוד —, טעמים —, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: i×71, br×30, b×17, small×17, span×1
- דוגמאות `<small>`: «THE SEDER PLATE» · «THE ORDER» · «PESAḤ AND THE HOME» · «WE WERE SLAVES TO PHARAOH IN EGYPT» · «SLAVERY AND FREEDOM»
- דוגמאות בסוגריים: «a» · «ḥazeret» · «b» · «8:5» · «cinnamon and ginger are the most common»
- מילות הוראה: —
- פיסוק: פסיק×249, נקודה×239, קו מפריד (–)×36, נקודתיים×24, סימן שאלה×12, מקף לטיני (-)×3, נקודה-פסיק×2
  - דגימה `The Jonathan Sacks Haggadah, The Seder` [(ברירת מחדל)]: HTTP 200, קינון 1, 34 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah, Magid, We Were Slaves in Egypt` [(ברירת מחדל)]: HTTP 200, קינון 2, 4 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah, Magid, Rabban Gamliel's Three Things` [(ברירת מחדל)]: HTTP 200, קינון 2, 8 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah, Nirtzah, Chasal Siddur Pesach` [(ברירת מחדל)]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah, Nirtzah, Chad Gadya` [(ברירת מחדל)]: HTTP 200, קינון 2, 1 מחרוזות

### The Jonathan Sacks Haggadah; Essays — פסח על שום מה? הגדת הרב יונתן זקס; מאמרים

- דוגמת ref לעלה: `The Jonathan Sacks Haggadah; Essays, The Story of Stories`
- עומק טקסט בעלים: {'1': 21}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: The Story of Stories (מאמר א; סיפור הסיפורים); A Tale of Two Civilizations (מאמר ב; בין שתי ציביליזציות); Pesah, Freud, and Jewish Identity (מאמר ג; פסח, פרויד וזהות יהודית); Building a Society of Freedom (מאמר ד; בנייתה של חברה בת חורין); History and Memory (מאמר ה; היסטוריה וזיכרון); Not Only One (מאמר ו; שלא אחד בלבד); Pesah and the Rebirth of Israel (מאמר ז; חג הפסח והולדתו מחדש של עם ישראל); An Afternoon in Jerusalem (מאמר ח; אחר צהריים בירושלים); The Universal Story (מאמר ט; הסיפור האוניברסלי); The Omer and the Politics of Torah (מאמר י; העומר והפוליטיקה של התורה); Time as a Narrative of Hope (מאמר יא; הזמן כנראטיב של תקווה); The Sages in Benei Brak (מאמר יב; החכמים בבני ברק); Women and the Exodus (מאמר יג; הנשים ויציאת מצרים); The Missing Fifth (מאמר יד; החמישי החסר); The Art of Asking Questions (מאמר טו; אמנות הצגת הקושיות); The Wicked Son What Does He Say? (מאמר טז; רשע מה הוא אומר?); Begin with Shame, End with Praise (מאמר יז; מתחיל בגנות ומסיים בשבח); Ben Zoma and the Sages (מאמר יח; בן זומא והחכמים); The First Pesah (מאמר יט; הפסח הראשון); The Unasked Question (מאמר כ; הקושיה שאינה נשאלת); One Little Goat (מאמר כא; חד גדיא)
- דגימה: 163 מחרוזות, 20070 מילים; ניקוד —, טעמים —, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: i×125, span×40, small×5
- דוגמאות `<small>`: «Remember the earliest of days; grasp the years of generations that have been. As» · «It was not only one man who rose up to destroy us: in every single generation pe» · «The unappeased memory of a future still to be fulfilled.(Harold Fisch, A Remembe» · «The wicked son – what does he say? “What is this service to you?” “To you,” he s» · «One little goat, one little goat my father bought for two zuzim. (Haggada)»
- דוגמאות בסוגריים: «Deut. 32:7» · «a mere reminder until the rebuilding of the Temple» · «Ex. 12:11» · «Good as Gold» · «specifically “scientism,” the belief that science is all there is»
- מילות הוראה: —
- פיסוק: פסיק×1482, נקודה×955, נקודתיים×147, קו מפריד (–)×143, מקף לטיני (-)×106, נקודה-פסיק×73, סימן שאלה×50, סימן קריאה×5
  - דגימה `The Jonathan Sacks Haggadah; Essays, The Story of Stories` [(ברירת מחדל)]: HTTP 200, קינון 1, 33 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah; Essays, Not Only One` [(ברירת מחדל)]: HTTP 200, קינון 1, 39 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah; Essays, Time as a Narrative of Hope` [(ברירת מחדל)]: HTTP 200, קינון 1, 33 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah; Essays, The Wicked Son What Does He Say?` [(ברירת מחדל)]: HTTP 200, קינון 1, 24 מחרוזות
  - דגימה `The Jonathan Sacks Haggadah; Essays, One Little Goat` [(ברירת מחדל)]: HTTP 200, קינון 1, 34 מחרוזות

### Tikkun HaKlali — תיקון הכללי

- דוגמת ref לעלה: `Tikkun HaKlali`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Paragraphs; צמתים בלי heTitle: 0
- דגימה: 13 מחרוזות, 3731 מילים; ניקוד 98%, טעמים 27%, קמץ קטן (U+05C7) ×0, מתג ×284
- שם ה׳: יהוה×65, אדני×8
- תגיות HTML: br×53, b×36, small×3
- דוגמאות `<small>`: «הֲרֵינִי מְקַשֵׁר עַצְמִי בַּאֲמִירַת הָעֲשָׂרָה מִזְמוֹרִים אֵלּוּ לְכָל הַצַּד» · «מִי יִתֵּן מִצִּיּוֹן יְשׁוּעַת יִשְׂרָאֵל בְּשׁוּב יְהֹוָה שְׁבוּת עַמּוֹ יָגֵל» · «תפלה קצרהרִבּוֹנוֹ שֶׁל עוֹלָם, עִלַּת הָעִלּוֹת וְסִבַּת כָּל הַסִּבּוֹת, אַנְת»
- דוגמאות בסוגריים: «*וּבִזְכוּת הַצַּדִּיק יְסוֹד עוֹלָם, נַחַל נוֹבֵעַ מְקוֹר חָכְמָה, רַבֵּנוּ רַב» · «אם אומר  חס ושלום בשביל מקרה שנזדמן לו באותו הלילה יאמר: וּבִפְרָט כָּל הַטִּפּו» · «כָזֶה» · «אַרְבַּע מֵאוֹת שְׁמוֹנִים וְחָמֵשׁ» · «ואם יהיה על קברו הקדוש יאמר:  וּבִזְכוּת הַצַּדִּיק הַזֶּה הַשּׁוֹכֵן פֹּה, צַדּ»
- מילות הוראה: אומר×2
- פיסוק: פסיק×369, מקף (־)×170, סוף פסוק (׃)×164, נקודה×76, נקודתיים×49, פסק (׀)×45, מרכאות (")×11, גרש לטיני (')×1
  - דגימה `Tikkun HaKlali` [Tikkun HaKlali - rabenubook.com]: HTTP 200, קינון 1, 13 מחרוזות

### Tzafnat Pa'neach on Mishneh Torah, Prayer and the Priestly Blessing — צפנת פענח על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Tzafnat Pa'neach on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 78 מחרוזות, 3656 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×12
- תגיות HTML: b×78, small×2
- דוגמאות `<small>`: «השמטה» · «ע"כ השמטה»
- דוגמאות בסוגריים: «זה» · «אם הם»
- מילות הוראה: כאן×15, אומר×8, בשבת×3, בתענית×3, ש"ץ×2, בחול×2, בר"ח×1, הקהל×1
- פיסוק: מרכאות (")×757, גרש לטיני (')×452, נקודה×89, נקודתיים×78, פסיק×26
  - דגימה `Tzafnat Pa'neach on Mishneh Torah, Prayer and the Priestly Blessing` [Tzafnat Pa'neach on Mishneh Torah, Warsaw-Piotrków, 1903-1908]: HTTP 200, קינון 3, 78 מחרוזות

### Tziunei Maharan on Mishneh Torah, Prayer and the Priestly Blessing — ציוני מהר"ן על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Tziunei Maharan on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 132 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×2
- תגיות HTML: b×3, small×2
- דוגמאות `<small>`: «[השמטה]» · «[עד כאן]:»
- מילות הוראה: כאן×3, עד כאן×1
- פיסוק: מרכאות (")×23, גרש לטיני (')×12, נקודה×6, נקודתיים×4, פסיק×4
  - דגימה `Tziunei Maharan on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 3 מחרוזות

### Unetaneh Tokef — ונתנה תוקף

- דוגמת ref לעלה: `Unetaneh Tokef`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- דגימה: 12 מחרוזות, 470 מילים; ניקוד 100%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: —
- דוגמאות בסוגריים: «אֱמֶת» · «אֱמֶת»
- מילות הוראה: —
- פיסוק: פסיק×78, נקודה×18
  - דגימה `Unetaneh Tokef` [מבוססים על המחזור של קורן בהגהותיו ובביאוריו של דניאל גולדשמידט ]: HTTP 200, קינון 1, 6 מחרוזות
  - דגימה `Unetaneh Tokef` [Goldshmidt with ms emendation]: HTTP 200, קינון 1, 6 מחרוזות

### Yad Eitan on Mishneh Torah, Prayer and the Priestly Blessing — יד איתן על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Yad Eitan on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 3 מחרוזות, 196 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: b×3
- דוגמאות בסוגריים: «נ"ב» · «נ"ד»
- מילות הוראה: אומר×1
- פיסוק: מרכאות (")×21, נקודה×8, גרש לטיני (')×6, נקודתיים×3, פסיק×1
  - דגימה `Yad Eitan on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 3 מחרוזות

### Yedid Nefesh — ידיד נפש

- דוגמת ref לעלה: `Yedid Nefesh`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Liturgy; צמתים בלי heTitle: 0
- דגימה: 72 מחרוזות, 285 מילים; ניקוד 68%, טעמים 2%, קמץ קטן (U+05C7) ×0, מתג ×22
- שם ה׳: —
- תגיות HTML: big×4, br×3
- מילות הוראה: —
- פיסוק: נקודה×39, נקודתיים×7, פסיק×1
  - דגימה `Yedid Nefesh` [Original version]: HTTP 200, קינון 1, 24 מחרוזות
  - דגימה `Yedid Nefesh` [Contemporary Version ]: HTTP 200, קינון 1, 24 מחרוזות
  - דגימה `Yedid Nefesh` [The Metsudah Siddur, Metsudah Publications, 1981 - HE]: HTTP 200, קינון 1, 24 מחרוזות

### Yismach Yisrael on Pesach Haggadah — ישמח ישראל על הגדה של פסח

- דוגמת ref לעלה: `Yismach Yisrael on Pesach Haggadah, Kadesh`
- עומק טקסט בעלים: {'2': 38}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 2 מחרוזות, 258 מילים; ניקוד —, טעמים —, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: —
- תגיות HTML: —
- מילות הוראה: —
- פיסוק: נקודה×13, פסיק×4, נקודתיים×2, סימן שאלה×1, סימן קריאה×1
  - דגימה `Yismach Yisrael on Pesach Haggadah, Kadesh` [(ברירת מחדל)]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Yismach Yisrael on Pesach Haggadah, Kadesh.
  - דגימה `Yismach Yisrael on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh` [(ברירת מחדל)]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Yismach Yisrael on Pesach Haggadah, Magid, Yechol Me'rosh Chodesh.
  - דגימה `Yismach Yisrael on Pesach Haggadah, Motzi Matzah` [(ברירת מחדל)]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Yismach Yisrael on Pesach Haggadah, Hallel, Fourth Cup of Wine` [(ברירת מחדל)]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Yismach Yisrael on Pesach Haggadah, Hallel, Fourth Cup of Wine.
  - דגימה `Yismach Yisrael on Pesach Haggadah, Nirtzah, Chad Gadya` [(ברירת מחדל)]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Yismach Yisrael on Pesach Haggadah, Nirtzah, Chad Gadya.

### Yitzchak Yeranen on Mishneh Torah, Prayer and the Priestly Blessing — יצחק ירנן על משנה תורה, הלכות תפילה וברכת כהנים

- דוגמת ref לעלה: `Yitzchak Yeranen on Mishneh Torah, Prayer and the Priestly Blessing`
- עומק טקסט בעלים: {'3': 1}; sectionNames: Chapter / Halakhah / Comment; צמתים בלי heTitle: 0
- דגימה: 37 מחרוזות, 9314 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×5
- תגיות HTML: b×109, br×35
- דוגמאות בסוגריים: «ואי» · «והיא» · «דא"כ» · «וכמ"ש» · «דס"ס»
- מילות הוראה: כאן×12, אומר×9, אומרים×4, בשבת×3, ש"ץ×3, יש אומרים×2, עד כאן×1, נוהגים×1
- פיסוק: מרכאות (")×1166, גרש לטיני (')×395, נקודה×266, פסיק×89
  - דגימה `Yitzchak Yeranen on Mishneh Torah, Prayer and the Priestly Blessing` [Friedberg Edition]: HTTP 200, קינון 3, 37 מחרוזות

### Yizkor — יזכור

- דוגמת ref לעלה: `Yizkor`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- דגימה: 20 מחרוזות, 725 מילים; ניקוד 92%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יי×2, ה׳ (קיצור)×2
- תגיות HTML: —
- דוגמאות בסוגריים: «שם האב בן שם אביו» · «שם האם בת שם אביה» · «זְקֵנַי וּזְקֵנוֹתַי, דּוֹדַי וְדוֹדוֹתַי, אָחַי וְאַחְיוֹתַי, בָּנַי וּבְנוֹתַי» · «שם הנפטר בן שם אביו» · «כָּל קְרוֹבַי וּקְרוֹבוֹתַי, הֵן מִצַּד אָבִי, הֵן מִצַּד אִמִּי»
- מילות הוראה: —
- פיסוק: פסיק×72, נקודה×37, גרש לטיני (')×14, נקודתיים×10, מקף לטיני (-)×9, מרכאות (")×5
  - דגימה `Yizkor` [Public Domain]: HTTP 200, קינון 1, 20 מחרוזות

### Zeroa Yamin on Pesach Haggadah — זרוע ימין על הגדה של פסח

- דוגמת ref לעלה: `Zeroa Yamin on Pesach Haggadah, Magid, Ha Lachma Anya`
- עומק טקסט בעלים: {'2': 14}; sectionNames: Paragraph / Comment; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Magid (מגיד); Barech (ברך); Hallel (הלל)
- דגימה: 40 מחרוזות, 10429 מילים; ניקוד 0%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×80, אדני×2
- תגיות HTML: b×68, br×28, small×1
- דוגמאות `<small>`: «אח"י הנה נא הואלתי יצא עתק קצת פירוש ההגדה זעיר שם זעיר שם אשר כתבתי בעניותי בקו»
- דוגמאות בסוגריים: «ועמ"ש בס' הקטן ברכי יוסף א"ח ריש סי' ר"ם» · «סנהדרין דף ק"ד» · «ובשמחת הרגל כתבתיו משם מהרש"פ וגם מהרש"פ הביאו משם מהרימ"ט כמ"ש בקונט' פאת הראש »
- מילות הוראה: אומר×9, כאן×3, בחול×2, אומרים×1, בתענית×1, נוהגים×1, עד כאן×1
- פיסוק: מרכאות (")×856, גרש לטיני (')×454, נקודה×252, נקודתיים×67, גרשיים (״)×3, פסיק×3
  - דגימה `Zeroa Yamin on Pesach Haggadah, Magid, Ha Lachma Anya` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 7 מחרוזות
  - דגימה `Zeroa Yamin on Pesach Haggadah, Magid, Story of the Five Rabbis` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 2 מחרוזות
  - דגימה `Zeroa Yamin on Pesach Haggadah, Magid, First Fruits Declaration` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 21 מחרוזות
  - דגימה `Zeroa Yamin on Pesach Haggadah, Magid, First Half of Hallel` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 1 מחרוזות
  - דגימה `Zeroa Yamin on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Otzar Perushei Ha-haggadah, Chida. Jerusalem, 1959]: HTTP 200, קינון 2, 9 מחרוזות

### Zevach Pesach on Pesach Haggadah — זבח פסח על הגדה של פסח

- דוגמת ref לעלה: `Zevach Pesach on Pesach Haggadah`
- עומק טקסט בעלים: {'1': 2, '2': 38}; sectionNames: Paragraph, Paragraph / Comment; צמתים בלי heTitle: 1
- צמתים ברמה הראשונה:  (); One Hundred Gates (מאה שערים); Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 30 מחרוזות, 5008 מילים; ניקוד 1%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: ה׳ (קיצור)×52
- תגיות HTML: b×18, br×4, small×3, sup×1, i×1
- דוגמאות `<small>`: «תשובות לשערים י"ט – כ"ג» · «תשובות לשערים כ"ה – כ"ו» · «תשובות לשערים כ"ד, כ"ז – כ"ט»
- דוגמאות בסוגריים: «פסחים קט"ז, א'» · «תהלים קי"ט, ב'» · «שמות י"ב, כ"ו» · «שמות י"ג, ח'» · «שם שם, י"ד»
- מילות הוראה: אומר×7, כאן×4, אומרים×2, עד כאן×1, נוהגים×1
- פיסוק: פסיק×371, מרכאות (")×304, נקודה×125, גרש לטיני (')×93, סימן שאלה×15, נקודתיים×11, סימן קריאה×4, קו מפריד (–)×3
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 1/10
  - דגימה `Zevach Pesach on Pesach Haggadah` [Enhanced edition, 2023]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Zevach Pesach on Pesach Haggadah', please pass a more specific ref for this book, and try again. 'Zevach Pesach on Pesach Haggadah' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on S
  - דגימה `Zevach Pesach on Pesach Haggadah, Magid, The Four Sons` [Enhanced edition, 2023]: HTTP 200, קינון 2, 30 מחרוזות
  - דגימה `Zevach Pesach on Pesach Haggadah, Motzi Matzah` [Enhanced edition, 2023]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Zevach Pesach on Pesach Haggadah, Motzi Matzah.
  - דגימה `Zevach Pesach on Pesach Haggadah, Hallel, Songs of Praise and Thanks` [Enhanced edition, 2023]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Zevach Pesach on Pesach Haggadah, Hallel, Songs of Praise and Thanks.
  - דגימה `Zevach Pesach on Pesach Haggadah, Nirtzah, Chad Gadya` [Enhanced edition, 2023]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Zevach Pesach on Pesach Haggadah, Nirtzah, Chad Gadya.
  - דגימה `Zevach Pesach on Pesach Haggadah` [L'viv, 1872]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Zevach Pesach on Pesach Haggadah', please pass a more specific ref for this book, and try again. 'Zevach Pesach on Pesach Haggadah' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on S

## נוסח: ספרד

| אינדקס | כותר עברי | סוג | קטגוריות | צמתים/עלים | עומק | גרסאות עבריות | רישיונות | ניקוד | טעמים | שם ה׳ | `<small>` | סוגריים |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Machzor Rosh Hashanah Sefard | מחזור ראש השנה ספרד | מחזור | Liturgy / High Holidays | 88/76 | 3 | 1 | unknown | 81% | 0% | יהוה×61, יי×12, ה׳ (קיצור)×9, אדני×4 | 74 | 14 |
| Machzor Yom Kippur Sefard | מחזור ליום כפור ספרד | מחזור | Liturgy / High Holidays | 76/67 | 2 | 1 | unknown | 69% | 0% | יהוה×63, ה׳ (קיצור)×4, אדני×3 | 77 | 25 |
| Shabbat Siddur Sefard Linear | סידור ספרד לשבת | סידור | Liturgy / Siddur | 157/139 | 3 | 1 | CC-BY | 100% | 10% | יהוה×95, אדני×1 | 5 | 1 |
| Siddur Sefard | סידור ספרד | סידור | Liturgy / Siddur | 244/214 | 2 | 3 | CC-BY, Public Domain, unknown | 85% | 1% | יהוה×10 | 24 | 6 |
| Weekday Siddur Sefard Linear | סידור ספרד לימות החול | סידור | Liturgy / Siddur | 86/81 | 2 | 1 | CC-BY | 100% | 9% | יהוה×56 | 0 | 0 |

### Machzor Rosh Hashanah Sefard — מחזור ראש השנה ספרד

- דוגמת ref לעלה: `Machzor Rosh Hashanah Sefard, Laws of Erev Rosh Hashanah`
- עומק טקסט בעלים: {'1': 76}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Laws of Erev Rosh Hashanah (דיני ערב ראש השנה); Annullment of Vows (סדר התרת נדרים); Yesod HaTeshuva of Rabbeinu Yonah (יסוד התשובה להחסיד רבנו יונה); Eiruv Chatzerot (סדר עירובי חצרות); Eiruv Tavshilin (סדר עירוב תבשילין); Eiruv Techumin (סדר עירובי תחומין); Lighting the Candles (סדר הדלקת נרות); Mincha for Erev Rosh Hashanah (מנחה לערב ראש השנה); Maariv (תפלת ערבית); Kiddush (קידוש לראש השנה); Rosh Hashanah Customs (מנהגי ליל ראש השנה); The Morning Prayers (תפלת שחרית); Reading of the Torah (קריאת התורה); Sounding of the Shofar (תקיעת שופר); Musaf (תפלת מוסף); Laws of Rosh Hashanah Day (דינים ומנהגים ליום ראש השנה); Mincha (מנחה לראש השנה); Tashlich (סדר תשליך)
- דגימה: 105 מחרוזות, 5676 מילים; ניקוד 81%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יהוה×61, יי×12, ה׳ (קיצור)×9, אדני×4
- תגיות HTML: b×79, small×74, big×15, strong×15, sup×1, i×1
- דוגמאות `<small>`: «כאשר האדם קם ממטתו שחרית (בבוקר) הוא כמו בריה חדשה לעבודת הבורא יתברך שמו, לכן צ» · «ואומר מודה אני אף קודם נטילת ידים, כיון שאין בו שם. מלבוש ראשון ילבש הטלית קטן ש» · «כתוב: ברכי נפשי את ה' וכל קרבי את שם קדשו, וכיון שצריך האדם לברך את השם בכל קרבי» · «תפלה נאה מספר שערי ציון לאומרה בכל בוקר:» · «הירא את דבר ה' ירגיל לומר הזמר הזה בכל בוקר. (ומחברו מגדולי הספרדים). וחתום שמעי»
- דוגמאות בסוגריים: «בבוקר» · «ומחברו מגדולי הספרדים» · «נ"א  קַרְקַפְתָּא דְלָא מַנַּח תְּפִלִּין» · «יו"ד ה"א וא"ו ה"א» · «ס"א  יְחִידָא»
- מילות הוראה: אומר×9, אומרים×4, בשבת×3, הקהל×2, החזן×1
- פיסוק: פסיק×440, נקודתיים×190, נקודה×164, מרכאות (")×59, גרש לטיני (')×17, מקף לטיני (-)×2
  - דגימה `Machzor Rosh Hashanah Sefard, Laws of Erev Rosh Hashanah` [Machzor Rosh Hashanah]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Machzor Rosh Hashanah Sefard, The Morning Prayers, Upon Arising in the Morning` [Machzor Rosh Hashanah]: HTTP 200, קינון 1, 37 מחרוזות
  - דגימה `Machzor Rosh Hashanah Sefard, The Morning Prayers, Second Day of Rosh Hashana, Blessings of the Shema` [Machzor Rosh Hashanah]: HTTP 200, קינון 1, 35 מחרוזות
  - דגימה `Machzor Rosh Hashanah Sefard, Sounding of the Shofar, Rav Saadiah Gaon's Ten Reasons for Shofar Sounding` [Machzor Rosh Hashanah]: HTTP 200, קינון 1, 10 מחרוזות
  - דגימה `Machzor Rosh Hashanah Sefard, Tashlich` [Machzor Rosh Hashanah]: HTTP 200, קינון 1, 20 מחרוזות

### Machzor Yom Kippur Sefard — מחזור ליום כפור ספרד

- דוגמת ref לעלה: `Machzor Yom Kippur Sefard, Kapparot`
- עומק טקסט בעלים: {'1': 67}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kapparot (סדר כפרות); Mincha Service for Erev Yom Kippur (מנחה לערב יום כפור); Candle Lighting (סדר הדלקת הנר); Blessing the Children (סדר ברכת הבנים); Before Kol Nidrei (קודם כל נדרי); Kol Nidrei (כל נדרי); Maariv Service for Yom Kippur Eve (תפלת ערבית לליל יום כפור); Customs of Yom Kippur Night (סדר ליל יום כפור); The Morning Prayers (תפלת שחרית); Reading of the Torah (קריאת התורה); Memorial Services (סדר הזכרת נשמות); Musaf Service (תפלת מוסף); Mincha Service (תפלת מנחה ליום כפור); Neilah Service (תפלת נעילה); Maariv Service for Motzei Yom Kippur (תפלת ערבית למוצאי יום כפור); On Motzei Shabbat (למוצאי שבת); Kiddush Levanah (סדר קידוש לבנה); Havdalah (סדר הבדלה)
- דגימה: 137 מחרוזות, 2690 מילים; ניקוד 69%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יהוה×63, ה׳ (קיצור)×4, אדני×3
- תגיות HTML: small×77, b×61, big×9, strong×9
- דוגמאות `<small>`: «לש"ץ חצי קדיש» · «חזן» · «נ"א» · «קו"ח» · «חזן»
- דוגמאות בסוגריים: «מט"א» · «נ"א  קֵץ» · «לכהנים  שֶׁצִּוִּיתָנוּ» · «לקהל  שֶׁצִּוִּיתָ» · «החזן בלחש»
- מילות הוראה: אומר×10, אומרים×4, ש"ץ×3, החזן×3, הקהל×2, בשבת×2, בחול×2, כאן×2
- פיסוק: פסיק×208, נקודתיים×132, נקודה×130, מרכאות (")×57, גרש לטיני (')×25
  - דגימה `Machzor Yom Kippur Sefard, Kapparot` [Machzor Yom Kippur]: HTTP 200, קינון 1, 23 מחרוזות
  - דגימה `Machzor Yom Kippur Sefard, Maariv Service for Yom Kippur Eve, Aleinu` [Machzor Yom Kippur]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Machzor Yom Kippur Sefard, The Morning Prayers, The King` [Machzor Yom Kippur]: HTTP 200, קינון 1, 14 מחרוזות
  - דגימה `Machzor Yom Kippur Sefard, Musaf Service, Priestly Blessing` [Machzor Yom Kippur]: HTTP 200, קינון 1, 80 מחרוזות
  - דגימה `Machzor Yom Kippur Sefard, Havdalah` [Machzor Yom Kippur]: HTTP 200, קינון 1, 17 מחרוזות

### Shabbat Siddur Sefard Linear — סידור ספרד לשבת

- דוגמת ref לעלה: `Shabbat Siddur Sefard Linear, Eiruv Tavshilin`
- עומק טקסט בעלים: {'1': 137, '2': 2}; sectionNames: Chapter / Paragraph, Chapter / Verse, Paragraph; צמתים בלי heTitle: 23
- צמתים ברמה הראשונה: Eiruv Tavshilin (עירוב תבשילין); Eiruvei Chatzeiros (עירובי חצרות); Eiruvei Techumin (עירובי תחומין);  ();  (); Mincha Service for Erev Shabbos (תפלת מנחה לערב שבת); Kabbalas Shabbos (קבלת שבת); Maariv Service for Shabbos and Yom Tov (תפלת ערבית לשבת ויו"ט); Order of Shabbos in the Home (סדר ליל שבת); Songs for Shabbos Eve (זמירות לליל שבת); Birchas Hamazon (ברכת המזון); Berachos Said Upon Witnessing Phenomenal Sights (ברכות הראיה); Various Other Berachos (ברכות שונות); The Morning Prayers (תפלת שחרית); Reading of the Torah (קריאת התורה); Musaf Service (תפלת מוסף); Kiddush for Shabbos day (קידוש ליום השבת); Songs for Shabbos Morning (זמירות ליום השבת); Mincha Service for Shabbos and Yom Tov (מנחה לשבת ויום טוב); Songs for Seudah Shelishis (זמירות לסעודה שלישית); Maariv Service for the Conclusion of Shabbos (תפלת ערבית למוצאי שבת); Kiddush Levanah (קידוש לבנה);  (); Songs for Motzoei Shabbos (זמירות למוצאי שבת); Hallel (הלל) …
- דגימה: 699 מחרוזות, 1962 מילים; ניקוד 100%, טעמים 10%, קמץ קטן (U+05C7) ×0, מתג ×392
- שם ה׳: יהוה×95, אדני×1
- תגיות HTML: small×5, b×2
- דוגמאות `<small>`: «בלחש» · «בקול רם» · «סַבְרִי מָרָנָן וְרַבּוֹתַי:» · «בִּרְשׁוּת» · «מָרָנָן וְרַבּוֹתַי:»
- דוגמאות בסוגריים: «כִּי הוּא יוֹם»
- מילות הוראה: הקהל×1, בשבת×1
- פיסוק: נקודתיים×206, מקף (־)×163, נקודה×48, פסיק×9, קו ארוך (—)×1, קו מפריד (–)×1
  - דגימה `Shabbat Siddur Sefard Linear, Eiruv Tavshilin` [The Metsudah Siddur, Metsudah Publications, 1981 - HE]: HTTP 200, קינון 1, 14 מחרוזות
  - דגימה `Shabbat Siddur Sefard Linear, Order of Shabbos in the Home, Kiddush for Shabbos Eve` [The Metsudah Siddur, Metsudah Publications, 1981 - HE]: HTTP 200, קינון 1, 52 מחרוזות
  - דגימה `Shabbat Siddur Sefard Linear, The Morning Prayers, Ashrei` [The Metsudah Siddur, Metsudah Publications, 1981 - HE]: HTTP 200, קינון 1, 285 מחרוזות
  - דגימה `Shabbat Siddur Sefard Linear, Mincha Service for Shabbos and Yom Tov, Ashrei` [The Metsudah Siddur, Metsudah Publications, 1981 - HE]: HTTP 200, קינון 1, 57 מחרוזות
  - דגימה `Shabbat Siddur Sefard Linear, Prayer Before Retiring at Night` [The Metsudah Siddur, Metsudah Publications, 1981 - HE]: HTTP 200, קינון 1, 291 מחרוזות

### Siddur Sefard — סידור ספרד

- דוגמת ref לעלה: `Siddur Sefard, Upon Arising, Modeh Ani`
- עומק טקסט בעלים: {'1': 213, '2': 1}; sectionNames: Chapter / Mishnah, Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Upon Arising (סדר השכמת הבוקר); Weekday Shacharit (שחרית לימות החול); Additional Prayers  (תוספות אחרי שחרית); Weekday Mincha (מנחה לימות החול); Weekday Maariv (ערבית לימות החול); Kiddush Levanah (קידוש לבנה); Bedtime Shema (קריאת שמע שעל המיטה); Lag BaOmer Songs (שירים לל"ג בעומר); Various Blessings (ברכות ותפילות שונות); Mealtime Blessings (סדר סעודה וברכותיה); Birchat HaMazon (סדר ברכת המזון); Blessings (ברכות הנהנין); Eruv Tavshilin (סדר ערוב תבשילין); Shabbat Candle Lighting (סדר הדלקת נרות שבת); Shabbat Eve Mincha (מנחה לערב שבת); Kabbalat Shabbat (קבלת שבת); Shabbat Eve Maariv (ערבית של שבת); Shabbat Evening Meal (סעודת ליל שבת); Shabbat Morning Services (שחרית של שבת); Musaf (מוסף של שבת); Shabbat Day Meal (סעודת שבת); Shabbat Mincha (מנחה לשבת קודש); Third Meal (סעודה שלישית); Motzaei Shabbat  (למוצאי שבת); Shaking Lulav (סדר נטילת לולב) …
- דגימה: 38 מחרוזות, 533 מילים; ניקוד 85%, טעמים 1%, קמץ קטן (U+05C7) ×0, מתג ×14
- שם ה׳: יהוה×10
- תגיות HTML: b×44, small×26, big×3
- דוגמאות `<small>`: «מיד כשיעור משנתו, בעודו על משכבו, יאמר:» · «לאחר שנטל ידיו יאמר:» · «לפני עטיפת הטלית קטן, יברך:» · «נַעֲלֶה וְנָבוֹא אֶל שַׁעֲרֵי מִירוֹן וְשָׁם נָשִׁיר שִׁבְחֵי הַתַּנָּא רַבִּי ש» · «נַעֲלֶה וְנָבוֹא אֶל שַׁעֲרֵי מִירוֹן וְשָׁם נָשִׁיר שִׁבְחֵי הַתַּנָּא רַבִּי ש»
- דוגמאות בסוגריים: «פב"פ» · «ליו"ט וְלִכְבוֹד הַרֶגֶל» · «לר"ה ויו"כ וְלִכְבוֹד יוֹם הַדִּין» · «ליו"ט וְיִזְכֶּה לַעֲלוֹת לָרֶגֶל» · «לר"ה ויו"כ וְיִכְתְּבֵהוּ וְיַחְתְּמֵהוּ לְחַיִּים טוֹבִים בָּזֶה הַיּוֹם»
- מילות הוראה: אומר×2
- פיסוק: פסיק×34, נקודתיים×28, נקודה×22, מרכאות (")×12, גרש לטיני (')×6
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 9/15
  - דגימה `Siddur Sefard, Upon Arising, Modeh Ani` [The Metsudah siddur, 1981]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Siddur Sefard, Lag BaOmer Songs, Naaleh V'Navo` [The Metsudah siddur, 1981]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Sefard, Shabbat Morning Services, Prayer for Oleh` [The Metsudah siddur, 1981]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Sefard, Pesach Haggadah, Korech` [The Metsudah siddur, 1981]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Sefard, Various Prayers & Segulot, Awesome Prayer of Rabbeinu Tam` [The Metsudah siddur, 1981]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Siddur Sefard, Upon Arising, Modeh Ani` [Torat Emet 357]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

### Weekday Siddur Sefard Linear — סידור ספרד לימות החול

- דוגמת ref לעלה: `Weekday Siddur Sefard Linear, The Morning Prayers, Upon Arising in the Morning`
- עומק טקסט בעלים: {'1': 81}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: The Morning Prayers (תפלת שחרית); Birkas Hamazon (ברכת המזון); Concluding Blessings (ברכה מעין שלש); Berachos Said Before Performing Mitzvos (ברכות המצוות); Berachos Said Before Eating or Drinking (ברכות הנהנין); Berachos Said Upon Witnessing Phenomenal Sights (ברכות הראיה); Various Other Berachos (ברכות שונות); Marriage Service (ברכות אירוסין ונשואין); Birchas Hamazon for Sheva Berachos (ברכת המזון לשבע ברכות); Service at a Circumcision (סדר ברית מילה); Birkas Hamzon for Bris Milah (ברכת המזון לברית מילה); Redemption of the Firstborn (סדר פדיון הבן); The Travelers' Prayer (תפלת הדרך); Mincha (תפלת מנחה); Maariv (תפלת מעריב); Counting the Omer (ספירת העומר); Prayer Before Retiring at Night (קריאת שמע על המטה); Berachos on Lulav (ברכות הלולב); Hallel (הלל); Musaf for Rosh Chodesh (מוסף לראש חודש); Musaf for Chol Hamo'ed (מוסף לחול המועד); Hoshanos (הושענות); Chanukah Service (הדלקת נרות חנוכה); Purim Service (ברכות המגילה); Selichos (סליחות)
- דגימה: 441 מחרוזות, 1236 מילים; ניקוד 100%, טעמים 9%, קמץ קטן (U+05C7) ×0, מתג ×199
- שם ה׳: יהוה×56
- תגיות HTML: b×13
- מילות הוראה: הקהל×1
- פיסוק: נקודתיים×125, מקף (־)×104, פסיק×17, נקודה×6, מרכאות (")×1
  - דגימה `Weekday Siddur Sefard Linear, The Morning Prayers, Upon Arising in the Morning` [The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981]: HTTP 200, קינון 1, 29 מחרוזות
  - דגימה `Weekday Siddur Sefard Linear, The Morning Prayers, Ashrei` [The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981]: HTTP 200, קינון 1, 283 מחרוזות
  - דגימה `Weekday Siddur Sefard Linear, The Morning Prayers, Thirteen Principles of Faith` [The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981]: HTTP 200, קינון 1, 73 מחרוזות
  - דגימה `Weekday Siddur Sefard Linear, Maariv, Berachos Preceding Shema` [The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981]: HTTP 200, קינון 1, 56 מחרוזות
  - דגימה `Weekday Siddur Sefard Linear, Selichos, Seventeenth of Tamuz` [The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981]: HTTP 404, קינון —, — מחרוזות — שגיאה: We have no text for Weekday Siddur Sefard Linear, Selichos, Seventeenth of Tamuz.

## נוסח: עדות המזרח / ספרדי

| אינדקס | כותר עברי | סוג | קטגוריות | צמתים/עלים | עומק | גרסאות עבריות | רישיונות | ניקוד | טעמים | שם ה׳ | `<small>` | סוגריים |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Machzor Rosh Hashanah Edot HaMizrach | מחזור ראש השנה עדות המזרח | מחזור | Liturgy / High Holidays | 58/53 | 2 | 1 | unknown | 93% | 9% | יהוה×63, ה׳ (קיצור)×9, אדני×1 | 38 | 8 |
| Machzor Yom Kippur Edot HaMizrach | מחזור יום כיפור עדות המזרח | מחזור | Liturgy / High Holidays | 64/56 | 2 | 1 | unknown | 94% | 5% | יהוה×123, אדני×6 | 227 | 48 |
| Pesach Haggadah Edot Hamizrah | הגדה של פסח עדות המזרח | הגדה | Liturgy / Haggadah | 36/31 | 2 | 2 | unknown | 89% | 16% | יהוה×24, אדני×1 | 15 | 7 |
| Seder Tisha B'Av (Edot HaMizrach) | סדר תשעה באב | אחר | Liturgy / Other Liturgy Works | 12/10 | 2 | 1 | unknown | 97% | 21% | יהוה×155, אדני×12, יי×1 | 64 | 14 |
| Selichot Edot HaMizrach | סליחות נוסח עדות המזרח | סליחות | Liturgy / High Holidays | 1/1 | 0 | 1 | Public Domain | 96% | 0% | יהוה×121, אדני×13, יי×1 | 38 | 40 |
| Siddur Edot HaMizrach | סידור נוסח עדות המזרח | סידור | Liturgy / Siddur | 151/129 | 2 | 4 | CC0, Public Domain, unknown | 95% | 6% | יהוה×177, יי×26, אדני×13 | 178 | 12 |

### Machzor Rosh Hashanah Edot HaMizrach — מחזור ראש השנה עדות המזרח

- דוגמת ref לעלה: `Machzor Rosh Hashanah Edot HaMizrach, Annulment of Vows and Curses`
- עומק טקסט בעלים: {'1': 52, '2': 1}; sectionNames: Chapter / Paragraph, Paragraph; צמתים בלי heTitle: 18
- צמתים ברמה הראשונה: Annulment of Vows and Curses (סדר התרת נדרים וקללות); Eiruv Tavshilin (עירוב תבשילין);  (); Mincha for Erev Rosh Hashana (מנחה לערב ראש השנה);  (); Arvit (ערבית); Nighttime Kiddush (קידוש ליל ראש השנה); Seder Rosh Hashana (סדר ליל ראש השנה); Masekhet Rosh Hashana (מסכת ראש השנה); Zohar Study for Rosh Hashana Night (זהר לסעדת ראש השנה);  ();  (); Opening of the Ark (סדר פתיחת ההיכל); Blessing on the Torah (ברכת התורה); Reading of the Torah for the First Day (קריאה ליום ראשון); Reading of the Torah for the Second Day (קריאה ליום שני); Maftir (מפטיר); Haftarah for the First Day of Rosh Hashana (הפטרה ליום א'); Haftarah for the Second Day of Rosh Hashana (הפטרה ליום שני); Blessing after the Haftarah (ברכות לאחר ההפטרה); Sounding of the Shofar (סדר תקיעת שופר); Unetanneh Tokef (פיוט רבי אמנון); Musaf (מוסף); Daytime Kiddush (סדר קידוש היום);  () …
- דגימה: 120 מחרוזות, 3883 מילים; ניקוד 93%, טעמים 9%, קמץ קטן (U+05C7) ×0, מתג ×217
- שם ה׳: יהוה×63, ה׳ (קיצור)×9, אדני×1
- תגיות HTML: b×99, small×38
- דוגמאות `<small>`: «בעיר הקודש ירושלים ת"ו יש נוהגים לומר התרת קללות בנוסח זה, יעמדו השואלים לפני עש» · «ויענו המתירים:» · «ואחר־כך ימסרו השואלים מודעה זו ויאמרו:» · «ואחר־כך יאמרו המתירים קבלת מסירת המודעה, וזה נוסחה:» · «יש נוהגים לעשות התרה ביום י"ט אב שהוא ארבעים יום לפני ראש־השנה, ובערב ראש־חודש א»
- דוגמאות בסוגריים: «נ"א בִּרְשׁוּת» · «הֻתְּרוּ מֵעִקָּרָן» · «בצפורן שמיר» · «קר"ע שט"ן» · «מספר "לשון חכמים" ח"א»
- מילות הוראה: כאן×6, אומרים×4, אומר×4, נוהגים×3, בשבת×2, בחול×1
- פיסוק: פסיק×461, מקף (־)×239, נקודה×143, נקודתיים×105, מרכאות (")×32, גרש לטיני (')×12
  - דגימה `Machzor Rosh Hashanah Edot HaMizrach, Annulment of Vows and Curses` [Machzor Edot HaMizrach for Rosh Hashanah]: HTTP 200, קינון 1, 34 מחרוזות
  - דגימה `Machzor Rosh Hashanah Edot HaMizrach, Nighttime Kiddush` [Machzor Edot HaMizrach for Rosh Hashanah]: HTTP 200, קינון 1, 85 מחרוזות
  - דגימה `Machzor Rosh Hashanah Edot HaMizrach, Baruch She'amar` [Machzor Edot HaMizrach for Rosh Hashanah]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Machzor Rosh Hashanah Edot HaMizrach', please pass a more specific ref for this book, and try again. 'Machzor Rosh Hashanah Edot HaMizrach' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a t
  - דגימה `Machzor Rosh Hashanah Edot HaMizrach, Haftarah for the Second Day of Rosh Hashana` [Machzor Edot HaMizrach for Rosh Hashanah]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Machzor Rosh Hashanah Edot HaMizrach` [Machzor Edot HaMizrach for Rosh Hashanah]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Machzor Rosh Hashanah Edot HaMizrach', please pass a more specific ref for this book, and try again. 'Machzor Rosh Hashanah Edot HaMizrach' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a t

### Machzor Yom Kippur Edot HaMizrach — מחזור יום כיפור עדות המזרח

- דוגמת ref לעלה: `Machzor Yom Kippur Edot HaMizrach, Kapparot`
- עומק טקסט בעלים: {'1': 56}; sectionNames: Paragraph; צמתים בלי heTitle: 21
- צמתים ברמה הראשונה: Kapparot (כפרות);  (); Mincha for Yom Kippur Eve (מנחה לערב יום הכיפורים); Seudah HaMafseket (סעודת המפסקת);  (); Blessing the Children (ברכת הבנים); Arvit (ערבית);  (); Mussaf (מוסף);  (); Neilah (נעילה); Motzei Yom Kippur (מוצאי החג)
- דגימה: 106 מחרוזות, 7589 מילים; ניקוד 94%, טעמים 5%, קמץ קטן (U+05C7) ×11, מתג ×487
- שם ה׳: יהוה×123, אדני×6
- תגיות HTML: b×296, small×253, br×250
- דוגמאות `<small>`: «בסיבוב כפרות יכוין לשם חת״ך בראשי תבות: זה חליפתך, תמורת, כפרתך, והוא יוצא מסופי» · «המסבב תרנגול לעצמו יאמר» · «שלש פעמים» · «המסבב תרנגול לאחר יאמר» · «(»
- דוגמאות בסוגריים: «בא״ח וילך ג» · «זֶה» · «זֶה» · «לנקבה   חֲלִיפָתֵךְ» · «זֶה»
- מילות הוראה: אומר×33, החזן×13, אומרים×12, בשבת×7, כאן×4, הקהל×3, יש אומרים×2, נוהגים×2
- פיסוק: נקודה×893, נקודתיים×402, פסיק×311, מקף (־)×197, סוף פסוק (׃)×46, גרשיים (״)×31, פסק (׀)×16, גרש (׳)×2
  - דגימה `Machzor Yom Kippur Edot HaMizrach, Kapparot` [Wikisource]: HTTP 200, קינון 1, 10 מחרוזות
  - דגימה `Machzor Yom Kippur Edot HaMizrach, Arvit, Barechu` [Wikisource]: HTTP 200, קינון 1, 5 מחרוזות
  - דגימה `Machzor Yom Kippur Edot HaMizrach` [Wikisource]: HTTP 400, קינון —, — מחרוזות — שגיאה: You passed 'Machzor Yom Kippur Edot HaMizrach', please pass a more specific ref for this book, and try again. 'Machzor Yom Kippur Edot HaMizrach' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on
  - דגימה `Machzor Yom Kippur Edot HaMizrach, Mussaf, Reader's Repetition` [Wikisource]: HTTP 200, קינון 1, 89 מחרוזות
  - דגימה `Machzor Yom Kippur Edot HaMizrach, Motzei Yom Kippur` [Wikisource]: HTTP 200, קינון 1, 2 מחרוזות

### Pesach Haggadah Edot Hamizrah — הגדה של פסח עדות המזרח

- דוגמת ref לעלה: `Pesach Haggadah Edot Hamizrah, Kadesh`
- עומק טקסט בעלים: {'1': 31}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Kadesh (קדש); Urchatz (ורחץ); Karpas (כרפס); Yachatz (יחץ); Magid (מגיד); Rachtzah (רחצה); Motzi Matzah (מוציא מצה); Maror (מרור); Korech (כורך); Shulchan Orech (שולחן עורך); Tzafun (צפון); Barech (ברך); Hallel (הלל); Nirtzah (נרצה)
- דגימה: 45 מחרוזות, 1338 מילים; ניקוד 89%, טעמים 16%, קמץ קטן (U+05C7) ×0, מתג ×50
- שם ה׳: יהוה×24, אדני×1
- תגיות HTML: small×15, b×2
- דוגמאות `<small>`: «מוזגין לו כוס ראשון ומקדש עליו» · «קודם הקידוש יאמר בקשה זו (מלשון חכמים ח"א)» · «כל אחד מבני הבית יקח כוסו בידו ויעמוד, והמקדש יקבל את הכוס בשתי ידיו משתי ידיו ש» · «אם חל בשבת אומר שלום עליכם, אשת חיל, ואתקינו סעדתא ומדלג אזמר בשבחין. ואחר כך או» · «אם חל יום טוב בחול מתחילים מכאן»
- דוגמאות בסוגריים: «מלשון חכמים ח"א» · «יהוה» · «בשבת שַׁבָּתוֹת לִמְנוּחָה וּ» · «בשבת יוֹם הַשַּׁבָּת הַזֶּה וְאֶת» · «בשבת וְשַׁבָּתוֹת וּ»
- מילות הוראה: אומר×4, בשבת×2, אומרים×1, בחול×1, כאן×1
- פיסוק: נקודה×123, פסיק×80, מקף (־)×37, סוף פסוק (׃)×28, נקודתיים×28, סימן שאלה×13, מקף לטיני (-)×11, פסק (׀)×6
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 5/10
  - דגימה `Pesach Haggadah Edot Hamizrah, Kadesh` [Haggadah Shaliehsaboo Edition]: HTTP 200, קינון 1, 20 מחרוזות
  - דגימה `Pesach Haggadah Edot Hamizrah, Magid, The Four Sons` [Haggadah Shaliehsaboo Edition]: HTTP 200, קינון 1, 5 מחרוזות
  - דגימה `Pesach Haggadah Edot Hamizrah, Magid, First Half of Hallel` [Haggadah Shaliehsaboo Edition]: HTTP 200, קינון 1, 4 מחרוזות
  - דגימה `Pesach Haggadah Edot Hamizrah, Tzafun` [Haggadah Shaliehsaboo Edition]: HTTP 200, קינון 1, 3 מחרוזות
  - דגימה `Pesach Haggadah Edot Hamizrah, Nirtzah, Echad Mi Yodea` [Haggadah Shaliehsaboo Edition]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו
  - דגימה `Pesach Haggadah Edot Hamizrah, Kadesh` [Pesach Haggadah]: HTTP 200, קינון —, — מחרוזות — אין טקסט בגרסה הזו

### Seder Tisha B'Av (Edot HaMizrach) — סדר תשעה באב

- דוגמת ref לעלה: `Seder Tisha B'Av (Edot HaMizrach), Tisha B'Av Night, Al Naharot Bavel`
- עומק טקסט בעלים: {'1': 7, '2': 3}; sectionNames: Chapter / Paragraph, Chapter / Verse, Paragraph; צמתים בלי heTitle: 1
- צמתים ברמה הראשונה: Tisha B'Av Night (ליל תשעה באב); Tisha B'Av Day (יום תשעה באב)
- דגימה: 347 מחרוזות, 9494 מילים; ניקוד 97%, טעמים 21%, קמץ קטן (U+05C7) ×50, מתג ×1315
- שם ה׳: יהוה×155, אדני×12, יי×1
- תגיות HTML: b×93, small×76, br×1
- דוגמאות `<small>`: «פותחים את ההיכל ומשאירים אותו פתוח עד חצות היום בתשעה באב» · «יש אומרים» · «הקהל יושב על הקרקע ומתחילים בקינות» · «ואומר החזן:» · «ועונים הקהל והחזן:»
- דוגמאות בסוגריים: «יְהֹוָה אַל תִּקְצֹף עַד מְאֹד לְהַכְנִיעִי, וְאַל לָעַד תִּזְכּוֹר עָוֹן לְהַרְ» · «נָא הַחֲיֵה רְדוּמֵֽינוּ בְּכוֹס תַּֽעַל, מֵמִית וּמְחַיֶּה מוֹרִיד שְׁאוֹל וַיַ» · «דּוֹדִי מָתַי תָּשׁוּב לְבֵית מְעוֹנִים. וְתָשִׁיב לֵב אָבוֹת עַל בָּנִים. יְרַנ» · «מִי לֹא יִירָא הֲמוֹן שֵֽׁבֶט אַף נְצִבִים? הֵם הַכְּפִירִים הַהוֹמִים כְּדוֹבִי» · «חַנּוּן עַד אָנָה תְּהִי נַחֲלָתְךָ חֲרֵבָה. נְטוּשָׁה בְיַד זָרִים וַעֲזוּבָה. »
- מילות הוראה: אומר×10, אומרים×6, הקהל×3, יש אומרים×2, החזן×2
- פיסוק: נקודה×880, פסיק×535, נקודתיים×455, מקף (־)×350, סוף פסוק (׃)×184, פסק (׀)×37, סימן שאלה×14, גרשיים (״)×4
  - דגימה `Seder Tisha B'Av (Edot HaMizrach), Tisha B'Av Night, Al Naharot Bavel` [Seder Tisha B'Av - Kollel Ohr Haemet]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Seder Tisha B'Av (Edot HaMizrach), Tisha B'Av Night, Ha'azinu HaShamayim` [Seder Tisha B'Av - Kollel Ohr Haemet]: HTTP 200, קינון 1, 1 מחרוזות
  - דגימה `Seder Tisha B'Av (Edot HaMizrach), Tisha B'Av Night, L'mi Evkeh` [Seder Tisha B'Av - Kollel Ohr Haemet]: HTTP 200, קינון 1, 2 מחרוזות
  - דגימה `Seder Tisha B'Av (Edot HaMizrach), Tisha B'Av Night, Aleinu` [Seder Tisha B'Av - Kollel Ohr Haemet]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Seder Tisha B'Av (Edot HaMizrach), Tisha B'Av Day` [Seder Tisha B'Av - Kollel Ohr Haemet]: HTTP 200, קינון 2, 330 מחרוזות

### Selichot Edot HaMizrach — סליחות נוסח עדות המזרח

- דוגמת ref לעלה: `Selichot Edot HaMizrach`
- עומק טקסט בעלים: {'1': 1}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- דגימה: 229 מחרוזות, 5461 מילים; ניקוד 96%, טעמים 0%, קמץ קטן (U+05C7) ×0, מתג ×0
- שם ה׳: יהוה×121, אדני×13, יי×1
- תגיות HTML: b×59, small×38, br×13, big×3, strong×3
- דוגמאות `<small>`: «(ואומר השליח צבור חצי קדיש)» · «(אמן)» · «(אמן)» · «(אמן)» · «(אמן)»
- דוגמאות בסוגריים: «ואומר השליח צבור חצי קדיש» · «אמן» · «אמן» · «אמן» · «אמן»
- מילות הוראה: אומר×14, אומרים×11, בעשרת ימי תשובה×7, יש אומרים×2, נוהגים×1, שליח ציבור×1
- פיסוק: נקודה×900, נקודתיים×517, פסיק×149, מרכאות (")×4, גרש לטיני (')×2, מקף (־)×1
  - דגימה `Selichot Edot HaMizrach` [Selichot Edot HaMizrach - Torat Emet]: HTTP 200, קינון 1, 229 מחרוזות

### Siddur Edot HaMizrach — סידור נוסח עדות המזרח

- דוגמת ref לעלה: `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani`
- עומק טקסט בעלים: {'1': 129}; sectionNames: Paragraph; צמתים בלי heTitle: 0
- צמתים ברמה הראשונה: Preparatory Prayers (סדר השכמת הבוקר); The Midnight Rite (סדר תיקון חצות); Weekday Shacharit (שחרית לימי החול); Additions for Shacharit (תוספות לשחרית); Weekday Mincha (מנחה לימי החול); Weekday Arvit (ערבית לימי החול); Counting of the Omer (ספירת העומר); Blessing of the Moon (ברכת הלבנה); Bedtime Shema (קריאת שמע שעל המיטה); Shabbat Candle Lighting (סדר הדלקת נרות שבת); Song of Songs (שיר השירים); Kabbalat Shabbat (קבלת שבת); Shabbat Arvit (ערבית של שבת); Shabbat Evening (סדר ליל שבת); Post Meal Blessing (ברכת המזון); Al Hamihya (ברכת מעין שלוש); Blessings on Enjoyments (ברכות הנהנין); Shabbat Shacharit (שחרית של שבת); Shabbat Mussaf (מוסף של שבת); Daytime Meal (סדר סעודה שניה); Shabbat Mincha (מנחה של שבת); Third Meal (סעודה שלישית); Havdalah (מוצאי שבת); Rosh Hodesh (סדר ראש חודש); Prayers for Three Festivals (תפילה לשלש רגלים) …
- דגימה: 463 מחרוזות, 15547 מילים; ניקוד 95%, טעמים 6%, קמץ קטן (U+05C7) ×32, מתג ×695
- שם ה׳: יהוה×177, יי×26, אדני×13
- תגיות HTML: b×419, small×227, br×18, big×12
- דוגמאות `<small>`: «כשיעור משנתו יאמר» · «האשה אומרת: מוֹדָה» · «בעשרת ימי תשובה אומרים:» · «בקיץ:» · «בחורף:»
- דוגמאות בסוגריים: «סנסן ליעיר ג:ט» · «בא"ח בשלח הכ"א» · «תהלים צא» · «תהילים קכ״א:א׳-ב׳» · «ואפילו בראש חדש אב»
- מילות הוראה: אומר×245, אומרים×31, בעשרת ימי תשובה×14, כאן×8, יש אומרים×6, נוהגים×5, החזן×5, בחנוכה×4
- פיסוק: פסיק×2173, נקודה×738, נקודתיים×707, מקף (־)×678, סוף פסוק (׃)×129, סימן שאלה×64, מרכאות (")×39, פסק (׀)×23
- דגימות בלי טקסט בגרסה המבוקשת (HTTP 200, ‏versions ריק): 5/15
  - דגימה `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani` [ Shaliehsaboo Edition]: HTTP 200, קינון 1, 4 מחרוזות
  - דגימה `Siddur Edot HaMizrach, Weekday Arvit, Amidah` [ Shaliehsaboo Edition]: HTTP 200, קינון 1, 73 מחרוזות
  - דגימה `Siddur Edot HaMizrach, Shabbat Shacharit, Birkat HaChodesh` [ Shaliehsaboo Edition]: HTTP 200, קינון 1, 7 מחרוזות
  - דגימה `Siddur Edot HaMizrach, Prayers for Three Festivals, Song for Shemini Atzeret` [ Shaliehsaboo Edition]: HTTP 200, קינון 1, 6 מחרוזות
  - דגימה `Siddur Edot HaMizrach, Mishna Study for Shabbat, Pirkei Avot` [ Shaliehsaboo Edition]: HTTP 200, קינון 1, 142 מחרוזות
  - דגימה `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani` [Torat Emet 357]: HTTP 200, קינון 1, 4 מחרוזות

## התנהגות `api/v3/texts` על refs מורכבים וטווחים

| בדיקה | ref | HTTP | שגיאה/אזהרה | צורת text | ref שהוחזר | גרסת ברירת המחדל |
|---|---|---|---|---|---|---|
| עלה | `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani` | 200 | — | קינון 1, 2 מחרוזות | Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani | The Metsudah siddur, 1981 |
| טווח בתוך עלה (1-3) | `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani 1-3` | 200 | — | קינון 1, 2 מחרוזות | Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani 1-3 | The Metsudah siddur, 1981 |
| סגמנט בודד (:1 / 1) | `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani 1` | 200 | — | קינון 0, 1 מחרוזות | Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani 1 | The Metsudah siddur, 1981 |
| טווח בין עלים (ref מלא-ref מלא) | `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani-Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Netilat Yadayim` | 200 | — | קינון 1, 2 מחרוזות | Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani | The Metsudah siddur, 1981 |
| טווח בין עלים (ref-כותר) | `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani-Netilat Yadayim` | 200 | — | קינון 1, 2 מחרוזות | Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani | The Metsudah siddur, 1981 |
| צומת ביניים | `Siddur Ashkenaz, Weekday` | 400 | You passed 'Siddur Ashkenaz, Weekday', please pass a more specific ref for this book, and try again. 'Siddur Ashkenaz, Weekday' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: htt | — | — | — |
| האינדקס כולו | `Siddur Ashkenaz` | 400 | You passed 'Siddur Ashkenaz', please pass a more specific ref for this book, and try again. 'Siddur Ashkenaz' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://developers.se | — | — | — |
| עלה | `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani` | 200 | — | קינון 1, 4 מחרוזות | Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani |  Shaliehsaboo Edition |
| טווח בתוך עלה (1-3) | `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani 1-3` | 200 | — | קינון 1, 3 מחרוזות | Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani 1-3 |  Shaliehsaboo Edition |
| סגמנט בודד (:1 / 1) | `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani 1` | 200 | — | קינון 0, 1 מחרוזות | Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani 1 |  Shaliehsaboo Edition |
| טווח בין עלים (ref מלא-ref מלא) | `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani-Siddur Edot HaMizrach, Preparatory Prayers, Morning Blessings` | 200 | — | קינון 1, 4 מחרוזות | Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani |  Shaliehsaboo Edition |
| טווח בין עלים (ref-כותר) | `Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani-Morning Blessings` | 200 | — | קינון 1, 4 מחרוזות | Siddur Edot HaMizrach, Preparatory Prayers, Modeh Ani |  Shaliehsaboo Edition |
| צומת ביניים | `Siddur Edot HaMizrach, Preparatory Prayers` | 400 | You passed 'Siddur Edot HaMizrach, Preparatory Prayers', please pass a more specific ref for this book, and try again. 'Siddur Edot HaMizrach, Preparatory Prayers' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the stru | — | — | — |
| האינדקס כולו | `Siddur Edot HaMizrach` | 400 | You passed 'Siddur Edot HaMizrach', please pass a more specific ref for this book, and try again. 'Siddur Edot HaMizrach' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://d | — | — | — |
| עלה | `Siddur Sefard, Upon Arising, Modeh Ani` | 200 | — | קינון 1, 7 מחרוזות | Siddur Sefard, Upon Arising, Modeh Ani | The Metsudah siddur, 1981 |
| טווח בתוך עלה (1-3) | `Siddur Sefard, Upon Arising, Modeh Ani 1-3` | 200 | — | קינון 1, 3 מחרוזות | Siddur Sefard, Upon Arising, Modeh Ani 1-3 | The Metsudah siddur, 1981 |
| סגמנט בודד (:1 / 1) | `Siddur Sefard, Upon Arising, Modeh Ani 1` | 200 | — | קינון 0, 1 מחרוזות | Siddur Sefard, Upon Arising, Modeh Ani 1 | The Metsudah siddur, 1981 |
| טווח בין עלים (ref מלא-ref מלא) | `Siddur Sefard, Upon Arising, Modeh Ani-Siddur Sefard, Upon Arising, Tallit` | 200 | — | קינון 1, 7 מחרוזות | Siddur Sefard, Upon Arising, Modeh Ani | The Metsudah siddur, 1981 |
| טווח בין עלים (ref-כותר) | `Siddur Sefard, Upon Arising, Modeh Ani-Tallit` | 200 | — | קינון 1, 7 מחרוזות | Siddur Sefard, Upon Arising, Modeh Ani | The Metsudah siddur, 1981 |
| צומת ביניים | `Siddur Sefard, Upon Arising` | 400 | You passed 'Siddur Sefard, Upon Arising', please pass a more specific ref for this book, and try again. 'Siddur Sefard, Upon Arising' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, se | — | — | — |
| האינדקס כולו | `Siddur Sefard` | 400 | You passed 'Siddur Sefard', please pass a more specific ref for this book, and try again. 'Siddur Sefard' is a 'complex' book-level ref. We only support book-level refs in cases of texts with a 'simple' structure. To learn more about the structure of a text on Sefaria, see: https://developers.sefari | — | — | — |

## שגיאות

| URL | שגיאה |
|---|---|
| `https://www.sefaria.org/api/v3/texts/Piskei%20HaSiddur?version=hebrew%7CVocalized+Edition+-+Kehot+Publication+Society` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Rabbi%20Sacks%20on%20Siddur` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/The%20Koren%20Shalem%20Siddur%3B%20Ashkenaz?version=hebrew%7CHebrew+Edition%3B+Koren+Publishers+Jerusalem%2C+2017` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/The%20Koren%20Shalem%20Siddur%3B%20Ashkenaz%2C%20Ma%27ariv%20for%20Shabbat%20and%20Yom%20Tov?version=hebrew%7CHebrew+Edition%3B+Koren+Publishers+Jerusalem%2C+2017` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/The%20Koren%20Shalem%20Siddur%3B%20Ashkenaz%2C%20Gates%20to%20Prayer%2C%20Mourner%27s%20Kaddish%20Transliterated?version=hebrew%7CHebrew+Edition%3B+Koren+Publishers+Jerusalem%2C+2017` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Weekday%20Siddur%20Chabad%2C%20Upon%20Arising?version=hebrew%7CWikisource` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Weekday%20Siddur%20Chabad%2C%20Ashrei%20Uva%20LeZion?version=hebrew%7CWikisource` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Weekday%20Siddur%20Chabad%2C%20Birkat%20HaMazon%20for%20Circumcision?version=hebrew%7CWikisource` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Weekday%20Siddur%20Chabad?version=hebrew%7CWikisource` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Weekday%20Siddur%20Sefard%20Linear%2C%20Selichos%2C%20Seventeenth%20of%20Tamuz?version=hebrew%7CThe+Metsudah+siddur%3A+a+new+linear+siddur+with+English+translation+by+Avrohom+Davis%2C+1981` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Ephod%20Bad%20on%20Pesach%20Haggadah%2C%20Kadesh?version=hebrew%7CHaggadah+Ephod+Bad%2C+Warsaw%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Ephod%20Bad%20on%20Pesach%20Haggadah%2C%20Magid%2C%20Yechol%20Me%27rosh%20Chodesh?version=hebrew%7CHaggadah+Ephod+Bad%2C+Warsaw%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Ephod%20Bad%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CHaggadah+Ephod+Bad%2C+Warsaw%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Ephod%20Bad%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CHaggadah+Ephod+Bad%2C+Warsaw%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kimcha%20Davshuna%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CMahzor+Roma%2C+Bologna+1540` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kimcha%20Davshuna%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CMahzor+Roma%2C+Bologna+1540` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kos%20Eliyahu%20on%20Pesach%20Haggadah%2C%20Kadesh?version=hebrew%7CHaggadah+Kos+Eliyahu.+Djerba%2C+1938` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kos%20Eliyahu%20on%20Pesach%20Haggadah%2C%20Magid%2C%20Yechol%20Me%27rosh%20Chodesh?version=hebrew%7CHaggadah+Kos+Eliyahu.+Djerba%2C+1938` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kos%20Eliyahu%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CHaggadah+Kos+Eliyahu.+Djerba%2C+1938` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kos%20Eliyahu%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CHaggadah+Kos+Eliyahu.+Djerba%2C+1938` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Kos%20Eliyahu%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CHaggadah+Kos+Eliyahu.+Djerba%2C+1938` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Tevele%20Bondi%20on%20Pesach%20Haggadah%2C%20Magid%2C%20Yechol%20Me%27rosh%20Chodesh?version=hebrew%7CHaggadah+shel+Pesach+im+perush+Tevele+Bondi%2C+Frankfort%2C+1898` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Tevele%20Bondi%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CHaggadah+shel+Pesach+im+perush+Tevele+Bondi%2C+Frankfort%2C+1898` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Tevele%20Bondi%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CHaggadah+shel+Pesach+im+perush+Tevele+Bondi%2C+Frankfort%2C+1898` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Maaseh%20Nissim%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CHaggada+Maaseh+Nissim%2C+Warsaw+1895` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Maaseh%20Nissim%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CHaggada+Maaseh+Nissim%2C+Warsaw+1895` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Naftali%20Seva%20Ratzon%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CNaftali+Seva+Ratzon%2C+Furth%2C+1727` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Yismach%20Yisrael%20on%20Pesach%20Haggadah%2C%20Kadesh` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Yismach%20Yisrael%20on%20Pesach%20Haggadah%2C%20Magid%2C%20Yechol%20Me%27rosh%20Chodesh` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Yismach%20Yisrael%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Yismach%20Yisrael%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Shibolei%20HaLeket%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CVilna%2C+1887` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Shibolei%20HaLeket%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CVilna%2C+1887` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Barukh%20SheAmar%20on%20Pesach%20Haggadah%2C%20Kadesh?version=hebrew%7CBarukh+Sheamar+on+Haggadah%2C+Tel+Aviv+1968` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Barukh%20SheAmar%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CBarukh+Sheamar+on+Haggadah%2C+Tel+Aviv+1968` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Barukh%20SheAmar%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CBarukh+Sheamar+on+Haggadah%2C+Tel+Aviv+1968` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Barukh%20SheAmar%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CBarukh+Sheamar+on+Haggadah%2C+Tel+Aviv+1968` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Divrei%20Negidim%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CHaggadah+shel+Pesach+LaMaharal%2C+London%2C+1960` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Divrei%20Negidim%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CHaggadah+shel+Pesach+LaMaharal%2C+London%2C+1960` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah?version=hebrew%7CEnhanced+edition%2C+2023` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CEnhanced+edition%2C+2023` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Songs%20of%20Praise%20and%20Thanks?version=hebrew%7CEnhanced+edition%2C+2023` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CEnhanced+edition%2C+2023` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah?version=hebrew%7CL%27viv%2C+1872` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CL%27viv%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Songs%20of%20Praise%20and%20Thanks?version=hebrew%7CL%27viv%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Zevach%20Pesach%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CL%27viv%2C+1872` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Peirush%20Hafla%27ah%20on%20Pesach%20Haggadah%2C%20Kadesh?version=hebrew%7CL%27viv%2C+1860` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Peirush%20Hafla%27ah%20on%20Pesach%20Haggadah%2C%20Motzi%20Matzah?version=hebrew%7CL%27viv%2C+1860` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Peirush%20Hafla%27ah%20on%20Pesach%20Haggadah%2C%20Hallel%2C%20Fourth%20Cup%20of%20Wine?version=hebrew%7CL%27viv%2C+1860` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Peirush%20Hafla%27ah%20on%20Pesach%20Haggadah%2C%20Nirtzah%2C%20Chad%20Gadya?version=hebrew%7CL%27viv%2C+1860` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Midrash%20BeChiddush%20on%20Pesach%20Haggadah?version=hebrew%7CPrzemy%C5%9Bl%2C+1891` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Machzor%20Rosh%20Hashanah%20Edot%20HaMizrach%2C%20Baruch%20She%27amar?version=hebrew%7CMachzor+Edot+HaMizrach+for+Rosh+Hashanah` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Machzor%20Rosh%20Hashanah%20Edot%20HaMizrach?version=hebrew%7CMachzor+Edot+HaMizrach+for+Rosh+Hashanah` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Machzor%20Yom%20Kippur%20Edot%20HaMizrach?version=hebrew%7CWikisource` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/The%20Koren%20Rosh%20HaShana%20Mahzor%3B%20Ashkenaz?version=hebrew%7CHebrew+Edition%3B+Koren+Publishers+Jerusalem%2C+2019` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/The%20Koren%20Yom%20Kippur%20Mahzor%3B%20Ashkenaz?version=hebrew%7CHebrew+Edition%3B+Koren+Publishers+Jerusalem%2C+2017` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/The%20Koren%20Yom%20Kippur%20Mahzor%3B%20Ashkenaz%2C%20Leader%27s%20Repetition%20for%20Mincha?version=hebrew%7CHebrew+Edition%3B+Koren+Publishers+Jerusalem%2C+2017` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Ma%27avar%20Yabbok?version=hebrew%7CVilna%2C+1860` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Machzor%20Yom%20Ha%27atzmaut%20%26%20Yom%20Yerushalyim` | HTTP 404 |
| `https://www.sefaria.org/api/v3/texts/Sidduro%20Shel%20Shabbat%2C%20Volume%20I?version=hebrew%7CWarsaw%2C+1872` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Sidduro%20Shel%20Shabbat%2C%20Volume%20II?version=hebrew%7CWarsaw%2C+1872` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Siddur%20Ashkenaz%2C%20Weekday` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Siddur%20Ashkenaz` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Siddur%20Edot%20HaMizrach%2C%20Preparatory%20Prayers` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Siddur%20Edot%20HaMizrach` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Siddur%20Sefard%2C%20Upon%20Arising` | HTTP 400 |
| `https://www.sefaria.org/api/v3/texts/Siddur%20Sefard` | HTTP 400 |

## הכרעות (למילוי ע״י בעל הפרויקט)

- נוסחים לשלב 2: ___
- מחזורים/סליחות/קינות לשלב 4: ___
- רישיון: ___

---

## ממצאי המשך: גרסאות מלאות של שלושת הסידורים (שאלות 8.4, 8.5, 8.21, 8.22)

> ⚠️ הסעיף הזה **נכתב ידנית** אחרי הסקר האוטומטי, ולא ע״י `tools/survey_siddur.py`.
> הרצה חוזרת של הסקריפט דורסת את הקובץ, ולכן צריך לשמור את הסעיף הזה לפני שמריצים אותו שוב.
> **מקור:** קריאות אמיתיות ל-sefaria.org ב-19.10.2026. כל גרסה עברית של `Siddur Ashkenaz`,
> ‏`Siddur Sefard` ו-`Siddur Edot HaMizrach` הורדה במלואה דרך
> `GET /download/version/{title} - he - {versionTitle}.json`. רשימת הגרסאות באה מ-`/api/texts/versions/{title}`,
> ובדיקות ברירת המחדל נעשו מול `/api/v3/texts`. הספירות נעשו בסקריפטים חד-פעמיים בתיקיית
> ה-scratchpad (לא נשמרו בריפו). בכל הטקסט המלא נספרו טוקנים שמופרדים ברווח או במקף, אחרי
> הסרת HTML. זה טקסט מלא ולא דגימה, ולכן המספרים כאן גוברים על עמודת "שם ה׳" בטבלאות
> שלמעלה (שם יש 5 עלים בלבד לכל גרסה).

### א. גרסאות עבריות, רישיון וכיסוי

כיסוי = עלים (JaggedArray) שיש בהם טקסט בגרסה, מתוך כל העלים במבנה של הגרסה.

| אינדקס | גרסה (versionTitle מדויק) | רישיון | כיסוי | הערות |
|---|---|---|---|---|
| Siddur Ashkenaz | `The Metsudah siddur, 1981` | CC-BY | 221/454 | ימי חול 170/174, שבת 50/206, חגים 0/59, קדיש 0/6 |
| Siddur Ashkenaz | `Daat Siddur Ashkenaz` | Public Domain | 224/454 | ימי חול 0/174, שבת 151/206, חגים 59/59, ברכות 8/9, קדיש 6/6 |
| Siddur Ashkenaz | `The Metsudah siddur: a new linear siddur with English translation by Avrohom Davis, 1981` | CC-BY | 7/454 | |
| Siddur Ashkenaz | `Torat Emet 357`, ‏`Shema with Cantillation ` (עם רווח בסוף), `Wikipedia`, `Siddur Veshinantam ` (עם רווח בסוף), `Tanach with Nikkud` | unknown | 1/454 כל אחת | גרסאות של עלה בודד |
| **איחוד כל הגרסאות** | | | **448/454** | חסרים: Shabbat › Musaf LeShabbat › Mourner's Kaddish; Shabbat › Shacharit › Amidah › Holiness of God; Shabbat › Shacharit › Pesukei Dezimra › Mizmor Letoda; Shabbat › … › Mi Sheberach › Bat Mitzvah; Weekday › Minchah › Post Amidah › Vidui and 13 Middot; Weekday › Shacharit › … › Prayers for Welfare of the People |
| Siddur Sefard | `The Metsudah siddur, 1981` | CC-BY | 44/214 | כמעט רק ימי חול (שחרית 20/20, מנחה, ערבית) |
| Siddur Sefard | `Torat Emet 357` | Public Domain | 177/214 | כל השבת, החגים, ל״ג בעומר, הגדה וכו׳, אבל שחרית של חול 0/20 |
| Siddur Sefard | `Modeh Anu` | unknown | 1/214 | |
| **איחוד** | | | **214/214** | |
| Siddur Edot HaMizrach | `" Shaliehsaboo Edition"` (**עם רווח בהתחלה**) | CC0 | 129/129 | ברירת המחדל של v3. מוטעם בפסוקים |
| Siddur Edot HaMizrach | `Torat Emet 357` | Public Domain | 129/129 | בלי טעמים |
| Siddur Edot HaMizrach | `Shaliehsaboo Edition` (בלי רווח), `Siddur Edot HaMizrach temp` | unknown | 1/129 כל אחת | |

**מסקנה:** בעדות המזרח יש שתי גרסאות מלאות, ושתיהן ברישיון פתוח. בספרד ובאשכנז אף גרסה
לא מכסה את כל הסידור לבדה, ולכן הטקסט של סידור אחד מורכב משתי מהדורות שונות (מצודה
ל-ימי חול + דעת או תורת אמת לשבת ולחג). לשתי המהדורות כללי כתיב שונים (ראה סעיף ג).

### ב. מה `api/v3/texts` מחזיר בפועל

- **בלי `version`, או עם `version=hebrew` / `version=primary`:** השרת בוחר לכל עלה בנפרד את
  הגרסה העברית העדיפה שיש בה טקסט. דוגמאות אמיתיות:
  `Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani` ← `The Metsudah siddur, 1981`.
  ‏`Siddur Ashkenaz, Shabbat, Shacharit, Preparatory Prayers, Elokai Neshama` ← `Daat Siddur Ashkenaz`.
  ‏`Siddur Sefard, Kabbalat Shabbat` ← `Torat Emet 357`.
  ‏`Siddur Edot HaMizrach, …` ← `" Shaliehsaboo Edition"`.
- **עם `version=hebrew|<title>` לעלה שאין לו טקסט בגרסה הזו:** השרת מחזיר HTTP 200,
  ‏`versions: []` ו-`warnings`. זה קרה ב-9 מ-15 הדגימות של Siddur Sefard. שימו לב:
  ‏`api/segments.py` ו-`pipeline.py` קוראים ל-`versions[0]` אחרי בקשה עם `hebrew|{title}`.
- **צומת ביניים או האינדקס כולו** (למשל `Siddur Ashkenaz, Weekday`): השרת מחזיר HTTP 400
  עם השגיאה "'complex' book-level ref".
- **טווח בין עלים** (`A-B` עם ref מלא, או `A-כותר`): השרת מחזיר HTTP 200, אבל **רק את העלה
  הראשון**, בלי שגיאה ובלי אזהרה (ה-`ref` שחוזר הוא A). זה נבדק בשלושת הסידורים.
- **טווח בתוך עלה** (`Leaf 1-3`) עובד. סגמנט בודד (`Leaf 1`) מוחזר כמחרוזת, לא כרשימה.
- `next`/`prev` בתשובה נותנים את העלה הסמוך. אפשר להשתמש בהם כדי לעבור על תפילה עלה
  אחרי עלה.
- **מבנה:** באשכנז עומק העץ מגיע ל-7, ובספרד ובעדות המזרח ל-2. כל עלה הוא רשימת פסקאות
  (`Paragraph`, עומק 1). חריג: `Siddur Sefard, Pesach Haggadah` (‏Chapter/Mishnah).
  ה-ref נבנה מכותרי הצמתים ולא מה-`key`. למשל ה-key הוא `"Tzitzit (**Includes Yehi Ratzon)"`
  אבל ב-ref כתוב `Tzitzit`.

### ג. שם ה׳: צורות וספירות (8.5, 8.21)

"תחילית" = אות אחת עד שלוש מבין ו/ב/כ/ל/מ/ש/ה לפני השם (למשל `לַיהֹוָה`, `בה'`).

| גרסה | `יהוה` (סה״כ / עם תחילית) | `יי` | `ה'` | כינוי `אלקים` | הערות |
|---|---|---|---|---|---|
| אשכנז · Metsudah 1981 | 975 / 86 (ל 66, ב 9, ו 5, ש 4, כ 2) | 1 | 5, כולם בהוראות `<small>` | 0 | `יְהֹוָה` ×881 |
| אשכנז · Daat | 402 / 46 (ל 31, ב 10, כ 3, ו 1, ש 1) | 106 (`יְיָ` 82, ‏`יי` לא מנוקד 17, עם תחילית `לַייָ` וכד׳ 7) | **707** (‏`ה'` 619, ‏`לה'` 70, ‏`בה'` 7, ‏`וה'` 6, ‏`שה'` 4, ‏`מה'` 1), 699 מהם בטקסט מנוקד שנאמר | 2 (`אֵל אֱלֹקִים עֶלְיוֹן` בשמרו שבתותי, ‏`אֱלֹקים תֵּן` בדרור יקרא) | **בדעת `ה'` היא הצורה העיקרית בטקסט התפילה** |
| ספרד · Metsudah 1981 | 968 / 79 (ל 63, ב 8, ש 4, ו 3, כ 1) | 1 | 8, כולם בהוראות `<small>` | 0 | |
| ספרד · Torat Emet 357 | 3933 / 442 (ל 330, ב 59, ו 24, כ 17, ש 7, מ 4, הל 1) | 38 | 50 (25 בטקסט מנוקד, למשל `זֶה ה' קִוִּינוּ` בשירי ל״ג בעומר) | 31: מהם 27 `הָאֱלֹקִי`/`האלוקי` (תואר לרבנים, "המקובל האלוקי", לא שם ה׳), ו-4 שם ה׳ (`אֱלֹקֵינוּ`, ‏`אֱלֹקֵי`, ‏`אֱלֹקֵיהֶם`, ‏`אלקינו`), למשל `יְהִי ה' אֱלֹקֵינוּ עִמָּנוּ` בשירי ל״ג בעומר | `יֱהֹוִה` (קריאת אלהים) ×1 |
| עדות · Torat Emet 357 | 2428 / 211 (ל 142, ב 26, ו 18, ש 11, כ 8, מ 4, …) | 26 | 28 | 1 (`בָּרוּךָ אַתָּה ה' אֱלֹקֵינוּ` באתקינו סעודתא) | **84 צורות ניקוד קבליות**, למשל `יִהִוִהִ` ×19, ‏`יֻהֻוֻהֻ` ×16, ‏`יַהַוַהַ` ×13. קריאת "אלהים" (חיריק בוו) ×4 |
| עדות · " Shaliehsaboo Edition" | 2833 / 240 (ל 167, ב 25, ו 22, ש 12, כ 8, מ 4, …) | 2 | 47 (36 בתוך `<small>`) | 0 | **88 צורות קבליות**, בחתימות הברכות של העמידה (למשל `בָּרוּךְ אַתָּה יִהִוִהִ, מְבָרֵךְ הַשָּׁנִים`). הן נאמרות "אדני". קריאת "אלהים" (`יֱהֹוִה`) ×5 |

ממצאים ל-8.21 ולמימוש 4.1.2:
- **`יהוה` עם תחילית שכיח בכל הגרסאות:** בין 46 ל-442 מופעים (`לַיהֹוָה`, `בַּיהֹוָה`, `וַיהֹוָה`, `שֶׁיְהֹוָה`).
  היום `is_tefila_divine_name` בודק `letters_only(piece) in {"יהוה","יי"}`, ולכן `לַיהֹוָה`
  **לא ממופה** ל"לַאדֹנָי". זה נכון לשני המצבים, תנ״ך ותפילה.
- **`ה'` עם תחילית** (`לה'`, ‏`בה'`, ‏`וה'`, ‏`שה'`, ‏`מה'`): 88 מופעים בטקסט הנאמר של דעת אשכנז.
- **קריאת "אלהים"** (`יֱהֹוִה`, ‏`יְהוִה`, ‏`וְלֵיהֹוִה`) מופיעה רק בגרסאות של ספרד ועדות המזרח, 1 עד 5 פעמים
  בכל גרסה. המיפוי הקיים יהפוך אותן ל"אדני", וזה שגוי.
- **צורות ניקוד קבליות** (84 עד 88 בעדות המזרח): כולן `יהוה` באותיות, ולכן הן כבר ממופות ל"אדני", וזה נכון.
  אבל אם ממפים לפי הניקוד, אסור להניח את הניקוד `יְהֹוָה`.
- **`ד'`** בכל הגרסאות הוא כמעט תמיד המספר 4 (`ד' פרשיות`, ‏`ד' עולים`, ‏`ד' מינים`) או קיצור
  (`וכד'`). כשם ה׳ הוא נמצא פעם אחת בלבד, בתוך הוראה (דעת: `ברוך אתה ד', מחיה המתים`). **לא למפות.**
- **`אלקים`/`אלוקינו` כמעט לא מופיעים** כשם ה׳: 0 עד 4 בכל גרסה. `האלקי` הוא תואר. אין סיבה למפות אותם
  לאלהים כברירת מחדל.
- **התאמות שווא בסופר הגולמי שתוקנו כאן:** `בִּכְיִי`, ‏`לְוִיַּי`, ‏`שְׁבוּיֵי` נספרו בטעות כ"יי" עם תחילית.
  מסננים אותם לפי הניקוד ביו״ד הראשונה (חיריק/צירה/פתח/דגש), ולכן הם לא בטבלה.
  ב-`classify_god_name` שבסקריפט הסינון הזה לא קיים, ולכן עמודת "שם ה׳" בטבלאות שלמעלה עלולה
  לכלול אותם.

### ד. איך מסומנות הוראות (8.4)

| גרסה | `<small>`: לא מנוקד / מנוקד | עוד סימון | שורות שלמות בלי ניקוד |
|---|---|---|---|
| אשכנז · Metsudah | 446 / 40 | `<b>` ×658 לפתיחת קטע (כמעט תמיד מנוקד). סוגריים ×170: תוספות לפי זמן (`(בעשי"ת … לעלא לעלא)`), ‏`(אמן)` ומקורות (`(אבודרהם)`) | 242 (`שליח ציבור:`, ‏`קהל וחזן:`, הלכות ארוכות) |
| אשכנז · Daat | 413 / 124 (`<em>` בתוך `<small>`) | סוגריים מרובעים ×56: ‏`[קהל: אמן]`, ‏`[אמן]` | 222 |
| ספרד · Metsudah | 430 / 33 | כמו מצודה אשכנז | 337 |
| ספרד · Torat Emet | 1759 / 1713 | `<b>` ×6181, ‏`<big>` ×151. סוגריים ×654. ב-`<small>` יש גם מספרי עליות (`שני`, `שלישי`) וגם פזמונים שלמים | 944 |
| עדות · Torat Emet | 1214 / 750 | `[אמן]` ×212 (רובם בתוך `<small>`) | 740 |
| עדות · Shaliehsaboo | 1465 / 739 | `[אמן]` ×252, מקורות בסוגריים (`(בא"ח בשלח הכ"א)`, ‏`(תהילים קמ״ה:א׳-ב׳)`) | 799 |

מסקנה: `<small>` הוא הסימון העיקרי, אבל **הוא לא מזהה הוראה בוודאות**. מתחת לתגית `<small>`
מופיעים גם טקסטים שנאמרים בפועל: `בָּרוּךְ שֵׁם כְּבוֹד מַלְכוּתוֹ` (נאמר בלחש), תוספות
לעשי״ת (`זָכְרֵנוּ לְחַיִּים`), מענה הקהל (`[אמן]`, ‏`יהא שמיה רבה`) ופזמונים חוזרים. יש היוריסטיקה
טובה שמבוססת על הנתונים: **אם התוכן ב-`<small>`/בסוגריים לא מנוקד, זו הוראה. אם הוא מנוקד, זה
טקסט שנאמר, אולי כחלק אופציונלי או חלופי.** יש חריגים בתוך שורות מנוקדות: מילים לא מנוקדות
שהן הוראה או קיצור, כמו `בעשי"ת` ×69, שמות חודשים (`אייר`, ‏`ניסן`) ו-`ג"פ`. ובדעת אשכנז
`ה'` לא מנוקד הוא **טקסט שנאמר**. לכן "לא מנוקד ⇒ הוראה" צריך חריג לשם ה׳.

### ה. טעמים בפסוקים מצוטטים, וסימונים שנראים כמו טעמים (8.22)

- **עדות המזרח · Shaliehsaboo (ברירת המחדל):** פסוקים מצוטטים מוטעמים במלואם. 996 מתוך 3353
  מחרוזות הן עם טעמי מקרא אמיתיים (מונח, מרכא, אתנח, טפחא…), למשל קריאת שמע 7/21, אשרי 4/6,
  פסוקי דזמרה 15/26. יש בה **כתיב/קרי בסוגריים מרובעים**: הכתיב לא מנוקד ואחריו הקרי המנוקד בסוגריים,
  למשל `הביט [הַבִּ֖יטָה]`, ‏`אין [וְאֵ֣ין]` (תיקון רחל). יש 74 מופעים כאלה.
  **תשובה ל-8.22: ביחידות `taamim` צריך להשאיר את זיהוי הכתיב פעיל.** אחרת `הביט` הלא-מנוקד
  ייכנס ליישור במצב `tefila`. עוד אפשרות היא לזהות את התבנית `X [Y]` לפני החיתוך.
- **עדות המזרח · Torat Emet, אשכנז · Daat:** אין בהן טעמים בכלל.
- **⚠️ מצודה (אשכנז וספרד) משתמשת בתווי טעמים לסימון הגייה, לא כטעמים:**
  - ‏U+0592 (סגולתא) מופיע **תמיד אחרי שווא**: 1500 מתוך 1500 באשכנז, ו-1712 מתוך 1717 בספרד.
    זה סימון של שווא נע (`קִדְּ֒שָֽׁנוּ`, ‏`יְבָרֶכְ֒ךָ`).
  - ‏U+05AF (עיגול מסורה) מסמן הפרדה בין מילים בקריאת שמע (`בְּכָל֯־לְ֯בָבְךָ`, ‏`עַל֯־יָ֯דֶֽךָ`).
  - בדקנו את `_unit_chunk` הקיים (`src/aligner/pipeline.py`) על הטקסט האמיתי. הוא מסווג
    **490 מתוך 1518 פסקאות של מצודה אשכנז ו-502 מתוך 1300 של מצודה ספרד כ-`taamim`**.
    כמעט כולן (490 ו-494) רק בגלל התווים האלה, ולכן הן ייחתכו בחותך הטעמים במקום בחותך הפרוזה.
    גם ב-Torat Emet ספרד יש 45 פסקאות כאלה (U+0592 ×150). ב-Shaliehsaboo יש 996 פסקאות
    `taamim`, וכולן טעמים אמיתיים.
  - במצודה ספרד יש גם טעמים אמיתיים, בכמה פסקאות בלבד (למשל `Additional Prayers › Chapter of Fear of God`, דברים י:יב).
- קמץ קטן (U+05C7): 1017 ב-Shaliehsaboo, 26 בדעת, 4 בתורת אמת ספרד, 0 במצודה.
  מתג (U+05BD): נפוץ מאוד במצודה (5750 באשכנז) וב-Shaliehsaboo (12477).

### ו. השלכות מוצעות (לא בוצעו, אין כאן שינוי קוד)

1. **שאלה פתוחה חדשה (מוצעת 8.24):** סגולתא ועיגול המסורה של מצודה מטעים את זיהוי הטעמים
   האוטומטי. כדאי להוסיף את U+0592 ו-U+05AF ל-`_NOT_TAAMIM_EVIDENCE`, או לדרוש לפחות טעם מפסיק
   אחד שאינו סגולתא. לפני כן צריך לבדוק את ההשפעה על פסוקי תנ״ך אמיתיים, שבהם סגולתא היא טעם.
2. ב-8.21: למפות `יהוה` ו-`יי` עם תחיליות ל"אדני" עם אותה תחילית. גם `ה'` עם תחילית (`לה'`, ‏`בה'`, ‏`וה'`, ‏`שה'`, ‏`מה'`).
   לא למפות `ד'`. קריאת "אלהים" (חיריק בוו) תמופה ל"אלהים".
3. משיכת טקסט לשלב 2: למשוך עלה אחרי עלה ולא להשתמש בטווחים בין צמתים. לשמור את
   `versionTitle` של כל עלה. לפי הצורך: לקבע גרסה לכל נוסח, או להשתמש ב-`version=hebrew` ולתעד את המהדורה שחזרה.
