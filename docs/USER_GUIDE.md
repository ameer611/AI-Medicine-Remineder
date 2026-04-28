# User Guide

How to use the Dori Scheduler medication reminder bot. This guide is for end users.

**Table of Contents**
- [Getting Started](#getting-started)
- [Scanning a Prescription](#scanning-a-prescription)
- [Adding Medications Manually](#adding-medications-manually)
- [Viewing Your Schedules](#viewing-your-schedules)
- [How Reminders Work](#how-reminders-work)
- [Tips & Best Practices](#tips--best-practices)
- [FAQs](#faqs)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### **Step 1: Find the Bot**

Search for the Dori Scheduler bot on Telegram by its username (e.g., `@DoriSchedulerBot`).

### **Step 2: Start the Bot**

Tap the `/start` command or the **START** button in Telegram.

You should see:

```
👋 Welcome to the Smart Prescription Reminder Bot!

How would you like to add your medication?
```

With three options:
- 📸 **Scan Prescription** — Upload a photo of your prescription
- ⌨️ **Add Manually** — Type in medication details yourself
- 📋 **View My Schedules** — See all your active medications

### **Step 3: Add Your First Medication**

Choose either "Scan" or "Manual" (see sections below).

---

## Scanning a Prescription

The easiest way to add medications! The bot will automatically read the prescription and extract medication details.

### **Full Walkthrough**

**Step 1: Start Scan**
```
Tap: 📸 Scan Prescription
```

The bot will ask:
```
📸 Please send me a photo of your prescription.
```

**Step 2: Take Photo**
```
• Tap the camera icon 📷 in Telegram
• Take a clear, well-lit photo of your prescription
• Make sure the text is readable
• Tap "Send" ✔️
```

**Step 3: Review Extracted Text**

The bot will show you the text it read:

```
📄 Extracted from image:

Aspirin 500mg: take one tablet twice daily after meals.
Vitamin D: take one capsule daily.
Prescribed: Dr. Smith, 2024-04-15
```

The bot asks:
```
Does this look correct?
[Yes] [No]
```

**Step 4: AI Parsing (if "Yes")**

The bot sends the text to an AI to extract medication details:

```
Processing... 🤖

Found 2 medications:
1. Aspirin 500mg
2. Vitamin D
```

**Step 5: Confirm Each Medication**

The bot shows the first medication:

```
💊 Aspirin 500mg

Doses per day: 2
Timing: custom
Notes: after meals

[✅ Confirm] [✏️ Edit]
```

**Options:**
- **✅ Confirm** — Move to time selection
- **✏️ Edit** — Change name, dosage, notes, etc.

**Step 6: Select Daily Times** (if "Confirm")

Click the times you take the medication:

```
⏰ When do you take this medication? (Select 2 times)

08:00  08:30  09:00  09:30  10:00
10:30  11:00  11:30  12:00  12:30
13:00  13:30  14:00  14:30  15:00
15:30  16:00  16:30  17:00  17:30
18:00  18:30  19:00  19:30  20:00
20:30  21:00  21:30  22:00

[✅ Confirm Times] [← Back]
```

Select times (e.g., 08:00 and 20:00 for twice daily).

**Step 7: Choose Reminder Timing** (when to get alerts)

The bot asks when to alert you:

```
⏰ When should we remind you?

[ 1 min ]  [ 5 min ]  [ 15 min ]  [ 30 min ]

[← Back]
```

**Recommended:** 5 minutes early (so you have time to get the medication ready).

**Step 8: Choose Duration** (how long to remind you)

The bot asks how many days to send reminders:

```
📅 How long should we remind you for?

[ 1 day ]  [ 7 days ]  [ 14 days ]  [ 30 days ]

[← Back]
```

**Step 9: Done! ✅**

The bot confirms:

```
✅ Aspirin 500mg saved!
Reminders: Daily at 08:00 and 20:00
Duration: 7 days

Next medication? [Continue] [Back to Menu]
```

You'll start receiving reminders tomorrow!

---

## Adding Medications Manually

Don't have a prescription? Add medications manually.

### **Full Walkthrough**

**Step 1: Start Manual Entry**
```
Tap: ⌨️ Add Manually
```

The bot shows an empty template:

```
💊 New Medication

Dosage: 1 dose per day
[✅ Confirm] [✏️ Edit]
```

**Step 2: Edit the Template**

Tap **✏️ Edit**. The bot asks which field to change:

```
What would you like to edit?

[Name] [Dosage] [Timing] [Notes] [Duration]

[← Back]
```

### **Editing Each Field**

**Name Field**
```
What's the medication name?

> Aspirin 500mg
```
Type the name and press Send.

**Dosage Field**
```
How many times per day?

[1] [2] [3] [4]
```
Choose the number of doses per day (must be 1-4).

**Timing Field**
```
Typical timing?

[Morning] [Afternoon] [Evening] [Custom]
```
Choose when you usually take it (just for reference).

**Notes Field**
```
Any special instructions?

> Take with water after breakfast
```
Type any notes (optional). Leave blank if none.

**Duration Field**
```
How many days should we remind you?

[1 day] [7 days] [14 days] [30 days]
```
Choose how long to receive reminders.

**Step 3: Return to Confirmation**

After each edit, you'll return to the medication summary. Edit again if needed, or tap ✅ Confirm.

**Step 4: Select Times** (same as Prescription Scan)

Choose all the times you take the medication each day.

**Step 5: Choose Reminder & Duration** (same as Prescription Scan)

Choose when to be reminded and for how many days.

**Step 6: Done!** ✅

The medication is saved and reminders start tomorrow.

---

## Viewing Your Schedules

See all your active medications and their daily reminder times.

**Command:**
```
/my_medications
```

Or tap:
```
📋 View My Schedules
```

**Display:**

```
📋 Your Active Medications:

1️⃣ Aspirin 500mg
   Doses: 2 times daily
   Times: 08:00, 20:00
   Reminder: 5 minutes before

2️⃣ Vitamin D
   Doses: 1 time daily
   Times: 09:00
   Reminder: 15 minutes before

3️⃣ Blood Pressure Medication
   Doses: 1 time daily
   Times: 21:00
   Reminder: 30 minutes before
```

You can use this to verify your medications are set up correctly.

---

## How Reminders Work

### **Example:**

You set Aspirin to remind at **08:00** with a **5-minute early reminder**.

**You'll receive:**

| Time | Message |
|------|---------|
| 07:55 | "Reminder: In 5 minutes, take Aspirin 500mg." |
| 08:00 | "Time to take: Aspirin 500mg" |

### **Multiple Medications At Same Time**

If you take two medications at the same time (e.g., 09:00):

```
09:00 Medication 1 reminder
09:05 Medication 2 reminder
```

Each medication gets its own reminder.

### **Duration Expiry**

If you set a 7-day duration, reminders will stop automatically after 7 days. If you need to continue, add the medication again.

---

## Tips & Best Practices

### **1. Clear Photos for Ocr**

When scanning a prescription:
- ✅ Well-lit, flat surface
- ✅ Text fully visible and readable
- ✅ Minimal shadows or glare
- ❌ Avoid blurry photos
- ❌ Don't hold at an angle

### **2. Review AI Parsing**

The AI isn't perfect. Always review:
- ✅ Medication name spelled correctly?
- ✅ Dosage matches prescription?
- ✅ Notes/instructions included?

Use the **Edit** button to fix any errors.

### **3. Choose Realistic Times**

Pick times you're actually awake and can take medication:
- ✅ 08:00, 14:00, 20:00 (spread throughout day)
- ✅ 09:00 (morning routine)
- ❌ 02:00 (middle of night)

### **4. Start Early Reminders for Forgetful Users**

If you forget easily, choose a 15 or 30-minute early reminder to give yourself time to prepare.

### **5. Set Appropriate Duration**

- Long-term daily meds (e.g., blood pressure): **30 days**
- Antibiotics (e.g., 7-day course): **7 days**
- Supplements (seasonal): **14 days**

---

## FAQs

**Q: Can I edit a medication after saving?**

A: Not directly yet. Delete the old one (start a new entry) and create a new one with corrections. Or message the bot admin.

**Q: What if the AI misreads my prescription?**

A: You can **Edit** each field before confirming. Fix any errors and tap ✅ Confirm.

**Q: Will I lose reminders if I close Telegram?**

A: No! Reminders will still arrive as Telegram notifications. Just re-open Telegram when you get a notification.

**Q: Can I have reminders at custom times (not 30-min intervals)?**

A: Currently, the time grid starts at 08:00 and shows 30-minute intervals. Choose the closest time and adjust your medication schedule.

**Q: How do I delete a medication?**

A: Feature coming soon! For now, message the bot admin.

**Q: What if I miss a reminder?**

A: Reminders repeat at the exact time and offset time. If you miss both, they resume the next day at the scheduled time.

**Q: Can I pause reminders temporarily?**

A: Once a medication expires (after the duration), reminders stop automatically. To add it back, scan/add it again.

**Q: Do reminders work at night?**

A: Yes, unless you've turned off notifications in Telegram settings. Check:
- **Telegram > Settings > Notifications > Message notifications**
- Ensure **DoriSchedulerBot** is not muted

---

## Troubleshooting

### **Bot doesn't respond to `/start`**

**Solution:**
1. Tap the **START** button in Telegram
2. Or type `/start` and press Send
3. Wait 2-3 seconds for response

If still frozen:
- Restart Telegram app
- Try `/start` again

### **Photo upload fails**

**Solutions:**
1. **Check file size:** Photos should be < 20 MB
2. **Check format:** Use PNG, JPG, or JPEG
3. **Retry with different angle:** Avoid glare/shadows
4. **Check internet:** Ensure strong Wi-Fi or 4G

### **AI parsing returned wrong medications**

**Solution:**
1. Tap **✏️ Edit** on the medication
2. Select the field to correct
3. Re-enter correct information
4. Tap ✅ Confirm

### **Reminders not arriving**

**Check:**
1. **Telegram notifications enabled?**
   - Settings > Notifications > Message notifications > ON

2. **Bot muted?**
   - Tap bot in Telegram
   - Info > Mute? (if any mute icon, unmute)

3. **Phone time correct?**
   - Check device date/time is accurate

4. **Medication duration expired?**
   - View schedule with `/my_medications`
   - If not listed, add medication again

### **"User not found" error**

**Solution:**
1. Tap `/start` to initialize your account
2. Try adding medication again

### **Can't select desired time**

**Note:** Times shown are 30-minute intervals from 08:00 to 22:00. If you need a different time:
- Choose closest time
- Update with admin/developer later

---

## Contact & Support

- **Report a bug:** Message the bot with `/support`
- **Report issue:** Contact bot admin
- **Feature request:** Comment `@admin feature: [your idea]`

---

## See Also

- [BOT_COMMANDS.md](BOT_COMMANDS.md) — Technical command reference
- [ARCHITECTURE.md](ARCHITECTURE.md) — How the system works
- [API_REFERENCE.md](API_REFERENCE.md) — For developers integrating the API

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Status:** Complete
