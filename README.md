# 🐍 pytaskii – The Smarter, Offline, Sofa-Loving Task Manager

Welcome to **pytaskii**, the Python-powered desktop twin of my web task manager. If the web version is the fancy extrovert living on Firebase, this one is the introvert who stays home, sips coffee, and refuses to open a browser tab.

> "I built this project just for fun – now *you* get to enjoy it, along with all my typos and logic bugs. You're welcome. 😇"

---

## 🚀 What It Does

- Add, edit, and delete tasks with ease
- Schedule tasks with future date and time
- Repeat tasks (daily, weekly, monthly, yearly)
- System notifications that *pretend* to be professional
- Automatically move notified tasks to the “completed” zone
- All data is stored in a beautiful, humble little `task.json` file
- Auto-summarization of task descriptions using **Gemini 1.5 Flash API**
- Your brain’s smarter roommate. Just quieter.

---

## 🧠 Why I Made a Python Version

Honestly? I built the web version first, hosted it, used Firebase and all that jazz.

👉 **Web version:** [taskii-web](https://mytaskwebapp.web.app)  
👉 **Repo:** [pytasky](https://github.com/copy-n-paste/webtasky)

But then I remembered I *actually* like Python and *dislike* HTML divs arguing about margins.

So here it is:  
**`pytaskii`**, for people who prefer buttons that don’t float, scroll, animate, or sass you in CSS.

---

## 🧩 Tech Stack

- `Python` + `tkinter` – UI that actually makes sense
- `plyer` – cross-platform system notifications
- `requests` – for communicating with Gemini
- `tkcalendar` – to pick dates like a civilized person
- `dotenv` – to keep API keys where no one can find them (including me)
- `task.json` – the quiet MVP of the project

---

## ⚙️ Setup (because obviously you want to try it)

```bash
git clone https://github.com/copy-n-paste/pytaskii.git
cd pytaskii
pip install -r requirements.txt
````

Make a `.env` file and put your [Gemini API Key](https://aistudio.google.com/app/apikey) like this:

```env
GEMINI_API_KEY=your_api_key_here
```

Then run it:

```bash
python main.py
```

---

## 💥 Pro Features (a.k.a. Bugs That Behaved Themselves)

* Edit/delete only works for pending tasks (because that makes sense)
* You can delete completed tasks (after basking in the glory of completion)
* The notification looks *so* real, your OS might promote it to admin
* Action section shows you the remaining time like: `2 days 3 hours left`

---

## 😎 License

> This project is licensed under the "Do Whatever You Want but Don't Blame Me If It Explodes" License.

---

## ✌️ Built With Joy, Typos, and Zero UI Libraries

You could’ve used Notion. You could’ve set reminders on your phone.
But no.
You chose `pytaskii`.
You’re one of us now.
