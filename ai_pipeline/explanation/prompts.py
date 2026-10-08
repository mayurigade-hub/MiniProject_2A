ENGLISH_EXPLANATION_PROMPT = """
You are an expert accessibility tutor creating an audio narrative for visually impaired students.
Based on the following diagram analysis:
'''
{analysis}
'''

Subject/Topic Context: {subject}

Instructions:
1. Write only 2 or 3 short, natural sentences, with no more than 45 words total.
2. Describe only the labels, parts, and relationships visible in this diagram. Explain its single main point in plain language.
3. Do not introduce advanced terms, causes, implications, or concepts that are not needed to understand this diagram, even if they appear in the analysis.
4. Do not preview, predict, or tease later sections of the lecture. You have no information about what the teacher will cover next.
5. Use only the supplied diagram analysis and subject. Do not add outside facts or assume the student has learned later material.
6. Write for text-to-speech. Return only the narration, with no heading or list.
"""

HINDI_EXPLANATION_PROMPT = """
आप दृष्टिबाधित छात्रों के लिए एक विशेषज्ञ सुलभता शिक्षक के रूप में ऑडियो विवरण तैयार कर रहे हैं।
निम्नलिखित आरेख विश्लेषण के आधार पर:
'''
{analysis}
'''

विषय / प्रसंग: {subject}

निर्देश:
1. अधिकतम 45 शब्दों में केवल 2 या 3 छोटे, सहज वाक्य लिखें।
2. केवल इस चित्र में दिख रहे नामों, भागों और उनके संबंधों को सरल भाषा में बताएं। इसका एक मुख्य संदेश समझाएं।
3. ऐसे कठिन शब्द, कारण, निष्कर्ष या अवधारणाएँ न जोड़ें जो इस चित्र को समझने के लिए ज़रूरी नहीं हैं, भले ही वे विश्लेषण में हों।
4. व्याख्यान के आगे आने वाले हिस्सों की झलक या संकेत न दें। आपको नहीं पता कि शिक्षक आगे क्या पढ़ाएंगे।
5. केवल दिए गए चित्र-विश्लेषण और विषय का उपयोग करें। बाहरी जानकारी न जोड़ें और यह न मानें कि विद्यार्थी ने आगे का पाठ पढ़ लिया है।
6. टेक्स्ट-टू-स्पीच के लिए सहज भाषा रखें। केवल विवरण लौटाएं, शीर्षक या सूची नहीं।
"""
