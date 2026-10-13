VIRAL ZONE VIDEO — Admin Bot (fixed configuration)

1. admin_bot.py, .env এবং serviceAccountKey.json একই ফোল্ডারে রাখুন।
2. .env.example কপি করে .env নাম দিন।
3. BotFather-এ প্রকাশিত পুরোনো Bot Token revoke করুন, নতুন Token তৈরি করে .env-এর BOT_TOKEN-এ বসান।
4. ADMIN_ID-তে আপনার Telegram numeric ID দিন।
5. Firebase Console থেকে সঠিক প্রজেক্টের Service Account JSON ডাউনলোড করে serviceAccountKey.json নাম দিন।
6. requirements ইনস্টল করুন:
   pip install -r requirements.txt
7. চালান:
   python admin_bot.py

নিরাপত্তা:
- serviceAccountKey.json বা .env কাউকে পাঠাবেন না এবং public repository-তে আপলোড করবেন না।
- Realtime Database Rules নিরাপদ রাখুন; service account key কেবল সার্ভারে রাখুন।
- এই bot-এর সঙ্গে user_panel.html-এর Firebase schema মিলিয়ে পরীক্ষা করতে হবে।
- এই প্যাকেজে আসল bot token অন্তর্ভুক্ত করা হয়নি।
