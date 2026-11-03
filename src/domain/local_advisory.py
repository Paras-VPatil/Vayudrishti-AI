"""
src/domain/local_advisory.py
----------------------------
Multilingual (Marathi मराठी, Hindi हिंदी, English) Local Advisory Engine for Maharashtra.

Provides tailored, actionable health, agricultural, occupational, and civic advisories
based on calculated AQI, dominant pollutant, season, and demographic persona:
  1. General Public (सामान्य नागरिक / आम नागरिक)
  2. Sensitive & Vulnerable Groups (ज्येष्ठ नागरिक, लहान मुले, दम्याचे रुग्ण)
  3. Farmers & Rural Agricultural Workers (शेतकरी व शेतमजूर - धुरके, काडीकचरा, फवारणी)
  4. Traffic Police, Transit & Delivery Workers (वाहतूक पोलीस, बस/रिक्षा चालक, डिलिव्हरी कामगार)
  5. Outdoor Construction & Daily Laborers (बांधकाम मजूर, रस्त्यावरील विक्रेते)
  6. Schools, Colleges & Sports Enthusiasts (शाळा, महाविद्यालये आणि मैदानी खेळ)
"""

from typing import Dict, Any, List, Optional
from src.domain.aqi import aqi_to_category, get_category_color
from src.domain.districts import find_nearest_district


# ─────────────────────────────────────────────────────────────────────────────
# Local Persona Templates by Language & AQI Category
# ─────────────────────────────────────────────────────────────────────────────

ADVISORY_TEMPLATES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "mr": {  # मराठी (Marathi)
        "Good": {
            "headline": "हवेची गुणवत्ता समाधानकारक (उत्कृष्ट)",
            "summary": "हवा अतिशय स्वच्छ आहे. सर्व प्रकारच्या बाह्य कामांसाठी आणि व्यायामासाठी हवा अनुकूल आहे.",
            "personas": {
                "general": "सकाळचे फिरणे, व्यायाम आणि बाह्य कामांसाठी वातावरण अत्यंत उत्तम आहे. कोणतीही खबरदारी बाळगण्याची गरज नाही.",
                "sensitive": "लहान मुले, ज्येष्ठ नागरिक आणि दम्याच्या रुग्णांना बाहेर मोकळ्या हवेत खेळणे किंवा फिरणे सुरक्षित आहे.",
                "farmer": "शेतातील कामांसाठी, मळणी आणि कीटकनाशक फवारणीसाठी हवामान अनुकूल आहे. हवा स्वच्छ असल्याने धूळ सहज विरघळते.",
                "traffic_worker": "वाहतूक नियमन करताना अतिरिक्त श्वसन संरक्षणाची आवश्यकता नाही. बाह्य ड्युटीसाठी दिवस उत्तम.",
                "outdoor_worker": "बांधकाम आणि बाह्य कष्टाच्या कामांसाठी दिवस अतिशय योग्य आहे. भरपूर पाणी प्या.",
                "schools": "शाळेतील मैदानी खेळ, क्रीडा स्पर्धा आणि बाह्य उपक्रम सुरळीतपणे राबवता येतील."
            },
            "mask_recommendation": "मास्कची गरज नाही",
            "ventilation": "घरातील खिडक्या उघड्या ठेवून मोकळी हवा घरात येऊ द्या."
        },
        "Satisfactory": {
            "headline": "हवेची गुणवत्ता मध्यम (समाधानकारक)",
            "summary": "हवेची गुणवत्ता सर्वसाधारणपणे स्वीकार्य आहे; मात्र अतिसंवेदनशील व्यक्तींनी किंचित काळजी घ्यावी.",
            "personas": {
                "general": "दैनंदिन कामे आणि सकाळचे चालणे सुरक्षित आहे. प्रदूषण पातळी नियंत्रणात आहे.",
                "sensitive": "अतिदमा किंवा तीव्र ऍलर्जी असलेल्या व्यक्तींना दीर्घकाळ धावणे किंवा जड श्रमाच्या वेळी हलका त्रास होऊ शकतो.",
                "farmer": "शेतातील कामे नेहमीप्रमाणे सुरू ठेवा. सुका कचरा अथवा उसाचे पाचट न जाळता खतासाठी वापरण्याचा सल्ला.",
                "traffic_worker": "वाहतूक चौकात धूर असल्यास हलका कापडी रुमाल किंवा मास्क वापरणे श्रेयस्कर ठरू शकते.",
                "outdoor_worker": "कामादरम्यान नियमित विश्रांती घ्या आणि हायड्रेटेड राहा.",
                "schools": "मैदानी खेळ आणि शारीरिक शिक्षण वर्ग नेहमीप्रमाणे घेता येतील."
            },
            "mask_recommendation": "अतिसंवेदनशील व्यक्तींसाठी ऐच्छिक",
            "ventilation": "दिवसाच्या वेळेस नैसर्गिक वायुवीजन (खिडक्या उघडणे) सुरक्षित आहे."
        },
        "Moderate": {
            "headline": "हवेची गुणवत्ता साधारण प्रदूषित (मध्यम)",
            "summary": "हवेत धुलिकणांचे प्रमाण वाढले आहे. फुफ्फुस व हृदयाच्या रुग्णांना, लहान मुलांना श्वास घेण्यास त्रास होऊ शकतो.",
            "personas": {
                "general": "दीर्घकाळ चालणे किंवा बाह्य धावणे टाळा. विशेषतः गर्दीच्या रस्त्यांवर जास्त वेळ थांबणे टाळावे.",
                "sensitive": "दम्याचे रुग्ण आणि ज्येष्ठ नागरिकांनी सकाळच्या वेळेस जास्त फिरणे टाळावे. इनहेलर सोबत ठेवा.",
                "farmer": "काडीकचरा अथवा उसाचे पाचट अजिबात जाळू नका; यामुळे ग्रामीण भागात धुराचे थर साचतात. पिकांवर फवारणी करताना मास्क वापरा.",
                "traffic_worker": "वाहतूक चौकात काम करणाऱ्या पोलिसांनी N95 किंवा किमान ३-प्लाय मास्क वापरावा. डोळ्यांची जळजळ टाळण्यासाठी पाणी मारावे.",
                "outdoor_worker": "धूळयुक्त ठिकाणी काम करताना धूळ प्रतिबंधक मास्क वापरावा. कामाच्या जागी पाणी शिंपडणे आवश्यक.",
                "schools": "दुपारच्या सत्रात जास्त धावपळीचे बाह्य खेळ कमी करावेत. इनडोअर ॲक्टिव्हिटींना प्राधान्य द्या."
            },
            "mask_recommendation": "N95 / 3-Ply मास्क गर्दीच्या आणि वाहतुकीच्या ठिकाणी वापरा",
            "ventilation": "वाहतुकीच्या मुख्य वेळेत (सकाळी ८-१०, संध्याकाळी ६-९) रस्त्यालगतच्या खिडक्या बंद ठेवा."
        },
        "Poor": {
            "headline": "हवेची गुणवत्ता खालावलेली (खराब)",
            "summary": "हवेत घातक सूक्ष्म धुलिकण (PM2.5) साचले आहेत. प्रदीर्घ वेळ बाहेर राहिल्यास निरोगी लोकांनाही त्रास संभवतो.",
            "personas": {
                "general": "सकाळचे जॉगिंग किंवा मैदानी व्यायाम बंद ठेवा. कामाव्यतिरिक्त बाहेर पडणे टाळा.",
                "sensitive": "लहान मुले, गरोदर स्त्रिया आणि ६० वर्षांवरील ज्येष्ठांनी घरातच राहावे. छातीत घरघर किंवा खोकला जाणवल्यास डॉक्टरांचा सल्ला घ्या.",
                "farmer": "शेतात उसाचे पाचट, पराटी किंवा गव्हाचे अवशेष पेटवणे तात्काळ थांबवा. ट्रॅक्टरने मशागत करताना धूळ संरक्षक चष्मा व मास्क वापरा.",
                "traffic_worker": "वाहतूक पोलिसांनी सक्तीने N95 मास्क परिधान करावा. ड्युटी रोटेशन दर २ तासांनी सावलीच्या व स्वच्छ जागी करावे.",
                "outdoor_worker": "बांधकाम ठिकाणी पाण्याचा सतत फवारा मारा. कामगारांना सक्तीने N95 मास्क द्यावेत.",
                "schools": "सर्व बाह्य क्रीडा स्पर्धा आणि मैदानी कवायती रद्द कराव्यात. वर्गखोल्या बंदिस्त ठेवा."
            },
            "mask_recommendation": "N95 / FFP2 मास्क सक्तीचा",
            "ventilation": "खिडक्या आणि दारे बंद ठेवा; एअर प्युरिफायर किंवा इनडोअर झाडे (उदा. मनी प्लांट, स्नेक प्लांट) वापरा."
        },
        "Very Poor": {
            "headline": "हवेची गुणवत्ता अत्यंत घातक (अति खराब)",
            "summary": "हवेचा दर्जा अतिशय चिंताजनक. निरोगी व्यक्तींमध्ये श्वसनाचे आजार उद्भवू शकतात, तर आजारी व्यक्तींमध्ये स्थिती गंभीर होऊ शकते.",
            "personas": {
                "general": "अत्यावश्यक कामाशिवाय घराबाहेर पडू नका. घरात असतानाही खिडक्या पूर्णपणे बंद ठेवा.",
                "sensitive": "दमा, ब्रॉन्कायटिस आणि हृदयविकार असलेल्या व्यक्तींनी घरातच राहावे. ऑक्सिजन पातळी तपासा आणि औषधोपचार तयार ठेवा.",
                "farmer": "कोणत्याही प्रकारचा बायोमास किंवा कचरा जाळण्यास संपूर्ण बंदी. शेतात काम करताना पूर्ण चेहरा झाकणारा मास्क आवश्यक.",
                "traffic_worker": "चौकातील ड्युटी वेळ कमी करा. N95 मास्कशिवाय वाहतूक नियमन करू नका. डोळ्यांसाठी संरक्षणात्मक गॉगल वापरा.",
                "outdoor_worker": "जड शारीरिक कामे आणि धूळ निर्माण करणारी बांधकामे स्थगित करा. मजुरांना सुरक्षित निवारक कक्षात ठेवा.",
                "schools": "शाळांमधील बाह्य हालचाली पूर्ण बंद. प्राथमिक शाळांना ऑनलाइन वर्ग घेण्याचा विचार करावा."
            },
            "mask_recommendation": "प्रमाणित N95 मास्क घराबाहेर अनिवार्य",
            "ventilation": "खिडक्या पूर्ण बंद ठेवा. धूर किंवा धूळ घरात येऊ देऊ नका."
        },
        "Severe": {
            "headline": "आरोग्य आणीबाणी स्थिती (अति तीव्र / गंभीर)",
            "summary": "हवेची गुणवत्ता अत्यंत धोकादायक पातळीवर पोहोचली आहे. सर्व नागरिकांच्या आरोग्यावर तीव्र दुष्परिणाम होऊ शकतात.",
            "personas": {
                "general": "बाहेर पडणे पूर्णपणे टाळा. घरातही शुद्ध हवेसाठी प्युरिफायर वापरा. डोळे आणि घशाची जळजळ जाणवू शकते.",
                "sensitive": "ज्येष्ठ नागरिक आणि रुग्णांना तातडीने डॉक्टरांच्या देखरेखीखाली किंवा स्वच्छ हवेशीर सुरक्षित वातावरणात ठेवा.",
                "farmer": "जिल्हा प्रशासनाच्या आदेशानुसार बायोमास ज्वलनावर कडक दंडात्मक कारवाई होऊ शकते. स्वतःच्या आरोग्याचे रक्षण करा.",
                "traffic_worker": "वाहतूक चौकात ऑटोमेटेड सिग्नल किंवा केबिनमधून नियमन करा. फील्डवरील कर्मचाऱ्यांना तातडीने ऑक्सिजनयुक्त विश्रांती द्या.",
                "outdoor_worker": "सर्व प्रकारची खुली बांधकामे व उत्खनन तात्काळ बंद ठेवावीत.",
                "schools": "शाळा आणि महाविद्यालये तात्पुरती बंद ठेवण्याची किंवा ऑनलाइन वर्ग घेण्याची शिफारस."
            },
            "mask_recommendation": "N95/N99 मास्क अत्यंत आवश्यक (बाहेर पडल्यास)",
            "ventilation": "घरातील सर्व दारे-खिडक्या हवाबंद ठेवा. ओलसर पडदे लावा."
        }
    },
    "hi": {  # हिंदी (Hindi)
        "Good": {
            "headline": "वायु गुणवत्ता अच्छी (उत्कृष्ट)",
            "summary": "हवा साफ और स्वच्छ है। सभी बाहरी गतिविधियों और व्यायाम के लिए मौसम पूरी तरह अनुकूल है।",
            "personas": {
                "general": "सुबह की सैर, जॉगिंग और बाहरी कार्यों के लिए हवा एकदम शुद्ध है।",
                "sensitive": "बच्चों, बुजुर्गों और अस्थमा के मरीजों के लिए बाहर निकलना और खेलना पूरी तरह सुरक्षित है।",
                "farmer": "खेतों में सामान्य कार्य, कटाई और छिड़काव के लिए स्थिति अनुकूल है।",
                "traffic_worker": "ट्रैफिक ड्यूटी के दौरान किसी अतिरिक्त सुरक्षा की आवश्यकता नहीं है।",
                "outdoor_worker": "निर्माण और मजदूरी के लिए दिन बेहतरीन है। पर्याप्त पानी पिएं।",
                "schools": "स्कूलों में खेलकूद और आउटडोर गतिविधियां सामान्य रूप से संचालित की जा सकती हैं।"
            },
            "mask_recommendation": "मास्क की आवश्यकता नहीं",
            "ventilation": "खिड़कियां खोलकर ताजी हवा को अंदर आने दें।"
        },
        "Satisfactory": {
            "headline": "वायु गुणवत्ता संतोषजनक",
            "summary": "वायु गुणवत्ता संतोषजनक है, लेकिन संवेदनशील व्यक्तियों को हल्का ध्यान रखना चाहिए।",
            "personas": {
                "general": "दैनिक कार्य और सुबह की सैर सुरक्षित है।",
                "sensitive": "गंभीर श्वसन रोग वाले व्यक्ति भारी व्यायाम के दौरान थोड़ा ध्यान रखें।",
                "farmer": "कृषि अवशेष (पराली/कचरा) न जलाएं, खाद बनाने को प्राथमिकता दें।",
                "traffic_worker": "धूल भरे चौराहों पर सूती कपड़ा या हल्का मास्क उपयोगी हो सकता है।",
                "outdoor_worker": "नियमित रूप से पानी पिएं और कार्य जारी रखें।",
                "schools": "खेलकूद गतिविधियां सामान्य रूप से जारी रखी जा सकती हैं।"
            },
            "mask_recommendation": "संवेदनशील लोगों के लिए वैकल्पिक",
            "ventilation": "प्राकृतिक वेंटिलेशन सुरक्षित है।"
        },
        "Moderate": {
            "headline": "वायु गुणवत्ता मध्यम प्रदूषित",
            "summary": "हवा में धूलकणों की मात्रा बढ़ी है। सांस और दिल के मरीजों को बाहर असुविधा हो सकती है।",
            "personas": {
                "general": "व्यस्त सड़कों पर लंबे समय तक टहलना या दौड़ना टालें।",
                "sensitive": "अस्थमा मरीज और बुजुर्ग सुबह जल्दी टहलने से बचें। इनहेलर पास रखें।",
                "farmer": "फसल के अवशेष या गन्ने का कचरा बिल्कुल न जलाएं। कीटनाशक छिड़कते समय मास्क लगाएं।",
                "traffic_worker": "ट्रैफिक पुलिस N95 या 3-प्लाई मास्क का उपयोग अवश्य करें।",
                "outdoor_worker": "धूल वाली जगहों पर डस्ट मास्क पहनें और निर्माण स्थल पर पानी का छिड़काव करें।",
                "schools": "दोपहर में अत्यधिक भागदौड़ वाले खेलों को सीमित करें।"
            },
            "mask_recommendation": "N95 या सर्जिकल मास्क भीड़भाड़ वाले इलाकों में पहनें",
            "ventilation": "ट्रैफिक के समय (सुबह 8-10, शाम 6-9) मुख्य सड़क की खिड़कियां बंद रखें।"
        },
        "Poor": {
            "headline": "वायु गुणवत्ता खराब",
            "summary": "हवा में हानिकारक PM2.5 कण बढ़े हैं। लंबे समय तक बाहर रहने पर स्वस्थ लोगों को भी सांस में तकलीफ हो सकती है।",
            "personas": {
                "general": "सुबह की सैर और आउटडोर वर्कआउट बंद रखें। बिना जरूरी काम बाहर न जाएं।",
                "sensitive": "बुजुर्ग, गर्भवती महिलाएं और बच्चे घर के भीतर रहें। खांसी या सीने में जकड़न होने पर डॉक्टर से मिलें।",
                "farmer": "खेत में आग लगाने पर पूरी तरह रोक। जुताई के दौरान मास्क और चश्मा पहनें।",
                "traffic_worker": "N95 मास्क अनिवार्य है। हर 2 घंटे में छायादार व साफ जगह पर रोटेशन करें।",
                "outdoor_worker": "धूल नियंत्रण के लिए पानी छिड़कें। श्रमिकों को N95 मास्क वितरित किए जाएं।",
                "schools": "सभी बाहरी खेल और परेड रद्द करें। कक्षाएं बंद कमरों में चलाएं।"
            },
            "mask_recommendation": "N95 / FFP2 मास्क अनिवार्य",
            "ventilation": "खिड़कियां बंद रखें और इनडोर प्यूरीफायर का उपयोग करें।"
        },
        "Very Poor": {
            "headline": "वायु गुणवत्ता बहुत खराब (गंभीर)",
            "summary": "हवा का स्तर चिंताजनक है। स्वस्थ लोगों में श्वसन संबंधी बीमारियां और बीमार व्यक्तियों में गंभीर समस्या हो सकती है।",
            "personas": {
                "general": "आवश्यक काम के बिना घर से बाहर बिल्कुल न निकलें।",
                "sensitive": "अस्थमा और हृदय रोगी घर के अंदर ही रहें और अपनी दवाइयां तैयार रखें।",
                "farmer": "कचरा या बायोमास जलाने पर सख्त प्रतिबंध। कृषि कार्यों में चेहरे को पूरी तरह ढकें।",
                "traffic_worker": "चौराहों पर ड्यूटी का समय कम करें। बिना N95 मास्क के कार्य न करें।",
                "outdoor_worker": "धूल पैदा करने वाले भारी निर्माण कार्य तत्काल रोके जाएं।",
                "schools": "आउटडोर खेल पूरी तरह बंद। प्राथमिक विद्यालयों में ऑनलाइन कक्षाओं पर विचार किया जाए।"
            },
            "mask_recommendation": "N95 मास्क बाहर निकलते ही जरूरी",
            "ventilation": "सभी दरवाजे और खिड़कियां पूरी तरह बंद रखें।"
        },
        "Severe": {
            "headline": "स्वास्थ्य आपातकाल (अति गंभीर स्थिति)",
            "summary": "हवा जहरीली हो चुकी है। सभी नागरिकों के स्वास्थ्य पर गंभीर असर पड़ सकता है।",
            "personas": {
                "general": "घर के अंदर रहें। आंखों और गले में जलन हो सकती है, अधिक पानी पिएं।",
                "sensitive": "मरीजों को स्वच्छ और सुरक्षित वातावरण में रखें। आवश्यकता पड़ने पर तत्काल अस्पताल जाएं।",
                "farmer": "खेतों में आग लगाने पर कानूनी कार्रवाई हो सकती है। स्वास्थ्य की सुरक्षा पहली प्राथमिकता है।",
                "traffic_worker": "सिग्नल केबिन से ट्रैफिक नियंत्रण करें। फील्ड स्टाफ को ऑक्सीजन युक्त विश्राम दें।",
                "outdoor_worker": "सभी बाहरी कार्य और खुदाई कार्य तत्काल बंद किए जाएं।",
                "schools": "स्कूलों और कॉलेजों को तत्काल बंद या ऑनलाइन करने की सिफारिश।"
            },
            "mask_recommendation": "N95/N99 मास्क अत्यंत अनिवार्य",
            "ventilation": "घर के सारे खिड़की-दरवाजे बंद रखें, गीले पर्दे लगाएं।"
        }
    },
    "en": {  # English
        "Good": {
            "headline": "Air Quality is Good (Clean)",
            "summary": "Air quality is satisfactory and poses little or no health risk. Ideal for all outdoor activities.",
            "personas": {
                "general": "Enjoy outdoor activities, morning walks, and open ventilation. Air quality is pristine.",
                "sensitive": "Completely safe for children, seniors, and asthma patients to exercise outdoors.",
                "farmer": "Optimal conditions for harvesting, threshing, and pesticide spraying. Airborne dust disperses rapidly.",
                "traffic_worker": "No respiratory protection required for standard outdoor transit shifts.",
                "outdoor_worker": "Favorable conditions for heavy outdoor labor. Maintain normal hydration.",
                "schools": "Ideal for sports day, outdoor physical training, and open-air assemblies."
            },
            "mask_recommendation": "No mask required",
            "ventilation": "Keep windows wide open for natural fresh air circulation."
        },
        "Satisfactory": {
            "headline": "Air Quality is Satisfactory",
            "summary": "Air quality is acceptable. A very small number of unusually sensitive individuals may experience slight irritation.",
            "personas": {
                "general": "Daily activities and morning walks are safe. Pollution levels remain within manageable limits.",
                "sensitive": "Individuals with severe asthma should monitor for minor coughing or throat dryness during intense exertion.",
                "farmer": "Routine farm operations safe. Avoid open burning of crop residue or sugarcane bagasse; prefer composting.",
                "traffic_worker": "Consider a light cotton mask or neck gaiter in congested transit intersections.",
                "outdoor_worker": "Safe for regular construction and loading tasks. Drink adequate water.",
                "schools": "Outdoor recess and physical education classes can proceed normally."
            },
            "mask_recommendation": "Optional for hyper-sensitive groups",
            "ventilation": "Safe for natural ventilation throughout the day."
        },
        "Moderate": {
            "headline": "Air Quality is Moderately Polluted",
            "summary": "Elevated particulate concentration. May cause breathing discomfort to people with lung disease, asthma, and heart conditions.",
            "personas": {
                "general": "Reduce prolonged heavy exertion along high-traffic corridors and industrial zones.",
                "sensitive": "Asthma patients and senior citizens should shift morning walks to mid-afternoon and keep quick-relief inhalers nearby.",
                "farmer": "Strictly refrain from burning sugarcane trash or stubble, which causes dense local smoke pockets in calm morning air. Wear a dust mask when operating tractors or sprayers.",
                "traffic_worker": "Traffic personnel at major junctions must wear N95 or multi-ply particulate respirators. Rinse eyes frequently.",
                "outdoor_worker": "Enforce water-sprinkling at dusty excavation points. Provide dust-filtering masks to daily-wage workers.",
                "schools": "Curtail intense midday endurance sports; prioritize covered or indoor recreational activities."
            },
            "mask_recommendation": "N95 / 3-Ply mask recommended in traffic and dusty corridors",
            "ventilation": "Keep roadside windows closed during peak commute hours (08:00-10:00, 18:00-21:00)."
        },
        "Poor": {
            "headline": "Air Quality is Poor (Unhealthy)",
            "summary": "High PM2.5 concentration. Prolonged exposure can trigger breathing discomfort in healthy people and severe distress in vulnerable groups.",
            "personas": {
                "general": "Avoid morning jogs and strenuous outdoor workouts. Commute with car windows raised on recirculate.",
                "sensitive": "Children, pregnant women, and elderly individuals should remain indoors. Consult a physician if persistent coughing or wheezing occurs.",
                "farmer": "Total prohibition on agricultural waste incineration. Inversion layers trap smoke near crop height. Use protective goggles and masks during field preparation.",
                "traffic_worker": "N95 masks mandatory for all traffic police on active junction beats. Institute a mandatory 2-hour rotation schedule to cleaner indoor air shelters.",
                "outdoor_worker": "Mandate continuous water-mist cannons at construction sites. Supply certified N95 respirators to all outdoor laborers.",
                "schools": "Cancel outdoor sports meets, morning assemblies, and strenuous athletics. Keep classrooms sealed."
            },
            "mask_recommendation": "N95 / FFP2 respirator mandatory outdoors",
            "ventilation": "Seal windows and doors; deploy HEPA air purifiers or maintain indoor green barriers."
        },
        "Very Poor": {
            "headline": "Air Quality is Very Poor (High Alert)",
            "summary": "Respiratory illness risk is elevated for the general population. Prolonged outdoor exposure can cause long-term cardiovascular and lung distress.",
            "personas": {
                "general": "Eliminate non-essential outdoor travel. Stay inside sealed environments as much as possible.",
                "sensitive": "Cardiovascular and COPD patients must stay strictly indoors in filtered air. Keep medical contacts and oxygen concentrators accessible.",
                "farmer": "Enforce zero open burning across the taluka. Field labor should be restricted to brief, essential maintenance with full particulate respirators.",
                "traffic_worker": "Limit active junction duty to 45-minute cycles. Wear fit-tested N95/N99 masks. Provide eye-drops for smoke irritation.",
                "outdoor_worker": "Halt non-essential earthwork, stone crushing, and dust-generating construction. Provide sheltered resting stations.",
                "schools": "Transition primary schools to online classes where feasible; strictly halt all outdoor school activities."
            },
            "mask_recommendation": "N95/N99 respirator strictly required whenever stepping outside",
            "ventilation": "Do not ventilate with outdoor air. Run purifiers on high."
        },
        "Severe": {
            "headline": "Air Quality Emergency (Hazardous)",
            "summary": "Air quality is critically hazardous. Poses serious health impacts even during brief outdoor exposure across the entire population.",
            "personas": {
                "general": "Remain strictly indoors. Keep indoor air filtered. Drink warm water and avoid heavy physical activity.",
                "sensitive": "High-risk medical emergency conditions. Vulnerable individuals should be monitored continuously for respiratory distress.",
                "farmer": "Severe regulatory penalties apply for any open burning. Keep livestock in sheltered, well-ventilated sheds away from ambient smoke.",
                "traffic_worker": "Reassign personnel to automated signal cabins. Field officers must use N99 respirators and take mandatory oxygen breaks.",
                "outdoor_worker": "Total halt on outdoor manual labor and construction activities as per emergency pollution control mandates.",
                "schools": "Immediate closure of schools and educational institutions or transition to emergency remote learning."
            },
            "mask_recommendation": "N99 / P100 respirator essential if outdoors",
            "ventilation": "Keep premises completely sealed. Use damp towels on door gaps if smoke infiltrates."
        }
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# Maharashtra Regional Environmental Contexts
# ─────────────────────────────────────────────────────────────────────────────

REGIONAL_CONTEXT_ALERTS: Dict[str, Dict[str, Dict[str, str]]] = {
    "Konkan": {
        "mr": "कोकण किनारपट्टी: समुद्रावरून येणाऱ्या दमट वाऱ्यांमुळे रात्रीच्या वेळी आर्द्रता वाढून प्रदूषक जमिनीलगत अडकण्याची शक्यता असते.",
        "hi": "कोंकण तटीय क्षेत्र: समुद्री हवा और उच्च आर्द्रता के कारण रात में प्रदूषक जमीन के नजदीक रुक सकते हैं।",
        "en": "Konkan Coastal Belt: High relative humidity and shallow marine boundary layers at night can trap local vehicular emissions near ground level."
    },
    "Western Maharashtra": {
        "mr": "पश्चिम महाराष्ट्र: हिवाळ्यात दरीतील हवा थंड झाल्याने (Valley Inversion) आणि ऊस तोडणी हंगामातील पाचट जाळण्यामुळे सकाळी धुक्यासारखे धुरके साचू शकते.",
        "hi": "पश्चिमी महाराष्ट्र: सर्दियों में घाटी के तापमान में उलटफेर (Valley Inversion) और गन्ने के अवशेष जलने से सुबह धुंध जम सकती है।",
        "en": "Western Maharashtra: Valley temperature inversions and seasonal sugarcane crushing/bagasse burning can create dense early morning ground-level smog."
    },
    "North Maharashtra": {
        "mr": "उत्तर महाराष्ट्र (खान्देश): कोरडे हवामान आणि कांदा-द्राक्ष पट्ट्यातील धूळ यामुळे PM10 चे प्रमाण वाढण्याची शक्यता असते.",
        "hi": "उत्तर महाराष्ट्र (खानदेश): शुष्क जलवायु और कृषि धूल के कारण PM10 का स्तर बढ़ सकता है।",
        "en": "North Maharashtra (Khandesh): Arid conditions and agro-transit dust frequently elevate coarse PM10 concentrations."
    },
    "Marathwada": {
        "mr": "मराठवाडा: कोरडे उन्हाळे आणि भूगर्भातील कोरडी धूळ यामुळे उन्हाळ्यात आणि हिवाळ्याच्या सुरुवातीला हवेत धुळीचे प्रमाण जास्त असते.",
        "hi": "मराठवाड़ा: शुष्क मौसम और मिट्टी की धूल के कारण वायु में कणों की मात्रा बढ़ जाती है।",
        "en": "Marathwada: Semi-arid climate and open soil wind-suspension elevate particulate dust load during transition seasons."
    },
    "Vidarbha": {
        "mr": "विदर्भ: चंद्रपूर-नागपूर पट्ट्यातील कोळसा खाणी आणि औष्णिक वीज प्रकल्पांमुळे हवेत SO2, NO2 आणि राख (Fly Ash) चे प्रमाण जास्त असू शकते. श्वसनाची विशेष काळजी घ्या.",
        "hi": "विदर्भ: चंद्रपुर-नागपुर क्षेत्र में कोयला खदानों और ताप विद्युत संयंत्रों के कारण SO2, NO2 और उड़ने वाली राख का प्रभाव रहता है।",
        "en": "Vidarbha: Thermal power generation clusters (Chandrapur, Koradi) and coal mining elevate industrial SO2 and fine fly ash. Monitor sulfurous odors."
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API Function
# ─────────────────────────────────────────────────────────────────────────────

def generate_local_advisory(
    aqi_value: float,
    lat: float,
    lon: float,
    dominant_pollutant: str = "PM2.5",
    lang: str = "en"
) -> Dict[str, Any]:
    """
    Generates a localized, persona-segmented advisory for a specific coordinate in Maharashtra.

    Args:
        aqi_value: Numeric AQI (0-500 scale)
        lat: Latitude of query point
        lon: Longitude of query point
        dominant_pollutant: Dominant pollutant key (e.g., 'PM2.5', 'PM10', 'NO2')
        lang: 'mr' (Marathi), 'hi' (Hindi), or 'en' (English). Defaults to 'en'.

    Returns:
        Structured dictionary with localized advisory, persona recommendations,
        mask guidelines, ventilation advice, and regional atmospheric context.
    """
    if lang not in ["mr", "hi", "en"]:
        lang = "en"

    # Determine category
    cat_name, cat_color, _ = aqi_to_category(aqi_value)
    if cat_name not in ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]:
        cat_name = "Moderate"

    # Get templates for language and category
    lang_templates = ADVISORY_TEMPLATES.get(lang, ADVISORY_TEMPLATES["en"])
    cat_template = lang_templates.get(cat_name, lang_templates["Moderate"])

    # Resolve nearest district to pull local regional context
    nearest_district = find_nearest_district(lat, lon)
    region = nearest_district.get("region", "Western Maharashtra")
    regional_alert = REGIONAL_CONTEXT_ALERTS.get(region, {}).get(lang, "")

    # Localized category names
    cat_names_localized = {
        "mr": {
            "Good": "उत्कृष्ट (Good)",
            "Satisfactory": "समाधानकारक (Satisfactory)",
            "Moderate": "मध्यम (Moderate)",
            "Poor": "खराब (Poor)",
            "Very Poor": "अति खराब (Very Poor)",
            "Severe": "अति तीव्र / गंभीर (Severe)"
        },
        "hi": {
            "Good": "अच्छा (Good)",
            "Satisfactory": "संतोषजनक (Satisfactory)",
            "Moderate": "मध्यम (Moderate)",
            "Poor": "खराब (Poor)",
            "Very Poor": "बहुत खराब (Very Poor)",
            "Severe": "गंभीर (Severe)"
        },
        "en": {
            "Good": "Good",
            "Satisfactory": "Satisfactory",
            "Moderate": "Moderate",
            "Poor": "Poor",
            "Very Poor": "Very Poor",
            "Severe": "Severe"
        }
    }

    # Color code
    color_map = {
        "Good": "#00b050",
        "Satisfactory": "#92d050",
        "Moderate": "#ffbf00",
        "Poor": "#ff7c00",
        "Very Poor": "#c00000",
        "Severe": "#7030a0"
    }

    return {
        "language": lang,
        "aqi": round(float(aqi_value), 1),
        "category": cat_name,
        "category_localized": cat_names_localized[lang].get(cat_name, cat_name),
        "color": color_map.get(cat_name, "#ffbf00"),
        "dominant_pollutant": dominant_pollutant,
        "district": {
            "name": nearest_district["name"],
            "name_mr": nearest_district.get("name_mr", nearest_district["name"]),
            "name_hi": nearest_district.get("name_hi", nearest_district["name"]),
            "division": nearest_district.get("division", ""),
            "region": region,
            "distance_km": nearest_district.get("distance_to_center_km", 0.0),
            "emission_profile": nearest_district.get("emission_profile", "")
        },
        "headline": cat_template["headline"],
        "summary": cat_template["summary"],
        "mask_recommendation": cat_template["mask_recommendation"],
        "ventilation": cat_template["ventilation"],
        "regional_environmental_note": regional_alert,
        "personas": {
            "general": {
                "title": {"mr": "सामान्य नागरिक", "hi": "आम नागरिक", "en": "General Public"}[lang],
                "advice": cat_template["personas"]["general"]
            },
            "sensitive": {
                "title": {"mr": "लहान मुले व ज्येष्ठ नागरिक (अतिसंवेदनशील)", "hi": "बच्चे व बुजुर्ग (संवेदनशील समूह)", "en": "Children & Seniors (Sensitive)"}[lang],
                "advice": cat_template["personas"]["sensitive"]
            },
            "farmer": {
                "title": {"mr": "शेतकरी व शेतमजूर (कृषी सल्ला)", "hi": "किसान एवं कृषि श्रमिक", "en": "Farmers & Agricultural Workers"}[lang],
                "advice": cat_template["personas"]["farmer"]
            },
            "traffic_worker": {
                "title": {"mr": "वाहतूक पोलीस व चालक", "hi": "ट्रैफिक पुलिस व चालक", "en": "Traffic Police & Transport Workers"}[lang],
                "advice": cat_template["personas"]["traffic_worker"]
            },
            "outdoor_worker": {
                "title": {"mr": "बांधकाम व दैनंदिन मजूर", "hi": "निर्माण एवं दैनिक श्रमिक", "en": "Construction & Daily Laborers"}[lang],
                "advice": cat_template["personas"]["outdoor_worker"]
            },
            "schools": {
                "title": {"mr": "शाळा, महाविद्यालये आणि क्रीडा", "hi": "स्कूल, कॉलेज एवं खेलकूद", "en": "Schools & Sports"}[lang],
                "advice": cat_template["personas"]["schools"]
            }
        }
    }
